"""FastAPI entrypoint wiring the ChatKit server and REST endpoints."""

from __future__ import annotations

from pathlib import Path

from chatkit.server import StreamingResult
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse
from starlette.responses import JSONResponse

# Load environment variables from .env file
# Look for .env in the backend directory (parent of app/)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from .request_context import RequestContext
from .server import SeaPayServer, create_chatkit_server

app = FastAPI(title="SeaPay ChatKit API")

_chatkit_server: SeaPayServer | None = create_chatkit_server()


def get_chatkit_server() -> SeaPayServer:
    if _chatkit_server is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ChatKit dependencies are missing. Install the ChatKit Python "
                "package to enable the conversational endpoint."
            ),
        )
    return _chatkit_server


@app.post("/chatkit")
async def chatkit_endpoint(
    request: Request, server: SeaPayServer = Depends(get_chatkit_server)
) -> Response:
    payload = await request.body()
    context = RequestContext(request=request)
    result = await server.process(payload, context)
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)
