"""
Authorization utilities for the UFO Sighting Bot.
Now using SQLite database instead of JSON files.
"""
from .database import (
    is_admin_user as db_is_admin_user,
    add_admin_user as db_add_admin_user,
    remove_admin_user as db_remove_admin_user,
    get_admin_users as db_get_admin_users
)

def load_authorized_users():
    """
    Load authorized users configuration from database.
    Returns dict compatible with old JSON format for backward compatibility.
    """
    return {
        "admin_users": db_get_admin_users()
    }

def save_authorized_users(auth_data):
    """
    Save authorized users configuration to database.
    Accepts old JSON format dict for backward compatibility.
    """
    # This is not recommended - use add_admin_user/remove_admin_user instead
    # But kept for backward compatibility
    if "admin_users" in auth_data:
        current_admins = set(db_get_admin_users())
        new_admins = set(auth_data["admin_users"])
        
        # Add new admins
        for user_id in new_admins - current_admins:
            db_add_admin_user(user_id)
        
        # Remove old admins
        for user_id in current_admins - new_admins:
            db_remove_admin_user(user_id)

def is_admin_user(user_id):
    """Check if user is an admin (has access to all admin commands)."""
    return db_is_admin_user(user_id)

def add_admin_user(user_id):
    """Add a user to the admin list."""
    return db_add_admin_user(user_id)

def remove_admin_user(user_id):
    """Remove a user from the admin list."""
    return db_remove_admin_user(user_id)

def get_admin_users():
    """Get list of admin users."""
    return db_get_admin_users()