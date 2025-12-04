"""
Widget helpers for presenting hotel search results as cards.
"""

from __future__ import annotations

from typing import Any

from chatkit.widgets import WidgetRoot, WidgetTemplate

hotel_card_widget_template = WidgetTemplate.from_file("hotel_card.widget")


def build_hotel_card_widget(hotels: list[dict[str, Any]], selected: str | None = None) -> WidgetRoot:
    """
    Render a hotel list widget using the .widget template.
    
    Args:
        hotels: List of hotel dictionaries. Each hotel should have:
            - id (or hotelName will be used as id)
            - hotelName
            - location
            - roomType
            - dates
            - price or pricePerNight
            - image or imageUrl
        selected: Optional hotel ID that is currently selected
    """
    if not hotels:
        # Return empty widget if no hotels
        return hotel_card_widget_template.build({"items": [], "selected": None})
    
    # Transform hotels to match the widget schema
    items = []
    for hotel in hotels:
        # Get or generate hotel ID
        hotel_id = hotel.get("id") or hotel.get("hotelName", "")
        
        # Format price - support both "price" and "pricePerNight"
        price = hotel.get("pricePerNight") or hotel.get("price", "")
        price_str = str(price) if isinstance(price, (int, float)) else price
        
        # Get image URL - support both "image" and "imageUrl"
        image_url = hotel.get("image") or hotel.get("imageUrl") or "https://via.placeholder.com/400x300?text=Hotel"
        
        items.append({
            "id": hotel_id,
            "hotelName": hotel.get("hotelName", ""),
            "location": hotel.get("location", ""),
            "roomType": hotel.get("roomType", ""),
            "dates": hotel.get("dates", ""),
            "price": price_str + "USDC",
            "image": image_url,
        })
    
    payload = {
        "items": items,
        "selected": selected,
    }
    
    return hotel_card_widget_template.build(payload)

