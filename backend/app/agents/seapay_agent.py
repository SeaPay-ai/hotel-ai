"""
SeaPay hotel booking agent.

This agent provides a hotel booking workflow that talks to the SeaPay MCP server. It:

- Asks the user for destination, dates, and number of guests.
- Calls the MCP `check_availability` tool to fetch hotel options.
- Presents multiple hotels and asks which one to reserve.
- Calls the MCP `reserve` tool to create a reservation.
- Surfaces payment requirements (e.g., HTTP 402 from the backend) back to the user.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from agents import Agent, HostedMCPTool, ModelSettings, RunContextWrapper, function_tool, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from chatkit.agents import AgentContext
from pydantic import BaseModel, ConfigDict, Field
from eth_account import Account
from x402.clients.httpx import x402HttpxClient
import os

from ..memory_store import MemoryStore
from ..request_context import RequestContext
from ..widgets.hotel_card_widget import build_hotel_card_widget
from ..widgets.quick_approve_reject_widget import build_approval_widget

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SeaPayContext(AgentContext):
    """Agent context for the SeaPay hotel booking agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    store: Annotated[MemoryStore, Field(exclude=True)]
    request_context: Annotated[RequestContext, Field(exclude=True, default_factory=RequestContext)]


class HotelData(BaseModel):
    """Hotel data model for widget display (strict schema compatible)."""

    model_config = ConfigDict(extra="forbid")

    hotelName: str
    location: str
    dates: str
    roomType: str
    price: float | str
    imageUrl: str | None = None





class CheckAvailabilitySchema(BaseModel):
    """Schema for check availability agent output."""

    hotels: list[HotelData] = Field(default_factory=list)


# Shared MCP tool configuration for all agents
# All agents use this single MCP connection to the SeaPay server
mcp = HostedMCPTool(
    tool_config={
        "type": "mcp",
        "server_label": "hotel_server",
        # Default to the current public tunnel for the SeaPay MCP server.
        "server_url": "https://e95e8d1772b6.ngrok-free.app/mcp",
        "allowed_tools": [
            "check_availability",
            "reserve",
        ],
        # We handle approval manually via the show_approval_request widget,
        # so we don't need the MCP framework's built-in approval system.
        "require_approval": "never",
    }
)

@function_tool(
    description_override=(
        "Make a payment for a hotel reservation using x402. "
        "This tool automatically handles HTTP 402 Payment Required responses "
        "by completing payments using the configured wallet. "
        "Takes hotel name, check-in date (YYYY-MM-DD), check-out date (YYYY-MM-DD), and number of guests."
    )
)
async def make_payment(
    ctx: RunContextWrapper[SeaPayContext],
    hotelName: str,
    checkIn: str,
    checkOut: str,
    guests: int,
) -> dict[str, Any]:
    """
    Make a payment for a hotel reservation with automatic x402 payment handling.
    
    This tool makes a reservation request to the SeaPay API and automatically
    handles payment if required (HTTP 402). Payments are completed using the
    configured Ethereum wallet from the PRIVATE_KEY environment variable.
    
    Args:
        hotelName: Name of the hotel to reserve
        checkIn: Check-in date in YYYY-MM-DD format
        checkOut: Check-out date in YYYY-MM-DD format
        guests: Number of guests
        
    Returns:
        dict: Reservation confirmation with reservationId, hotelName, dates, guests, totalPrice, and status
    """
    logger.info(
        "[TOOL CALL] make_payment: %s, %s to %s, %d guests",
        hotelName,
        checkIn,
        checkOut,
        guests,
    )
    
    try:
        # Ensure private key has 0x prefix
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise ValueError("PRIVATE_KEY environment variable is not set")
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        
        wallet_account = Account.from_key(private_key)
        logger.info("[PAYMENT] Using wallet address: %s", wallet_account.address)
        
        # Base URL for the SeaPay API server
        base_url = os.getenv(
            "SEAPAY_API_BASE_URL",
            "https://e95e8d1772b6.ngrok-free.app"
        )
        
        # Make request with x402 client (automatically handles payments)
        async with x402HttpxClient(
            account=wallet_account, base_url=base_url
        ) as client:
            response = await client.post(
                "/api/reserve",
                json={
                    "hotelName": hotelName,
                    "checkIn": checkIn,
                    "checkOut": checkOut,
                    "guests": guests,
                },
            )
            
            # Parse response JSON (httpx response.json() is synchronous)
            try:
                response_data = response.json()
            except Exception:
                response_data = {"error": "Invalid response format"}
            
            if response.status_code == 200:
                logger.info(
                    "[SUCCESS] Reservation created: %s",
                    response_data.get("reservationId", "unknown"),
                )
                return {
                    "success": True,
                    "reservationId": response_data.get("reservationId"),
                    "hotelName": response_data.get("hotelName", hotelName),
                    "checkIn": response_data.get("checkIn", checkIn),
                    "checkOut": response_data.get("checkOut", checkOut),
                    "guests": response_data.get("guests", guests),
                    "totalPrice": response_data.get("totalPrice"),
                    "status": response_data.get("status", "confirmed"),
                    "message": "Reservation confirmed successfully. Payment was automatically processed via x402.",
                }
            else:
                logger.error(
                    "[ERROR] Reservation failed: status %d, %s",
                    response.status_code,
                    response_data,
                )
                return {
                    "success": False,
                    "status": response.status_code,
                    "error": response_data.get("error", "Unknown error"),
                    "message": f"Reservation failed: {response_data.get('error', 'Unknown error')}",
                }
                
    except ValueError as e:
        # Wallet configuration error
        logger.error("[ERROR] Wallet configuration: %s", e)
        return {
            "success": False,
            "error": str(e),
            "message": "Payment processing is not configured. Please set PRIVATE_KEY environment variable in .env file.",
        }
    except Exception as e:
        logger.error("[ERROR] Payment error: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to complete payment: {str(e)}",
        }


