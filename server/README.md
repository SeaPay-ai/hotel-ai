# Sea Pay Server

A TypeScript Express server that provides hotel booking functionality with crypto payment integration via x402 and AI agent support via MCP (Model Context Protocol).

## Features

- **Hotel Availability Checking**: Free endpoint to check hotel availability
- **Hotel Reservations**: Payment-protected endpoint for making reservations
- **x402 Payment Integration**: Crypto payment middleware for monetizing API endpoints
- **MCP Server**: AI agent integration with tools for hotel booking operations

## MCP Server Tools

The MCP server exposes two tools for AI agents:

### 1. `check_availability`

Checks hotel availability for given dates and guest count.

**Parameters:**

- `checkIn` (string): Check-in date in YYYY-MM-DD format
- `checkOut` (string): Check-out date in YYYY-MM-DD format
- `guests` (number): Total number of guests

**Returns:** Array of available hotels with booking details

### 2. `reserve`

Reserves a hotel room. Creates a reservation for the specified hotel and dates.

**Parameters:**

- `hotelName` (string): Name of the hotel to reserve (must match exactly)
- `checkIn` (string): Check-in date in YYYY-MM-DD format
- `checkOut` (string): Check-out date in YYYY-MM-DD format
- `guests` (number): Total number of guests

**Returns:** Reservation confirmation with reservation ID and details

## Installation

1. Install dependencies:

```bash
npm install
```

## Configuration

### Wallet Address

Before running the server, update your receiving wallet address in `config/server.config.ts`:

```typescript
export const RECEIVING_WALLET_ADDRESS = "0xYourAddress"; // Replace with your wallet
```

### Network Configuration

The server is configured for testnet by default. To use mainnet:

1. Update `config/server.config.ts`:

   - Change `NETWORK` from `"base-sepolia"` to `"base"`
   - Set up CDP API keys (see x402 documentation)

2. Set environment variables:

```bash
CDP_API_KEY_ID=your-api-key-id
CDP_API_KEY_SECRET=your-api-key-secret
```

## Running the Server

### Development Mode (with hot reload)

```bash
npm run dev
```

This starts the server with TypeScript hot reload using `tsx watch`. The server will automatically restart when you make changes to the code.

### Production Mode

1. Build the TypeScript code:

```bash
npm run build
```

2. Start the compiled server:

```bash
npm start
```

### Type Checking

Check TypeScript types without compiling:

```bash
npm run type-check
```

## Server Endpoints

Once the server is running, you'll see:

- **Server**: `http://localhost:3000`
- **MCP Endpoint**: `http://localhost:3000/mcp`
- **API Endpoints**:
  - `GET http://localhost:3000/api/check-availability` - Check hotel availability (free)
  - `POST http://localhost:3000/api/reserve` - Reserve a hotel (requires payment)

## MCP Server Usage

The MCP server is accessible at `http://localhost:3000/mcp`. AI agents can connect to this endpoint to use the hotel booking tools.

### Connecting an AI Agent

To connect an AI agent (like Claude Desktop) to this MCP server:

1. **Add to Claude Desktop configuration** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "sea-pay": {
      "command": "node",
      "args": ["/path/to/sea-pay/server/dist/server.js"],
      "env": {}
    }
  }
}
```

Or use HTTP transport:

```json
{
  "mcpServers": {
    "sea-pay": {
      "url": "http://localhost:3000/mcp"
    }
  }
}
```

2. **Restart Claude Desktop**

3. **Use the tools**: The AI agent will now have access to:
   - `check_availability` - Check hotel availability
   - `reserve` - Make hotel reservations

### Example MCP Tool Usage

An AI agent can use the tools like this:

**Check Availability:**

```json
{
  "tool": "check_availability",
  "arguments": {
    "checkIn": "2025-11-25",
    "checkOut": "2025-11-30",
    "guests": 2
  }
}
```

**Make Reservation:**

```json
{
  "tool": "reserve",
  "arguments": {
    "hotelName": "Grand Plaza Hotel",
    "checkIn": "2025-11-25",
    "checkOut": "2025-11-30",
    "guests": 2
  }
}
```

## API Usage Examples

### Check Availability (Free)

```bash
curl "http://localhost:3000/api/check-availability?checkIn=2025-11-25&checkOut=2025-11-30&guests=2"
```

### Reserve Hotel (Requires Payment)

```bash
curl -X POST "http://localhost:3000/api/reserve" \
  -H "Content-Type: application/json" \
  -d '{
    "hotelName": "Grand Plaza Hotel",
    "checkIn": "2025-11-25",
    "checkOut": "2025-11-30",
    "guests": 2
  }'
```

Without payment, this will return HTTP 402 Payment Required with payment instructions.

## Project Structure

```
server/
├── config/              # Configuration files
│   ├── server.config.ts # Server and x402 configuration
│   └── hotels.data.ts  # Hotel database
├── middleware/          # Express middleware
│   ├── x402.middleware.ts # Payment middleware
│   └── mcp.middleware.ts  # MCP server setup
├── routes/              # API routes
│   └── hotel.routes.ts # Hotel endpoints
├── services/            # Business logic
│   └── hotel.service.ts # Hotel operations
├── types/               # TypeScript types
│   └── index.ts        # Type definitions
├── server.ts           # Main entry point
└── tsconfig.json      # TypeScript configuration
```

## Development

### Adding New MCP Tools

To add a new MCP tool:

1. Open `middleware/mcp.middleware.ts`
2. Add a new `mcpServer.registerTool()` call in `createMcpServer()`
3. Define the tool schema using Zod
4. Implement the tool handler function

Example:

```typescript
mcpServer.registerTool(
  "tool_name",
  {
    description: "Tool description",
    inputSchema: z.object({
      param1: z.string().describe("Parameter description"),
    }),
  },
  async ({ param1 }) => {
    // Tool implementation
    return {
      content: [{ type: "text", text: JSON.stringify(result, null, 2) }],
    };
  }
);
```

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, change it in `config/server.config.ts`:

```typescript
PORT: process.env.PORT || 3000, // Change 3000 to another port
```

Or set the PORT environment variable:

```bash
PORT=3001 npm run dev
```

### TypeScript Errors

Run type checking:

```bash
npm run type-check
```

### MCP Connection Issues

- Ensure the server is running before connecting
- Check that the MCP endpoint is accessible: `http://localhost:3000/mcp`
- Verify the transport is initialized (check server logs)

## License

See LICENSE file in project root.

## Resources

- [x402 Documentation](https://x402.org/docs)
- [MCP Documentation](https://modelcontextprotocol.io)
- [Express.js Documentation](https://expressjs.com)
