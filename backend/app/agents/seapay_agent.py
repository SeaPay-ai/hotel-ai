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

from agents import Agent, HostedMCPTool, ModelSettings, RunContextWrapper, function_tool
from chatkit.agents import AgentContext
from pydantic import BaseModel, ConfigDict, Field
from eth_account import Account
from x402.clients.httpx import x402HttpxClient
import os

from ..memory_store import MemoryStore
from ..request_context import RequestContext
from ..widgets.hotel_card_widget import build_hotel_card_widget

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


class SeaPayBookingState(BaseModel):
    """Lightweight booking state the model can reason about."""

    destination: str | None = None
    checkin_date: str | None = None  # YYYY-MM-DD
    checkout_date: str | None = None  # YYYY-MM-DD
    guests: int | None = None
    hotels: list[HotelData] = Field(default_factory=list)
    selected_hotel: str | None = None
    payment_required: bool = False
    reservation_created: bool = False
    confirm: bool = False


class ExtractorSchema(BaseModel):
    """Schema for extracting booking information from user messages."""

    destination: str
    checkin_date: str  # YYYY-MM-DD
    checkout_date: str  # YYYY-MM-DD
    traveler_num: str  # Number of guests as string
    all_filled: bool  # True if all required fields are present
    hotel_decision: str | None = None  # Hotel name if user has chosen one


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
        # In the chatbox flow we want the agent to be able to call tools freely.
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


# ============================================================================
# Specialized Agents for Workflow Steps
# ============================================================================

# 1. Extractor Agent - Extracts booking information from user messages
EXTRACTOR_INSTRUCTIONS = """
You are an information extractor for hotel bookings.

Your job is to extract booking information from user messages and output it in a structured format.

Extract the following fields:
- destination: City or location (e.g., "Paris", "New York")
- checkin_date: Check-in date in YYYY-MM-DD format
- checkout_date: Check-out date in YYYY-MM-DD format  
- traveler_num: Number of guests as a string (e.g., "2")
- all_filled: Set to true if ALL of the above fields are present and valid
- hotel_decision: Hotel name if the user has explicitly chosen a hotel, otherwise null

Rules:
- If a field is missing, use an empty string "" (not null)
- Dates must be in YYYY-MM-DD format
- Only set all_filled=true if destination, checkin_date, checkout_date, and traveler_num are all present
- Only set hotel_decision if the user explicitly mentions a hotel name they want to book
"""

extractor_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="Booking Information Extractor",
    instructions=EXTRACTOR_INSTRUCTIONS,
    tools=[],  # No tools needed for extraction
    output_type=ExtractorSchema,
    model_settings=ModelSettings(store=True),
)


# 2. Ask for Missing Info Agent - Asks user for missing booking fields
ASK_MISSING_INFO_INSTRUCTIONS = """
You are a helpful assistant that asks users for missing booking information.

Your job is to look at the extracted booking information and ask the user ONLY for the fields that are missing.

If the user has provided:
- destination but missing dates → ask for check-in and check-out dates
- dates but missing destination → ask for destination
- missing guests → ask for number of guests

Rules:
- Only ask for missing fields, don't repeat what the user already provided
- Be friendly and concise
- Ask one question at a time if possible
- Accept dates in various formats but guide users to YYYY-MM-DD
"""

ask_missing_info_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="Ask for Missing Information",
    instructions=ASK_MISSING_INFO_INSTRUCTIONS,
    tools=[],  # No tools needed
    model_settings=ModelSettings(store=True),
)


# 3. Check Availability Agent - Calls MCP check_availability and shows hotel cards
CHECK_AVAILABILITY_INSTRUCTIONS = """
You are a hotel availability checker for SeaPay.

Your workflow (diagram steps 1-2):
1. Call the MCP tool `check_availability` with the booking details (checkIn, checkOut, guests)
2. Parse the MCP response to get the list of available hotels
3. IMMEDIATELY call the `show_hotel_cards` tool with the hotel list to display them visually
4. After showing the cards, provide a brief text summary of the options
5. Ask the user which hotel they want to reserve (accept hotel name or index like "#2")

Rules:
- ALWAYS call `show_hotel_cards` immediately after receiving hotel results from MCP
- NEVER invent hotels, prices, or availability - only use data from MCP tool
- Present hotels clearly and ask for user's choice
"""

check_availability_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="Check Hotel Availability",
    instructions=CHECK_AVAILABILITY_INSTRUCTIONS,
    tools=[mcp, show_hotel_cards],  # Uses MCP and show_hotel_cards
    output_type=CheckAvailabilitySchema,
    model_settings=ModelSettings(store=True),
)


