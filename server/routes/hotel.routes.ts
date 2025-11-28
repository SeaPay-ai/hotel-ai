/**
 * Hotel Routes
 *
 * Express route handlers for hotel booking API endpoints.
 * These routes handle HTTP requests for checking availability and making reservations.
 */

import express, { type Request, type Response } from "express";
import { checkAvailability, reserveHotel } from "../services/hotel.service.js";
import type { ReservationRequest } from "../types/index.js";

const router = express.Router();

/**
 * GET /api/check-availability
 *
 * Check hotel availability for given dates and guest count.
 * This endpoint is free and does not require payment.
 *
 * Query Parameters:
 * - checkIn (required): Check-in date in YYYY-MM-DD format
 * - checkOut (required): Check-out date in YYYY-MM-DD format
 * - adults (required): Number of adults
 * - children (required): Number of children
 *
 * @returns Array of available hotels
 *
 * @example
 * GET /api/check-availability?checkIn=2024-01-15&checkOut=2024-01-20&adults=2&children=1
 */
router.get("/check-availability", (req: Request, res: Response): void => {
  const { checkIn, checkOut, adults, children } = req.query;

  // Validate required query parameters
  if (!checkIn || !checkOut || !adults || !children) {
    res.status(400).json({
      error:
        "Missing required query parameters: checkIn, checkOut, adults, children",
    });
    return;
  }

  try {
    const availableHotels = checkAvailability(
      checkIn as string,
      checkOut as string,
      parseInt(adults as string, 10),
      parseInt(children as string, 10)
    );

    res.json(availableHotels);
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error occurred";
    res.status(500).json({
      error: "Failed to check availability",
      message: errorMessage,
    });
  }
});

/**
 * POST /api/reserve
 *
 * Reserve a hotel room. This endpoint is protected by x402 payment middleware
 * and requires payment before processing the reservation.
 *
 * Request Body or Query Parameters:
 * - hotelName (required): Name of the hotel to reserve
 * - checkIn (required): Check-in date in YYYY-MM-DD format
 * - checkOut (required): Check-out date in YYYY-MM-DD format
 * - adults (required): Number of adults
 * - children (required): Number of children
 *
 * @returns Reservation confirmation with reservation ID and details
 *
 * @example
 * POST /api/reserve
 * {
 *   "hotelName": "Grand Plaza Hotel",
 *   "checkIn": "2024-01-15",
 *   "checkOut": "2024-01-20",
 *   "adults": 2,
 *   "children": 1,
 * }
 */
router.post("/reserve", (req: Request, res: Response): void => {
  // Support both JSON body and query parameters
  const requestData: Partial<ReservationRequest> =
    Object.keys(req.body || {}).length > 0 ? req.body : req.query;

  const { hotelName, checkIn, checkOut, adults, children } = requestData;

  // Validate required fields
  if (!hotelName || !checkIn || !checkOut || !adults || !children) {
    res.status(400).json({
      error:
        "Missing required fields: hotelName, checkIn, checkOut, adults, children",
    });
    return;
  }

  try {
    // Process the reservation
    // Convert string values to numbers if they come from query params
    const adultsNum =
      typeof adults === "string" ? parseInt(adults, 10) : Number(adults);
    const childrenNum =
      typeof children === "string" ? parseInt(children, 10) : Number(children);

    const reservation = reserveHotel(
      hotelName as string,
      checkIn as string,
      checkOut as string,
      adultsNum,
      childrenNum
    );

    // Return success response with reservation details
    res.json({
      success: true,
      reservation,
      message: "Reservation confirmed successfully",
    });
  } catch (error) {
    // Return error response
    const errorMessage =
      error instanceof Error ? error.message : "Unknown error occurred";
    res.status(400).json({
      success: false,
      error: errorMessage,
    });
  }
});

export default router;
