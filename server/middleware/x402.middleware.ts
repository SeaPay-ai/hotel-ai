/**
 * x402 Payment Middleware
 *
 * Configures and applies x402 payment middleware to protect API endpoints.
 * This middleware enables crypto payment requirements for specified routes.
 *
 * When a request is made to protected routes without payment:
 * - Server responds with HTTP 402 Payment Required
 * - Payment instructions are included in the response body
 *
 * When payment is included (via X-PAYMENT header):
 * - Middleware verifies payment via the facilitator
 * - Request proceeds to the route handler if payment is valid
 *
 * Supports dynamic pricing via price functions that calculate price based on request body.
 *
 * @see https://x402.org/docs for more information
 */

import { paymentMiddleware } from "x402-express";
import type { Request, Response, NextFunction } from "express";
import type { RoutesConfig } from "x402/types";
import {
  RECEIVING_WALLET_ADDRESS,
  PAYMENT_ROUTES,
  FACILITATOR_URL,
} from "../config/server.config.js";
import type { DynamicRouteConfig, PriceFunction } from "../types/index.js";

/**
 * Configure and return x402 payment middleware with dynamic pricing support
 *
 * This wrapper handles routes with dynamic pricing (function-based prices)
 * by calculating the price per request and creating middleware instances dynamically.
 *
 * @returns Express middleware function
 */
export const configureX402Middleware = (): ((
  req: Request,
  res: Response,
  next: NextFunction
) => Promise<void>) => {
  // Separate routes with static prices from routes with dynamic prices
  const staticRoutes: RoutesConfig = {};
  const dynamicRouteConfigs: Record<string, DynamicRouteConfig> = {};

  for (const [route, config] of Object.entries(PAYMENT_ROUTES)) {
    if (typeof config.price === "function") {
      dynamicRouteConfigs[route] = config;
    } else {
      // Static price routes can be used directly with x402
      staticRoutes[route] = config as RoutesConfig[string];
    }
  }

  // Create middleware for static routes (only if there are any)
  const staticMiddleware =
    Object.keys(staticRoutes).length > 0
      ? paymentMiddleware(RECEIVING_WALLET_ADDRESS, staticRoutes, {
          url: FACILITATOR_URL,
        })
      : null;

  // Return combined middleware
  return async (
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> => {
    const routeKey = `${req.method.toUpperCase()} ${req.path}`;
    const dynamicConfig = dynamicRouteConfigs[routeKey];

    // Handle dynamic pricing routes
    if (dynamicConfig) {
      try {
        // Calculate price based on request body or query parameters
        // Support both JSON body and query parameters for flexibility
        const requestData =
          Object.keys(req.body || {}).length > 0 ? req.body : req.query;

        const priceFunction = dynamicConfig.price as PriceFunction;
        const calculatedPrice = priceFunction(requestData || {});

        // Format price as string (x402 expects "$X.XX" format)
        const priceString = `$${calculatedPrice.toFixed(2)}`;

        // Create a temporary route config with the calculated price
        // Convert to RoutesConfig format expected by x402
        const tempRoutes: RoutesConfig = {
          [routeKey]: {
            ...dynamicConfig,
            price: priceString,
          } as RoutesConfig[string],
        };

        // Create a new middleware instance with the calculated price
        const dynamicMiddleware = paymentMiddleware(
          RECEIVING_WALLET_ADDRESS,
          tempRoutes,
          {
            url: FACILITATOR_URL,
          }
        );

        // Execute the middleware
        await dynamicMiddleware(req, res, next);
        return;
      } catch (error) {
        // If price calculation fails, return error
        const errorMessage =
          error instanceof Error ? error.message : "Unknown error occurred";
        res.status(400).json({
          error: "Failed to calculate price",
          message: errorMessage,
        });
        return;
      }
    }

    // Handle static pricing routes
    if (staticMiddleware) {
      await staticMiddleware(req, res, next);
      return;
    }

    // No matching route, continue to next middleware
    next();
  };
};