# 4. Reserve Agent - Calls MCP reserve tool (diagram steps 3-4)
RESERVE_INSTRUCTIONS = """
You are a hotel reservation agent for SeaPay.

Your workflow (diagram steps 3-4):
1. Confirm the user's hotel choice and booking details
2. Call the MCP tool `reserve` with:
   - hotelName: The exact hotel name the user chose
   - checkIn: Check-in date (YYYY-MM-DD)
   - checkOut: Check-out date (YYYY-MM-DD)
   - guests: Number of guests (as integer)
3. The MCP `reserve` tool returns a JSON response with:
   - `success`: boolean
   - `status`: HTTP status code (200 for success, 402 for payment required)
   - `body`: the actual API response data
4. Handle the response:
   - If status 200: Parse `body` and show reservation confirmation (reservationId, hotel, dates, guests, totalPrice)
   - If status 402: Parse `body` to extract payment details (amount, currency, network, instructions) and inform the user that payment is required

Rules:
- ALWAYS use the MCP `reserve` tool (never make direct API calls)
- Parse the response structure correctly (success, status, body)
- For 402 responses, clearly explain payment requirements
"""

reserve_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="Reserve Hotel",
    instructions=RESERVE_INSTRUCTIONS,
    tools=[mcp],  # Uses MCP reserve tool
    model_settings=ModelSettings(store=True),
)


# 5. Reserve + Payment Agent - Handles payment and retry (diagram steps 5-9)
RESERVE_PAYMENT_INSTRUCTIONS = """
You are a payment handler for SeaPay hotel reservations.

Your workflow (diagram steps 5-9):
1. You receive payment details from a previous 402 response (amount, currency, network, instructions)
2. The user has confirmed they want to proceed with payment
3. Call the `make_payment` tool with the booking details:
   - hotelName: The exact hotel name
   - checkIn: Check-in date (YYYY-MM-DD)
   - checkOut: Check-out date (YYYY-MM-DD)
   - guests: Number of guests (as integer)
4. The `make_payment` tool automatically handles payment via x402
5. If successful: Show final reservation confirmation with reservationId, hotel, dates, guests, totalPrice
6. If error: Explain what went wrong and next steps

Rules:
- ALWAYS use the `make_payment` tool (it handles x402 payments automatically)
- Use the same booking details as the original reservation attempt
- The tool handles payment automatically, so you don't need to process payments manually
- Clearly communicate success or failure to the user
"""

reserve_payment_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="Reserve with Payment",
    instructions=RESERVE_PAYMENT_INSTRUCTIONS,
    tools=[make_payment],  # Uses make_payment tool for automatic x402 payment handling
    model_settings=ModelSettings(store=True),
)


# ============================================================================
# Main SeaPay Agent - Orchestrates the workflow
# ============================================================================

SEAPAY_INSTRUCTIONS = """
You are SeaPay, a hotel booking assistant for a crypto-enabled hotel search platform.

You orchestrate the complete booking workflow:

1. Extract booking information from user messages
2. Ask for any missing information
3. Check hotel availability and show options
4. Reserve the chosen hotel
5. Handle payment if required

Your workflow matches the SeaPay booking diagram:
- Extract → Ask for missing info → Check availability → Reserve → Reserve+Payment

Use the appropriate specialized agents for each step, or handle the workflow directly using MCP tools.

Payment confirmation flow:
- When a reservation requires payment (HTTP 402 response), inform the user about the payment requirement
- Wait for the user to confirm they want to proceed with payment
- If the user confirms (says "yes", "confirm", "proceed", etc.), call the `make_payment` tool with the booking details:
  - hotelName: The exact hotel name
  - checkIn: Check-in date (YYYY-MM-DD)
  - checkOut: Check-out date (YYYY-MM-DD)
  - guests: Number of guests (as integer)
- The `make_payment` tool automatically handles payment via x402
- After successful payment, show the reservation confirmation

General rules:
- ALWAYS use MCP tool `check_availability` for hotel availability
- ALWAYS use MCP tool `reserve` for making reservations (never direct API calls)
- ALWAYS call `show_hotel_cards` immediately after receiving hotel results
- When payment is required and user confirms, ALWAYS use the `make_payment` tool
- NEVER make up hotels, locations, dates, prices, or availability
- Keep responses short, friendly, and focused on the next action
"""


# Main SeaPay agent - uses MCP tools directly for the workflow
seapay_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="SeaPay Hotel Booking Agent",
    instructions=SEAPAY_INSTRUCTIONS,
    tools=[mcp, show_hotel_cards, make_payment],  # Uses shared MCP tool, show_hotel_cards, and make_payment
    model_settings=ModelSettings(
        store=True,
    ),
)


