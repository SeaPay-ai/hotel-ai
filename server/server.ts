/**
 * Main Server Entry Point
 *
 * This is the main Express server application that:
 * 1. Sets up Express middleware
 * 2. Configures x402 payment middleware for protected endpoints
 * 3. Registers API routes
 * 4. Sets up MCP (Model Context Protocol) server for AI agent integration
 * 5. Starts the HTTP server
 *
 * @module server
 */

import express, { type Express } from "express";
import { SERVER_CONFIG } from "./config/server.config.js";
import { configureX402Middleware } from "./middleware/x402.middleware.js";
import hotelRoutes from "./routes/hotel.routes.js";
import {
  createMcpServer,
  createMcpHandler,
} from "./middleware/mcp.middleware.js";

// Initialize Express application
const app: Express = express();

// Apply body parser middleware
// This allows the server to parse JSON request bodies and URL-encoded forms
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ---------------------------------------------------------
// 1. X402 PAYMENT MIDDLEWARE
// ---------------------------------------------------------
// Apply x402 payment middleware to protect certain endpoints
// Requests to protected routes without payment will receive HTTP 402
app.use(configureX402Middleware());

// ---------------------------------------------------------
// 2. API ROUTES
// ---------------------------------------------------------
// Register hotel booking API routes
// All routes are prefixed with /api
app.use("/api", hotelRoutes);

// ---------------------------------------------------------
// 3. MCP SERVER SETUP
// ---------------------------------------------------------
// Set up MCP server for AI agent integration
// This allows AI agents to use hotel booking functionality as tools
const mcpServer = createMcpServer();
const mcpHandler = createMcpHandler(mcpServer);

// Register MCP endpoint
// AI agents can connect to this endpoint to use the hotel booking tools
app.all("/mcp", mcpHandler);

// ---------------------------------------------------------
// 4. START SERVER
// ---------------------------------------------------------
// Start the HTTP server and listen on the configured port
app.listen(SERVER_CONFIG.PORT, (): void => {
  console.log(`Server running on http://localhost:${SERVER_CONFIG.PORT}`);
  console.log(`MCP Endpoint: http://localhost:${SERVER_CONFIG.PORT}/mcp`);
  console.log(`API Endpoints:`);
  console.log(
    `  GET  http://localhost:${SERVER_CONFIG.PORT}/api/check-availability`
  );
  console.log(
    `  POST http://localhost:${SERVER_CONFIG.PORT}/api/reserve (requires payment)`
  );
});
