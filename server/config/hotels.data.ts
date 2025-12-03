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
    hotelName: "Oceanview Resort",
    location: "Los Angeles, CA",
    roomType: "Ocean View Suite",
    price: 0.02,
    imageUrl:
      "https://www.marriott.com/content/dam/marriott-product/marriott/marriott-la-live/marriott-la-live-guest-room-king.jpg",
  },
  {
    hotelName: "Urban Loft Chicago",
    location: "Chicago, IL",
    roomType: "City View Studio",
    price: 0.03,
    imageUrl:
      "https://cache.marriott.com/content/dam/marriott-product/marriott/marriott-chicago-downtown-magnificent-mile/marriott-chicago-downtown-magnificent-mile-exterior.jpg",
  },
  {
    hotelName: "Midtown Grand Hotel",
    location: "New York, NY",
    roomType: "Standard Queen",
    price: 0.05,
    imageUrl:
      "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSxc7i62iba1D8a381plgSmkRCiE2pKVbzVFw&s",
  },
  {
    hotelName: "Brooklyn Boutique",
    location: "New York, NY",
    roomType: "Studio Apartment",
    price: 0.01,
    imageUrl:
      "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_QF71UDiLRMUK5EW_MICQnH0HvNIp4L_a1Q&s",
  },
  {
    hotelName: "Windy City Inn",
    location: "Chicago, IL",
    roomType: "Double Room",
    price: 0.02,
    imageUrl:
      "https://cache.marriott.com/content/dam/marriott-product/marriott/marriott-chicago-downtown-magnificent-mile/marriott-chicago-downtown-magnificent-mile-exterior.jpg",
  },
  {
    hotelName: "Lakeside Hotel Chicago",
    location: "Chicago, IL",
    roomType: "King Suite with Lake View",
    price: 0.03,
    imageUrl:
      "https://cache.marriott.com/content/dam/marriott-product/marriott/marriott-chicago-downtown-magnificent-mile/marriott-chicago-downtown-magnificent-mile-exterior.jpg",
  },
  {
    hotelName: "Hollywood Hills Hotel",
    location: "Los Angeles, CA",
    roomType: "Luxury Villa",
    price: 0.04,
    imageUrl:
      "https://www.marriott.com/content/dam/marriott-product/marriott/marriott-la-live/marriott-la-live-guest-room-king.jpg",
  },
  {
    hotelName: "LA Downtown Suites",
    location: "Los Angeles, CA",
    roomType: "Executive Studio",
    price: 0.05,
    imageUrl:
      "https://www.marriott.com/content/dam/marriott-product/marriott/marriott-la-live/marriott-la-live-guest-room-king.jpg",
  },
];
