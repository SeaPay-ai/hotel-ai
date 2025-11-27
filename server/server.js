import express from 'express';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { z } from 'zod';

const app = express();
const PORT = 3000;

app.use(express.json());

// ---------------------------------------------------------
// 1. YOUR HOTEL BOOKING EXPRESS API
// ---------------------------------------------------------
const hotels = [
  {
    hotelName: "Grand Plaza Hotel",
    location: "New York, NY",
    roomType: "Deluxe King",
    price: 250,
    imageUrl: "https://assets.hyatt.com/content/dam/hyatt/hyattdam/images/2014/09/21/1720/NYCGH-P154-Executive-King.jpg/NYCGH-P154-Executive-King.16x9.jpg"
  },
  {
    hotelName: "Seaside Resort",
    location: "Miami, FL",
    roomType: "Ocean View Suite",
    price: 350,
    imageUrl: "https://example.com/seaside-resort.jpg"
  },
  {
    hotelName: "Mountain Retreat",
    location: "Aspen, CO",
    roomType: "Cozy Cabin",
    price: 450,
    imageUrl: "https://example.com/mountain-retreat.jpg"
  }
];

// Helper function to perform availability check (mock logic)
const checkAvailability = (checkIn, checkOut, adults, children) => {
  // In a real app, we would query a database using these parameters.
  // For this mock, we return the static list of hotels, adding the requested dates to each.
  return hotels.map(hotel => ({
    ...hotel,
    dates: `${checkIn} to ${checkOut}`,
    adults,
    children
  }));
};

app.get('/api/check-availability', (req, res) => {
  const { checkIn, checkOut, adults, children } = req.query;

  if (!checkIn || !checkOut || !adults || !children) {
    return res.status(400).json({ error: "Missing required query parameters: checkIn, checkOut, adults, children" });
  }

  const availableHotels = checkAvailability(checkIn, checkOut, parseInt(adults), parseInt(children));
  res.json(availableHotels);
});

// ---------------------------------------------------------
// 2. THE MCP SERVER SETUP
// ---------------------------------------------------------
const mcpServer = new McpServer({
  name: "Hotel Booking API",
  version: "1.0.0"
});

mcpServer.registerTool(
  "check_availability",
  {
    description: "Checks hotel availability based on dates and guest count.",
    inputSchema: z.object({
      checkIn: z.string().describe("Check-in date (YYYY-MM-DD)."),
      checkOut: z.string().describe("Check-out date (YYYY-MM-DD)."),
      adults: z.number().describe("Number of adults."),
      children: z.number().describe("Number of children.")
    })
  },
  async ({ checkIn, checkOut, adults, children }) => {
    const availableHotels = checkAvailability(checkIn, checkOut, adults, children);
    return {
      content: [{ type: "text", text: JSON.stringify(availableHotels, null, 2) }]
    };
  }
);

// ---------------------------------------------------------
// 3. THE NEW STREAMABLE TRANSPORT (Handling Connections)
// ---------------------------------------------------------
let transport;

app.all('/mcp', async (req, res) => {
  if (!transport) {
    transport = new StreamableHTTPServerTransport({
        path: "/mcp", 
    });
    await mcpServer.connect(transport);
  }
  await transport.handleRequest(req, res, req.body);
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
  console.log(`MCP Endpoint: http://localhost:${PORT}/mcp`);
});
