"""
SeaPayServer implements the ChatKitServer interface for the SeaPay hotel booking assistant.
"""

from __future__ import annotations

from typing import Any, AsyncIterator

from agents import Agent, Runner
from chatkit.agents import stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import (
    Action,
    Attachment,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
)
from openai.types.responses import ResponseInputContentParam

from .agents.seapay_agent import SeaPayContext, seapay_agent
from .memory_store import MemoryStore
from .request_context import RequestContext
from .thread_item_converter import SeaPayThreadItemConverter


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
        return

    async def action(
        self,
        thread: ThreadMetadata,
        action: Action[str, Any],
        sender: WidgetItem | None,
        context: RequestContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        # Handle custom actions if needed in the future
        return

    async def to_message_content(self, _input: Attachment) -> ResponseInputContentParam:
        raise RuntimeError("File attachments are not supported in this demo.")

    # -- Helpers ----------------------------------------------------
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
