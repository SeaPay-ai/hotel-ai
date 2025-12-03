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
 * - guests (required): Total number of guests
 *
 * @returns Array of available hotels
 *
 * @example
 * GET /api/check-availability?checkIn=2024-01-15&checkOut=2024-01-20&guests=2
 */
router.get("/check-availability", (req: Request, res: Response): void => {
  const { checkIn, checkOut, destination, guests } = req.query;

  // Validate required query parameters
  if (!checkIn || !checkOut || !destination || !guests) {
    res.status(400).json({
      error:
        "Missing required query parameters: checkIn, checkOut, destination, guests",
    });
    return;
  }

  try {
    const guestsNum = parseInt(guests as string, 10);

    const availableHotels = checkAvailability(
      checkIn as string,
      checkOut as string,
      destination as string,
      guestsNum
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
 * - guests (required): Total number of guests
 *
 * @returns Reservation confirmation with reservation ID and details
 *
 * @example
 * POST /api/reserve
 * {
 *   "hotelName": "Grand Plaza Hotel",
 *   "checkIn": "2024-01-15",
 *   "checkOut": "2024-01-20",
 *   "guests": 2
 * }
 */
router.post("/reserve", (req: Request, res: Response): void => {
  // Support both JSON body and query parameters
  const requestData: Partial<ReservationRequest> =
    Object.keys(req.body || {}).length > 0 ? req.body : req.query;

  const { hotelName, checkIn, checkOut, guests } = requestData;

  // Validate required fields
  if (!hotelName || !checkIn || !checkOut || !guests) {
    res.status(400).json({
      error:
        "Missing required fields: hotelName, checkIn, checkOut, guests",
    });
    return;
  }

  try {
    // Process the reservation
    // Convert string value to number if it comes from query params
    const guestsNum =
      typeof guests === "string" ? parseInt(guests, 10) : Number(guests);

    const reservation = reserveHotel(
      hotelName as string,
      checkIn as string,
      checkOut as string,
      guestsNum
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
