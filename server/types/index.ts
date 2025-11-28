/**
 * Type Definitions
 *
 * Centralized type definitions for the hotel booking API server.
 */

/**
 * Hotel data structure
 */
export interface Hotel {
  hotelName: string;
  location: string;
  roomType: string;
  price: number;
  imageUrl: string;
}

/**
 * Available hotel with booking details
 */
export interface AvailableHotel extends Hotel {
  dates: string;
  adults: number;
  children: number;
}

/**
 * Reservation request data (from body or query)
 */
export interface ReservationRequest {
  hotelName: string;
  checkIn: string;
  checkOut: string;
  adults: number | string;
  children: number | string;
  nights?: number;
}

/**
 * Reservation confirmation
 */
export interface Reservation {
  reservationId: string;
  hotelName: string;
  location: string;
  roomType: string;
  checkIn: string;
  checkOut: string;
  nights: number;
  adults: number;
  children: number;
  totalPrice: number;
  status: "confirmed" | "pending" | "cancelled";
  imageUrl: string;
}

/**
 * Server configuration
 */
export interface ServerConfig {
  PORT: number;
  NODE_ENV: "development" | "production" | "test";
}

/**
 * Hotel prices mapping
 */
export type HotelPrices = Record<string, number>;

/**
 * Price calculation function for dynamic pricing
 */
export type PriceFunction = (body: Record<string, unknown>) => number;

/**
 * Route configuration with dynamic pricing support
 * Extends x402's RouteConfig to support function-based pricing
 */
export interface DynamicRouteConfig {
  price: string | PriceFunction;
  network: string;
  config?: {
    description?: string;
    inputSchema?: Record<string, unknown>;
    outputSchema?: Record<string, unknown>;
    mimeType?: string;
    maxTimeoutSeconds?: number;
    resource?: string;
    discoverable?: boolean;
    customPaywallHtml?: string;
  };
}

/**
 * Payment routes configuration with dynamic pricing support
 */
export type PaymentRoutes = Record<string, DynamicRouteConfig>;
