/**
 * Server Configuration
 *
 * Centralized configuration for the Express server.
 * Contains server settings, x402 payment middleware configuration,
 * and other runtime settings.
 *
 * @see https://x402.org/docs for x402 payment integration information
 */

import type {
  PaymentRoutes,
  PriceFunction,
  HotelPrices,
} from "../types/index.js";

// ============================================================================
// SERVER CONFIGURATION
// ============================================================================

/**
 * Server configuration settings
 */
export const SERVER_CONFIG = {
  /**
   * Port number for the Express server
   * Default: 3000
   */
  PORT: Number(process.env.PORT) || 3000,

  /**
   * Environment mode
   * 'development' | 'production' | 'test'
   */
  NODE_ENV: (process.env.NODE_ENV || "development") as
    | "development"
    | "production"
    | "test",
} as const;

// ============================================================================
// X402 PAYMENT MIDDLEWARE CONFIGURATION
// ============================================================================

/**
 * Your receiving wallet address where payments will be sent
 * IMPORTANT: Replace with your actual wallet address
 */
export const RECEIVING_WALLET_ADDRESS =
  "0xCc37efEE4Dc6b2552fb14e1D5fBD51D57847d7d9";

/**
 * x402 Facilitator URL
 * - Testnet: "https://x402.org/facilitator"
 * - Mainnet: Use CDP facilitator (requires API keys)
 */
export const FACILITATOR_URL = "https://x402.org/facilitator";

/**
 * Network configuration
 * - "base-sepolia" for testnet
 * - "base" for mainnet
 * - "solana" for Solana network
 */
export const NETWORK = "base-sepolia" as const;

/**
 * Hotel prices per night in USD
 */
const HOTEL_PRICES: HotelPrices = {
  "Grand Plaza Hotel": 0.01,
  "Oceanview Resort": 0.02,
  "Urban Loft Chicago": 0.03,
  "Luxury Suites NYC": 0.04,
  "Midtown Grand Hotel": 0.05,
  "Brooklyn Boutique": 0.01,
  "Windy City Inn": 0.02,
  "Lakeside Hotel Chicago": 0.03,
  "Hollywood Hills Hotel": 0.04,
  "LA Downtown Suites": 0.05,
};

/**
 * Calculate number of nights between check-in and check-out dates
 *
 * @param checkIn - Check-in date string (YYYY-MM-DD)
 * @param checkOut - Check-out date string (YYYY-MM-DD)
 * @returns Number of nights
 */
function calcNights(checkIn: string, checkOut: string): number {
  const inD = new Date(checkIn);
  const outD = new Date(checkOut);

  const msPerDay = 1000 * 60 * 60 * 24;
  const diffMs =
    Date.UTC(outD.getFullYear(), outD.getMonth(), outD.getDate()) -
    Date.UTC(inD.getFullYear(), inD.getMonth(), inD.getDate());

  return diffMs / msPerDay;
}

/**
 * Price calculation function for dynamic pricing
 *
 * @param body - Request body containing hotel reservation details
 * @returns Calculated price in USD
 * @throws Error if hotel is not found
 */
const calculateReservationPrice: PriceFunction = (
  body: Record<string, unknown>
): number => {
  const hotelName = body.hotelName as string;
  const checkIn = body.checkIn as string;
  const checkOut = body.checkOut as string;
  const nights = body.nights as number | undefined;

  const nightly = HOTEL_PRICES[hotelName];
  if (!nightly) {
    throw new Error(`Unknown hotel: ${hotelName}`);
  }

  return nightly * (nights ?? calcNights(checkIn, checkOut));
};

/**
 * Payment route configurations
 * Defines which endpoints require payment and their pricing/metadata
 */
export const PAYMENT_ROUTES: PaymentRoutes = {
  // Reserve endpoint configuration
  "POST /api/reserve": {
    // USDC amount in dollars (dynamic pricing function)
    price: calculateReservationPrice,
    network: NETWORK,

    // Metadata for x402 Bazaar discovery
    config: {
      description:
        "Reserve a hotel room. Requires payment to complete the reservation.",

      // Input schema for API documentation and discovery
      inputSchema: {
        type: "object",
        properties: {
          hotelName: {
            type: "string",
            description: "Name of the hotel to reserve",
          },
          checkIn: {
            type: "string",
            description: "Check-in date (YYYY-MM-DD)",
          },
          checkOut: {
            type: "string",
            description: "Check-out date (YYYY-MM-DD)",
          },
          guests: {
            type: "number",
            description: "Total number of guests",
          },
        },
        required: ["hotelName", "checkIn", "checkOut", "guests"],
      },

      // Output schema for API documentation and discovery
      outputSchema: {
        type: "object",
        properties: {
          reservationId: {
            type: "string",
            description: "Unique reservation confirmation ID",
          },
          hotelName: { type: "string", description: "Hotel name" },
          roomType: { type: "string", description: "Room type reserved" },
          checkIn: { type: "string", description: "Check-in date" },
          checkOut: { type: "string", description: "Check-out date" },
          totalPrice: {
            type: "number",
            description: "Total price for the reservation",
          },
          status: {
            type: "string",
            description: "Reservation status (confirmed, pending, etc.)",
          },
        },
      },
    },
  },
};
