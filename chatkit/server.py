from __future__ import annotations

from agents import HostedMCPTool, Agent, ModelSettings, RunContextWrapper, TResponseInputItem, Runner, RunConfig, trace
from pydantic import BaseModel, ValidationError
from openai.types.shared.reasoning import Reasoning

import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncIterator

from agents.model_settings import ModelSettings
from chatkit.agents import AgentContext, stream_agent_response
from chatkit.server import ChatKitServer, StreamingResult
from chatkit.store import NotFoundError, Store
from chatkit.types import (
    Action,
    AssistantMessageContent,
    AssistantMessageItem,
    Attachment,
    HiddenContextItem,
    ThreadItemDoneEvent,
    ThreadItemUpdated,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
    WidgetItem,
    WidgetRootUpdated,
)
from fastapi import Depends, FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from openai.types.responses import (
    EasyInputMessageParam,
    ResponseInputContentParam,
    ResponseInputTextParam,
)
from starlette.responses import JSONResponse
from memory_store import MemoryStore


DEFAULT_THREAD_ID = "demo_default_thread"
logger = logging.getLogger(__name__)
class MyChatKitServer(ChatKitServer):
    def __init__(self, data_store: Store, file_store: FileStore | None = None):
        super().__init__(data_store, file_store)

    assistant_agent = Agent[AgentContext](
        model="gpt-4.1",
        name="Assistant",
        instructions="You are a helpful assistant",
    )

    async def respond(
        self,
        thread: ThreadMetadata,
        input: UserMessageItem | ClientToolCallOutputItem,
        context: Any,
    ) -> AsyncIterator[Event]:
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )
        result = Runner.run_streamed(
            self.assistant_agent,
            await to_input_item(input, self.to_message_content),
            context=agent_context,
        )
        async for event in stream_agent_response(agent_context, result):
            yield event

    async def to_message_content(
        self, input: FilePart | ImagePart
    ) -> ResponseInputContentParam:
        raise NotImplementedError()
    

app = FastAPI()
store = MemoryStore()
server = MyChatKitServer(store)

@app.post("/chatkit")
async def chatkit_endpoint(request: Request):
    result = await server.process(await request.body(), {})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    return Response(content=result.json, media_type="application/json")

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}