@function_tool(
    description_override=(
        "Display hotel search results as visual cards. "
        "Call this after receiving hotel options from check_availability. "
        "Takes a list of hotel objects with hotelName, location, dates, roomType, price, and optional imageUrl."
    )
)
async def show_hotel_cards(
    ctx: RunContextWrapper[SeaPayContext],
    hotels: list[HotelData],
) -> dict[str, Any]:
    """
    Display hotel search results as visual card widgets.
    
    Args:
        hotels: List of hotel data objects with hotelName, location, dates, roomType, price, and optional imageUrl
    """
    logger.info("[TOOL CALL] show_hotel_cards: %s hotels", len(hotels))
    
    if not hotels:
        return {"message": "No hotels to display", "count": 0}
    
    try:
        # Convert Pydantic models to dicts for widget builder
        hotel_dicts = [hotel.model_dump() for hotel in hotels]
        
        # Build a single ListView widget with all hotels
        widget = build_hotel_card_widget(hotel_dicts, selected=None)
        
        # Stream the widget to the chat
        hotel_names = ", ".join([hotel.hotelName for hotel in hotels[:3]])
        if len(hotels) > 3:
            hotel_names += f" and {len(hotels) - 3} more"
        await ctx.context.stream_widget(widget, copy_text=f"Found {len(hotels)} hotel(s): {hotel_names}")
        
        return {
            "message": f"Displayed {len(hotels)} hotel(s) in a list",
            "count": len(hotels),
        }
    except Exception as e:
        logger.error("[ERROR] Failed to build hotel list widget: %s", e)
        return {
            "message": f"Error displaying hotels: {str(e)}",
            "count": 0,
        }


@function_tool(
    description_override=(
        "Show an approval request widget before making tool calls that require user approval. "
        "This widget displays a card with approve/reject buttons. "
        "Takes a title and description explaining what action requires approval."
    )
)
async def show_approval_request(
    ctx: RunContextWrapper[SeaPayContext],
    title: str,
    description: str,
) -> dict[str, Any]:
    """
    Display an approval request widget with approve/reject actions.
    
    This widget should be shown before making tool calls that require user approval,
    such as MCP tool calls for checking availability or making reservations.
    
    Args:
        title: The title text for the approval request (e.g., "Approve hotel search?")
        description: Description explaining what action requires approval
    """
    logger.info("[TOOL CALL] show_approval_request: %s - %s", title, description)
    
    try:
        # Build the approval widget
        widget = build_approval_widget(title=title, description=description)
        
        # Stream the widget to the chat
        await ctx.context.stream_widget(widget, copy_text=f"{title}: {description}")
        
        return {
            "message": "Approval request displayed",
            "title": title,
            "description": description,
        }
    except Exception as e:
        logger.error("[ERROR] Failed to build approval widget: %s", e)
        return {
            "message": f"Error displaying approval request: {str(e)}",
        }


