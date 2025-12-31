"""
Ticket management utilities for the UFO Sighting Bot.
Now using SQLite database instead of JSON files.
"""
import uuid
from datetime import datetime, timedelta
from .database import (
    create_ticket as db_create_ticket,
    get_ticket as db_get_ticket,
    update_ticket as db_update_ticket,
    close_ticket as db_close_ticket,
    delete_ticket as db_delete_ticket,
    get_user_tickets as db_get_user_tickets,
    get_all_tickets as db_get_all_tickets,
    get_open_tickets as db_get_open_tickets,
    get_guild_tickets as db_get_guild_tickets
)

def load_tickets():
    """
    Load support tickets from database.
    Returns dict compatible with old JSON format for backward compatibility.
    """
    return db_get_all_tickets()

def save_tickets(tickets_data):
    """
    Save support tickets to database.
    Accepts old JSON format dict for backward compatibility.
    Note: This is not recommended - use individual ticket functions instead.
    """
    # This is kept for backward compatibility but is not efficient
    # It's better to use create_ticket, update_ticket, etc. directly
    pass  # Database operations are atomic, no bulk save needed

def create_ticket(user_id, user_name, guild_id, guild_name, message):
    """Create a new support ticket and return the ticket ID."""
    # Generate unique ticket ID
    ticket_id = str(uuid.uuid4())[:8]
    
    # Create ticket in database
    db_create_ticket(ticket_id, user_id, user_name, guild_id, guild_name, message)
    
    return ticket_id

def get_ticket(ticket_id):
    """Get a specific ticket by ID."""
    return db_get_ticket(ticket_id)

def update_ticket(ticket_id, updates):
    """Update a ticket with new information."""
    return db_update_ticket(ticket_id, **updates)

def close_ticket(ticket_id, closed_by="admin", admin_response=None, admin_responder=None):
    """Close a ticket and mark it as resolved."""
    return db_close_ticket(ticket_id, closed_by, admin_response, admin_responder)

def delete_ticket(ticket_id):
    """Permanently delete a ticket."""
    return db_delete_ticket(ticket_id)

def get_user_tickets(user_id, status_filter=None):
    """Get all tickets for a specific user, optionally filtered by status."""
    return db_get_user_tickets(user_id, status_filter)

def get_open_tickets():
    """Get all open tickets."""
    return db_get_open_tickets()

def cleanup_old_tickets(days_old=30):
    """Delete tickets older than specified days that are closed."""
    tickets = db_get_all_tickets()
    cutoff_date = datetime.now() - timedelta(days=days_old)
    tickets_to_delete = []
    
    for ticket_id, ticket in tickets.items():
        # Only delete closed tickets
        if ticket["status"].startswith("closed"):
            ticket_date = datetime.fromisoformat(ticket["created_at"])
            if ticket_date < cutoff_date:
                tickets_to_delete.append(ticket_id)
    
    # Delete old tickets
    count = 0
    for ticket_id in tickets_to_delete:
        if db_delete_ticket(ticket_id):
            count += 1
    
    return count
