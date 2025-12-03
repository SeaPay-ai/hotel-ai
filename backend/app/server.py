"""
SeaPayServer implements the ChatKitServer interface for the SeaPay hotel booking assistant.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from agents import Agent, Runner
from chatkit.agents import stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import (
    Action,
    ThreadItem,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
)
from pydantic import TypeAdapter

from .agents.seapay_agent import SeaPayContext, seapay_agent
from .memory_store import MemoryStore
from .request_context import RequestContext
from .thread_item_converter import SeaPayThreadItemConverter

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SeaPayServer(ChatKitServer[RequestContext]):
    """ChatKit server wired up with the SeaPay hotel booking assistant."""

    def __init__(self) -> None:
        self.store: MemoryStore = MemoryStore()
        super().__init__(self.store)
        self.thread_item_converter = SeaPayThreadItemConverter()

    # -- Required overrides ----------------------------------------------------
    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        items_page = await self.store.load_thread_items(
            thread.id,
            after=None,
            limit=20,
            order="desc",
            context=context,
        )
        items = list(reversed(items_page.data))
        input_items = await self.thread_item_converter.to_agent_input(items)

        agent, agent_context = self._select_agent(thread, item, context)

        result = Runner.run_streamed(agent, input_items, context=agent_context)

        async for event in stream_agent_response(agent_context, result):
            yield event

    async def action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Handle custom widget actions.

        For hotel selection actions, create a user message and process it through the agent.
        """
        action_type = action.type
        payload = action.payload or {}

        # Handle hotel selection actions
        if action_type in ("select_hotel", "hotels.select_hotel"):
            hotel_id = payload.get("id")
            hotel_name = payload.get("hotelName")
            options = payload.get("options", [])

            # Find hotel name from options if not directly provided
            if not hotel_name and hotel_id and isinstance(options, list):
                for hotel in options:
                    if isinstance(hotel, dict) and hotel.get("id") == hotel_id:
                        hotel_name = hotel.get("hotelName")
                        break

            if hotel_name:
                user_message = f"I want to reserve {hotel_name}"
                # Explicitly log the user's selection to the chat before processing
                user_item_dict: UserMessageItem = {
                    "type": "user_message",
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_message}],
                    "thread_id": thread.id,
                    "created_at": datetime.now(timezone.utc),
                    "inference_options": {},
                }
                thread_item_adapter = TypeAdapter(ThreadItem)
                user_item = thread_item_adapter.validate_python(user_item_dict)
                
                # Save the message to the store
                await self.store.add_thread_item(thread.id, user_item, context)
                
                # Yield the user message event so it appears in the chat
                # Use TypeAdapter to properly construct the Pydantic model
                event_adapter = TypeAdapter(ThreadStreamEvent)
                event = event_adapter.validate_python({
                    "type": "thread.item.added",
                    "item": user_item,
                })
                yield event
                
                # Now process the message through the agent
                async for event in self.respond(thread, user_item, context):
                    yield event
                return

        # Handle "show more hotels" action
        elif action_type == "hotels.more_hotels":
            user_message = "Show me more hotels"
            async for event in self._process_user_message(thread, user_message, context):
                yield event
            return
        
        # Handle approval/rejection actions from the approval widget
        elif action_type == "request.approve":
            # User approved the action - continue the agent flow
            user_message = "I approve. Please proceed."
            async for event in self._process_user_message(thread, user_message, context):
                yield event
            return
        
        elif action_type == "request.reject":
            # User rejected the action - inform the agent to end gracefully
            user_message = "I reject. Please cancel that action."
            async for event in self._process_user_message(thread, user_message, context):
                yield event
            return

    async def to_message_content(self, _input: Any) -> Any:
        """File attachments are not supported."""
        raise RuntimeError("File attachments are not supported in this demo.")

    # -- Helpers ----------------------------------------------------
    async def _process_user_message(
        self,
        thread: ThreadMetadata,
        message_text: str,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """
        Create a user message from text and process it through the agent.

        Args:
            thread: The thread metadata
            message_text: The user message text
            context: The request context

        Yields:
            ThreadStreamEvent: Events from processing the message
        """
        user_item_dict: UserMessageItem = {
            "type": "user_message",
            "id": str(uuid.uuid4()),
            "role": "user",
            "content": [{"type": "input_text", "text": message_text}],
            "thread_id": thread.id,
            "created_at": datetime.now(timezone.utc),
            "inference_options": {},
        }
        # Convert dict to ThreadItem using TypeAdapter (since ThreadItem is a Union)
        thread_item_adapter = TypeAdapter(ThreadItem)
        user_item = thread_item_adapter.validate_python(user_item_dict)

        # Save the message to the store
        await self.store.add_thread_item(thread.id, user_item, context)

        # Yield the user message event so it appears in the chat
        event_adapter = TypeAdapter(ThreadStreamEvent)
        user_event = event_adapter.validate_python({
            "type": "thread.item.added",
            "item": user_item,
        })
        yield user_event

        # Process the message through the agent
        async for event in self.respond(thread, user_item, context):
            yield event

    def _select_agent(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: RequestContext,
    ) -> tuple[Agent, SeaPayContext]:
        """
        Select the appropriate agent for this thread.

        All conversations are routed to the SeaPay hotel booking agent.
        """
        seapay_context = SeaPayContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )
        return seapay_agent, seapay_context


def create_chatkit_server() -> SeaPayServer | None:
    """Return a configured ChatKit server instance if dependencies are available."""
    return SeaPayServer()