# ============================================================================
# Specialized Agents for Workflow Steps
# ============================================================================




# 3. Check Availability Agent - Calls MCP check_availability and shows hotel cards
CHECK_AVAILABILITY_INSTRUCTIONS = """
You are a hotel availability checker for SeaPay.

Your workflow (diagram steps 1-2):
1. BEFORE calling the MCP tool, call `show_approval_request` with:
   - title: "Proceed with hotel search?"
   - description: A clear description of what you're about to search (e.g., "I'm about to search for available hotels in [destination] for [checkIn] to [checkOut] with [guests] guests")
2. After showing the approval widget, wait for the user's response
3. If the user approves (says "I approve", "yes", "proceed", etc.), immediately call the MCP tool `check_availability` with the booking details (checkIn, checkOut, guests)
4. If the user rejects (says "I reject", "no", "cancel", etc.), acknowledge their decision politely and end the conversation (e.g., "I understand. If you change your mind, feel free to ask me to search again.")
5. Parse the MCP response to get the list of available hotels
6. IMMEDIATELY call the `show_hotel_cards` tool with the hotel list to display them visually
7. After showing the cards, provide a brief text summary of the options. Prices should always be shown in USDC.
8. Ask the user which hotel they want to reserve (accept hotel name or index like "#2")

Rules:
- ALWAYS call `show_approval_request` before calling MCP `check_availability`
- If user rejects, acknowledge and end the conversation gracefully
- ALWAYS call `show_hotel_cards` immediately after receiving hotel results from MCP
- NEVER invent hotels, prices, or availability - only use data from MCP tool
- Present hotels clearly and ask for user's choice
"""

check_availability_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="Check Hotel Availability",
    instructions=CHECK_AVAILABILITY_INSTRUCTIONS,
    tools=[mcp, show_hotel_cards, show_approval_request],  # Uses MCP, show_hotel_cards, and show_approval_request
    output_type=CheckAvailabilitySchema,
    model_settings=ModelSettings(store=True),
)


# 4. Reserve Agent - Calls MCP reserve tool (diagram steps 3-4)
RESERVE_INSTRUCTIONS = """
You are a hotel reservation agent for SeaPay.

Your workflow (diagram steps 3-4):
1. Confirm the user's hotel choice and booking details
2. BEFORE calling the MCP tool, call `show_approval_request` with:
   - title: "Proceed with reservation?"
   - description: A clear description of what you're about to reserve (e.g., "I'm about to reserve [hotelName] for [checkIn] to [checkOut] with [guests] guests")
3. After showing the approval widget, wait for the user's response
4. If the user approves (says "I approve", "yes", "proceed", etc.), immediately call the MCP tool `reserve` with:
   - hotelName: The exact hotel name the user chose
   - checkIn: Check-in date (YYYY-MM-DD)
   - checkOut: Check-out date (YYYY-MM-DD)
   - guests: Number of guests (as integer)
5. If the user rejects (says "I reject", "no", "cancel", etc.), acknowledge their decision politely and end the conversation (e.g., "I understand. If you change your mind, feel free to ask me to help with a reservation.")
6. The MCP `reserve` tool returns a JSON response with these fields:
   - `success`: boolean
   - `status`: HTTP status code (200 for success, 402 for payment required)
   - `body`: the actual API response data
7. Handle the response:
   - If status 200: Parse `body` and show reservation confirmation (reservationId, hotel, dates, guests, totalPrice)
   - If status 402: Parse `body` to extract payment details (amount, currency, network, instructions) and inform the user that payment is required
8. The amount should be divided by 1000000000 (10 to the 9th power) to get the amount in USDC, the currency should always be USDC, the network should always be base-sepolia

Rules:
- ALWAYS call `show_approval_request` before calling MCP `reserve`
- If user rejects, acknowledge and end the conversation gracefully
- ALWAYS use the MCP `reserve` tool (never make direct API calls)
- Parse the response structure correctly (success, status, body)
- For 402 responses, clearly explain payment requirements
"""

