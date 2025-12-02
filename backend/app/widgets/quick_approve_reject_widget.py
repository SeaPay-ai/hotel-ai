"""
Widget helper for displaying approval requests with approve/reject actions.
"""

from __future__ import annotations

from chatkit.widgets import WidgetRoot, WidgetTemplate

# Load the widget template from file
# Note: The file name has a space, so we need to handle it properly
quick_approve_reject_widget_template = WidgetTemplate.from_file("Quick Approve_Reject.widget")


def build_approval_widget(title: str, description: str) -> WidgetRoot:
    """
    Build an approval widget with approve/reject actions.
    
    This widget displays a card with a title and description, and provides
    approve/reject buttons that trigger request.approve and request.reject actions.
    
    Args:
        title: The title text to display (e.g., "Approve this?")
        description: The description text explaining what action requires approval
        
    Returns:
        WidgetRoot: The built widget ready to be streamed to the chat
    """
    payload = {
        "title": title,
        "description": description,
    }
    
    return quick_approve_reject_widget_template.build(payload)

