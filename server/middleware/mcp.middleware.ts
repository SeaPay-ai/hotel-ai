/**
 * MCP (Model Context Protocol) Middleware
 *
 * Sets up and configures the MCP server for AI agent integration.
 * The MCP server exposes hotel booking functionality as tools that
 * AI agents can use to interact with the API.
 *
 * @see https://modelcontextprotocol.io for more information
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import type { Request, Response } from "express";
import { z } from "zod";
import { checkAvailability } from "../services/hotel.service.js";
import { SERVER_CONFIG } from "../config/server.config.js";

/**
 * Create and configure the MCP server instance
 *
 * @returns Configured MCP server instance
 */
export const createMcpServer = (): McpServer => {
  const mcpServer = new McpServer({
    name: "Hotel Booking API",
    version: "1.0.0",
  });

  // Register the check_availability tool
  // This allows AI agents to check hotel availability
  mcpServer.registerTool(
    "check_availability",
    {
      description: "Checks hotel availability based on dates and guest count.",
      inputSchema: z.object({
        checkIn: z.string().describe("Check-in date (YYYY-MM-DD)."),
        checkOut: z.string().describe("Check-out date (YYYY-MM-DD)."),
        destination: z.string().describe("Destination city or location."),
        guests: z.number().describe("Total number of guests."),
      }),
    },
    async ({ checkIn, checkOut, destination, guests }) => {
      const availableHotels = checkAvailability(
        checkIn,
        checkOut,
        destination,
        guests
      );

      return {
        content: [
          { type: "text", text: JSON.stringify(availableHotels, null, 2) },
        ],
      };
    }
  );

  // Register the reserve tool
  // This allows AI agents to make hotel reservations
  // The tool implementation calls the HTTP /api/reserve endpoint so that
  // x402 payment middleware can protect the reservation flow.
  mcpServer.registerTool(
    "reserve",
    {
      description:
        "Reserves a hotel room. Creates a reservation for the specified hotel and dates. Returns a reservation confirmation with reservation ID and details.",
      inputSchema: z.object({
        hotelName: z
          .string()
          .describe(
            "Name of the hotel to reserve. Must match one of the available hotels exactly."
          ),
        checkIn: z.string().describe("Check-in date (YYYY-MM-DD)."),
        checkOut: z.string().describe("Check-out date (YYYY-MM-DD)."),
        guests: z.number().describe("Total number of guests."),
      }),
    },
    async ({ hotelName, checkIn, checkOut, guests }) => {
      try {
        // Call the payment-protected REST API endpoint so that x402
        // can enforce payment (and potentially return HTTP 402).
        const response = await (globalThis as any).fetch(
          `http://localhost:${SERVER_CONFIG.PORT}/api/reserve`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              hotelName,
              checkIn,
              checkOut,
              guests,
            }),
          }
        );

        let data: unknown = null;
        try {
          data = await response.json();
        } catch {
          // If the response is not JSON, keep data as null
        }

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  success: response.ok,
                  status: response.status,
                  body: data,
                },
                null,
                2
              ),
            },
          ],
          isError: !response.ok,
        };
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Unknown error occurred";
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  success: false,
                  error: errorMessage,
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        };
      }
    }
  );

  return mcpServer;
};

/**
 * Handle MCP requests via HTTP transport
 *
 * Creates and manages the streamable HTTP transport for MCP server.
 * This allows the MCP server to communicate over HTTP.
 *
 * @param mcpServer - The MCP server instance
 * @returns Express route handler function
 */
export const createMcpHandler = (
  mcpServer: McpServer
): ((req: Request, res: Response) => Promise<void>) => {
  let transport: StreamableHTTPServerTransport | undefined;

  return async (req: Request, res: Response): Promise<void> => {
    // Initialize transport on first request
    if (!transport) {
      transport = new StreamableHTTPServerTransport({
        sessionIdGenerator: undefined, // Stateless transport
      });
      await mcpServer.connect(transport);
    }

    // Handle the MCP request
    await transport.handleRequest(req, res, req.body);
  };
};
