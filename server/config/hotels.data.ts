/**
 * Hotel Data
 *
 * Mock hotel database. In a production application, this would be
 * replaced with a proper database connection (e.g., PostgreSQL, MongoDB).
 *
 * Each hotel entry contains:
 * - hotelName: Unique identifier for the hotel
 * - location: City and state where the hotel is located
 * - roomType: Type of room available
 * - price: Price per night in USD
 * - imageUrl: URL to hotel/room image
 */

import type { Hotel } from "../types/index.js";

export const HOTELS: Hotel[] = [
  {
    hotelName: "Grand Plaza Hotel",
    location: "New York, NY",
    roomType: "Deluxe King",
    price: 0.01,
    imageUrl:
      "https://assets.hyatt.com/content/dam/hyatt/hyattdam/images/2014/09/21/1720/NYCGH-P154-Executive-King.jpg/NYCGH-P154-Executive-King.16x9.jpg",
  },
  {
    hotelName: "Seaside Resort",
    location: "Miami, FL",
    roomType: "Ocean View Suite",
    price: 0.02,
    imageUrl:
      "https://cf.bstatic.com/xdata/images/hotel/max1024x768/390822692.jpg?k=c34015ae993300be2c9cee1b70de695a451a40f61471028096c59be44abe59c9&o=",
  },
  {
    hotelName: "Mountain Retreat",
    location: "Aspen, CO",
    roomType: "Cozy Cabin",
    price: 0.03,
    imageUrl:
      "https://media.vrbo.com/lodging/34000000/33100000/33092200/33092154/dcef192f.jpg?impolicy=resizecrop&rw=1200&ra=fit",
  },
];
