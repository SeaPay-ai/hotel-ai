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
        adults: z.number().describe("Number of adults."),
        children: z.number().describe("Number of children."),
      }),
    },
    async ({ checkIn, checkOut, adults, children }) => {
      const availableHotels = checkAvailability(
        checkIn,
        checkOut,
        adults,
        children
      );

      return {
        content: [
          { type: "text", text: JSON.stringify(availableHotels, null, 2) },
        ],
      };
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
