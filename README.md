# Sea Pay

A multi-component application featuring a ChatKit-powered newsroom assistant and a hotel booking API server with x402 payment integration.

## Project Structure

This repository contains two main components:

1. **News Guide** - A ChatKit-powered newsroom assistant (backend/frontend)
2. **Sea Pay Server** - Hotel booking API with x402 payment middleware and MCP integration (server/)

## Components

### News Guide

Foxhollow Dispatch newsroom assistant showcasing retrieval-heavy ChatKit flows and rich widgets.

**Backend:**
- FastAPI server running on port `8002` (default)
- Python-based ChatKit server with multiple AI agents
- Article and event data stores

**Frontend:**
- React + Vite application running on port `5172` (default)
- ChatKit React integration
- Article browsing and chat interface

### Sea Pay Server

Express server providing hotel booking functionality with x402 payment integration and MCP (Model Context Protocol) support.

**Features:**
- Hotel availability checking
- Room reservation with payment requirement
- x402 payment middleware for protected endpoints
- MCP server for AI agent integration
- Runs on port `3000` (default)

## Quickstart

### Prerequisites

- Node.js >= 18.18
- npm >= 9
- Python 3.x
- `uv` package manager (for Python backend)

### Environment Variables

Export the following environment variables:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export VITE_CHATKIT_API_DOMAIN_KEY="domain_pk_local_dev"  # For local development
```

### Running News Guide

From the repository root:

```bash
# Install root dependencies
npm install

# Run both backend and frontend concurrently
npm run dev
# or
npm run start
```

This will:
- Start the FastAPI backend on `http://localhost:8002`
- Start the Vite frontend on `http://localhost:5172`

Access the application at: http://localhost:5172

### Running Sea Pay Server

From the `server/` directory:

```bash
cd server
npm install
npm run dev  # Development mode with hot reload
# or
npm run build && npm start  # Production mode
```

The server will run on `http://localhost:3000`

**Available Endpoints:**
- `GET /api/check-availability` - Check hotel availability
- `POST /api/reserve` - Reserve a hotel room (requires payment)
- `ALL /mcp` - MCP server endpoint for AI agent integration

## News Guide Example Prompts

- "What's trending right now?" (article search + list widget)
- "Summarize this page for me." (page-aware `get_current_page`)
- "Show me everything tagged parks and outdoor events." (information retrieval using tools)
- "@Elowen latest stories?" (author @-mention lookup; only works when manually typing @, no copy paste)
- "What events are happening this Saturday?" (select the "Event finder" tool from the composer menu first)
- "Give me a quick puzzle break." (select the "Coffee break puzzle" tool from the composer menu)

## News Guide Features

- Retrieval tool suite for metadata and content (`list_available_tags_and_keywords`, `search_articles_by_tags/keywords/exact_text`, `search_articles_by_author`), plus article list widgets to present results.
- Page-aware context via `article-id` request header and `get_current_page` tool for grounded answers about the open article, using the custom fetch ChatKit option.
- Entity tags with previews; tagged articles/authors become `<ARTICLE_REFERENCE>` / `<AUTHOR_REFERENCE>` markers that drive `get_article_by_id`.
- Progress streaming (`ProgressUpdateEvent`) during searches and page loads to keep the UI responsive.
- Composer tool options for explicit agent routing (`event_finder`, `puzzle`) using `tool_choice`.
- Widgets with client and server actions: article list "View" buttons (`open_article`) and event timeline with server-handled `view_event_details` updates.

## Sea Pay Server Features

- Hotel booking API with availability checking
- x402 payment middleware integration for protected endpoints
- Dynamic pricing based on hotel selection and stay duration
- MCP server integration for AI agent tool access
- Express-based RESTful API

## Development

### Backend (News Guide)

The backend uses `uv` for dependency management:

```bash
cd backend
uv sync
```

The backend server is started via the `scripts/run-backend.sh` script, which:
- Sets up a virtual environment
- Syncs dependencies using `uv`
- Runs the FastAPI server with uvicorn on port 8002

### Frontend (News Guide)

The frontend uses Vite and React:

```bash
cd frontend
npm install
npm run dev
```

### Server (Sea Pay)

The server uses TypeScript and Express:

```bash
cd server
npm install
npm run dev  # Uses tsx watch for hot reload
```

## Configuration

### News Guide Backend

- Port: `8002` (configurable via `PORT` environment variable)
- Backend URL: `http://127.0.0.1:8002` (configurable via `BACKEND_URL`)

### News Guide Frontend

- Port: `5172` (default Vite port)
- Proxies `/chatkit`, `/articles`, and `/tags` to the backend

### Sea Pay Server

- Port: `3000` (configurable via `PORT` environment variable)
- Network: `base-sepolia` (testnet) - configured in `server/config/server.config.ts`
- Facilitator URL: `https://x402.org/facilitator`

## License

[Add license information if applicable]