reserve_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="Reserve Hotel",
    instructions=RESERVE_INSTRUCTIONS,
    tools=[mcp, show_approval_request],  # Uses MCP reserve tool and show_approval_request
    model_settings=ModelSettings(store=True),
)


# 5. Reserve + Payment Agent - Handles payment and retry (diagram steps 5-9)
RESERVE_PAYMENT_INSTRUCTIONS = """
You are a payment handler for SeaPay hotel reservations.

Your workflow (diagram steps 5-9):
1. You receive payment details from a previous 402 response (amount, currency, network, instructions), the amount should devided by 1000000000 to get the amount in USDC, the currency always be USDC, the network always be base-sepolia
2. BEFORE calling the `make_payment` tool, call `show_approval_request` with:
   - title: "Proceed with payment?"
   - description: A clear description of the payment (e.g., "I'm about to process payment of [amount] USDC for [hotelName] reservation from [checkIn] to [checkOut]")
3. After showing the approval widget, wait for the user's response
4. If the user approves (says "I approve", "yes", "proceed", etc.):
   a. Immediately call the `make_payment` tool with the booking details:
      - hotelName: The exact hotel name
      - checkIn: Check-in date (YYYY-MM-DD)
      - checkOut: Check-out date (YYYY-MM-DD)
      - guests: Number of guests (as integer)
   b. The `make_payment` tool automatically handles payment via x402
   c. After the tool completes, show the result:
      - If successful: Display the reservation confirmation with reservationId, hotel, dates, guests, totalPrice
      - If error: Explain what went wrong and next steps
   d. ALWAYS thank the user after showing the result (e.g., "Thank you for using SeaPay! Your reservation has been confirmed." or "Thank you for your patience. Unfortunately, the payment could not be processed.")
5. If the user rejects (says "I reject", "no", "cancel", etc.), acknowledge their decision politely and end the conversation (e.g., "I understand. If you change your mind, feel free to proceed with the payment later.")

Rules:
- ALWAYS call `show_approval_request` before calling `make_payment`
- After user approval, IMMEDIATELY call `make_payment` tool
- After `make_payment` completes, ALWAYS show the result (success or error details)
- ALWAYS thank the user after showing the payment result
- If user rejects, acknowledge and end the conversation gracefully
- ALWAYS use the `make_payment` tool (it handles x402 payments automatically)
- Use the same booking details as the original reservation attempt
- The tool handles payment automatically, so you don't need to process payments manually
- Clearly communicate success or failure to the user
"""

reserve_payment_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="Reserve with Payment",
    instructions=RESERVE_PAYMENT_INSTRUCTIONS,
    tools=[make_payment, show_approval_request],  # Uses make_payment tool and show_approval_request
    model_settings=ModelSettings(store=True),
)


# ============================================================================
# Main SeaPay Agent - Orchestrates the workflow
# ============================================================================



SEAPAY_SUPERVISOR_INSTRUCTIONS = """
You are SeaPay, a hotel booking assistant for a crypto-enabled hotel search and booking platform.

Your primary role is to orchestrate the complete booking workflow.

Your workflow proceeds as follows:
1.  **Gather Information:** Polite ask the user for their destination, check-in and check-out dates, number of guests, and any other preferences.
    - Memorize this information using your memory store as you gather it.
    - Ensure you have all necessary details (destination, dates, guests) before proceeding.
2.  **Check Availability:** Once all necessary information is gathered, `delegate_to_check_availability`.
3.  **Reserve Hotel:** After the user selects a hotel, `delegate_to_reserve_hotel`.
4.  **Handle Payment:** If a reservation requires payment, `delegate_to_reserve_payment`.

Always assume the user wants to proceed through the booking flow.

Use the `show_approval_request` tool (if available) before any irreversible actions or tool calls made by delegated agents that require user confirmation.
"""


# Main SeaPay agent - uses delegation tools to orchestrate the workflow
seapay_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="SeaPay Hotel Booking Agent",
    instructions=f"{RECOMMENDED_PROMPT_PREFIX}\n\n{SEAPAY_SUPERVISOR_INSTRUCTIONS}",
    tools=[
        show_approval_request,
    ],
    handoffs=[
        check_availability_agent,
        reserve_agent,
        reserve_payment_agent,
    ],
    model_settings=ModelSettings(
        store=True,
    ),
)


