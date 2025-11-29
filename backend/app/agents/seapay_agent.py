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

from typing import Annotated

from agents import Agent, HostedMCPTool, ModelSettings
from chatkit.agents import AgentContext
from pydantic import BaseModel, ConfigDict, Field

from ..memory_store import MemoryStore
from ..request_context import RequestContext


class SeaPayContext(AgentContext):
    """Agent context for the SeaPay hotel booking agent."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    store: Annotated[MemoryStore, Field(exclude=True)]
    request_context: Annotated[RequestContext, Field(exclude=True, default_factory=RequestContext)]


class HotelOption(BaseModel):
    """Represents a single hotel option returned from MCP."""

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
    hotels: list[HotelOption] = Field(default_factory=list)
    selected_hotel: str | None = None
    payment_required: bool = False
    reservation_created: bool = False


# Hosted MCP tool configuration pointing at the SeaPay Node server.
seapay_mcp_tool = HostedMCPTool(
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


SEAPAY_INSTRUCTIONS = """
You are SeaPay, a hotel booking assistant for a crypto-enabled hotel search
platform.

Your end-to-end workflow:

1. Greet the user briefly.
2. Collect booking information:
   - destination (city, optionally country)
   - check-in date (YYYY-MM-DD)
   - check-out date (YYYY-MM-DD)
   - number of guests
   Only ask for the missing fields; don't repeat already-known info.
3. When you have all required booking info, call the MCP tool
   `check_availability` to fetch real hotel options. Never invent hotels,
   locations, prices, or dates.
4. Present 3–6 hotel options:
   - Name, location
   - Dates and room type
   - Price (in USDC or dollars)
   - Any image/description if available
   Use a concise, skimmable list.
5. Ask the user which hotel they want to reserve. Accept either the hotel
   name or a clear index (e.g. “#2”).
6. Once the user clearly chooses a hotel, confirm the choice and then call the
   MCP tool `reserve` with the chosen hotel and booking details.
7. If the reserve call succeeds:
   - Show the reservation id, hotel name, dates, guests, and total price.
8. If the reserve call is blocked by payment (for example, the backend
   returns an HTTP 402 Payment Required or a similar payment-required error):
   - Explain that payment is required to complete the booking through SeaPay.
   - Summarize the amount and network if that information is available in the
     tool response.
   - Ask the user to confirm whether they want to proceed with payment.
   - After confirmation, explain that they should follow the payment
     instructions shown in the UI / wallet and that they can retry the
     reservation once payment is complete.

General rules:
- ALWAYS use MCP tools (`check_availability`, `reserve`) for any hotel
  availability, pricing, or reservation details.
- NEVER make up hotel names, locations, dates, prices, or availability.
- Keep responses short, friendly, and focused on the next action the user
  should take.
- If the user asks non-booking questions, answer briefly but guide them back
  to searching and booking hotels.
"""


seapay_agent = Agent[SeaPayContext](
    model="gpt-4.1-mini",
    name="SeaPay Hotel Booking Agent",
    instructions=SEAPAY_INSTRUCTIONS,
    tools=[seapay_mcp_tool],
    model_settings=ModelSettings(
        store=True,
    ),
)


