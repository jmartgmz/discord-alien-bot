"""
SQLite database utilities for the UFO Sighting Bot.
Handles all database operations with proper connection management and thread safety.
"""
import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
from threading import Lock

# Database file path
DB_FILE = "data/ufo_bot.db"

# Thread-safe lock for database operations
db_lock = Lock()


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures proper connection handling and thread safety.
    """
    with db_lock:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_database():
    """
    Initialize the database schema.
    Creates all necessary tables if they don't exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Guild configuration table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                log_channel_id INTEGER,
                support_channel_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Global settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS global_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User reactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reaction_count INTEGER DEFAULT 0,
                last_reaction_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id)
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_reactions_guild 
            ON user_reactions(guild_id)
        """)
        
        # Admin users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                user_id INTEGER PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Banned users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (
                user_id INTEGER PRIMARY KEY,
                reason TEXT,
                banned_by INTEGER,
                banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tickets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                guild_id INTEGER NOT NULL,
                guild_name TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                admin_response TEXT,
                admin_responder TEXT,
                response_timestamp TIMESTAMP,
                closed_by TEXT,
                closed_timestamp TIMESTAMP
            )
        """)
        
        # Create indexes for tickets
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickets_user 
            ON tickets(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickets_status 
            ON tickets(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickets_guild 
            ON tickets(guild_id)
        """)
        
        conn.commit()


# ============================================================================
# Guild Configuration Functions
# ============================================================================

def get_guild_config(guild_id):
    """Get configuration for a specific guild."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM guild_config WHERE guild_id = ?
        """, (guild_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def set_guild_config(guild_id, channel_id=None, log_channel_id=None, support_channel_id=None):
    """Set or update configuration for a guild."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if config exists
        existing = get_guild_config(guild_id)
        
        if existing:
            # Update existing config
            updates = []
            params = []
            if channel_id is not None:
                updates.append("channel_id = ?")
                params.append(channel_id)
            if log_channel_id is not None:
                updates.append("log_channel_id = ?")
                params.append(log_channel_id)
            if support_channel_id is not None:
                updates.append("support_channel_id = ?")
                params.append(support_channel_id)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(guild_id)
                cursor.execute(f"""
                    UPDATE guild_config 
                    SET {', '.join(updates)}
                    WHERE guild_id = ?
                """, params)
        else:
            # Insert new config
            cursor.execute("""
                INSERT INTO guild_config (guild_id, channel_id, log_channel_id, support_channel_id)
                VALUES (?, ?, ?, ?)
            """, (guild_id, channel_id, log_channel_id, support_channel_id))


def get_all_guild_configs():
    """Get all guild configurations."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM guild_config")
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# Global Settings Functions
# ============================================================================

def get_global_setting(key):
    """Get a global setting value."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM global_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            return row['value']
        return None


def set_global_setting(key, value):
    """Set a global setting value."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO global_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, str(value)))


# ============================================================================
# User Reactions Functions
# ============================================================================

def get_user_reactions(guild_id, user_id):
    """Get reaction count for a specific user in a guild."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT reaction_count FROM user_reactions 
            WHERE guild_id = ? AND user_id = ?
        """, (guild_id, user_id))
        row = cursor.fetchone()
        if row:
            return row['reaction_count']
        return 0


def increment_user_reactions(guild_id, user_id, count=1):
    """Increment reaction count for a user in a guild."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_reactions (guild_id, user_id, reaction_count, last_reaction_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(guild_id, user_id) 
            DO UPDATE SET 
                reaction_count = reaction_count + ?,
                last_reaction_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
        """, (guild_id, user_id, count, count))


def get_guild_reactions(guild_id):
    """Get all user reactions for a specific guild."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, reaction_count 
            FROM user_reactions 
            WHERE guild_id = ?
            ORDER BY reaction_count DESC
        """, (guild_id,))
        return {row['user_id']: row['reaction_count'] for row in cursor.fetchall()}


def get_all_reactions():
    """Get all user reactions grouped by guild."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT guild_id, user_id, reaction_count 
            FROM user_reactions
            ORDER BY guild_id, reaction_count DESC
        """)
        
        reactions = {}
        for row in cursor.fetchall():
            guild_id = str(row['guild_id'])
            user_id = str(row['user_id'])
            if guild_id not in reactions:
                reactions[guild_id] = {}
            reactions[guild_id][user_id] = row['reaction_count']
        
        return reactions


# ============================================================================
# Admin Users Functions
# ============================================================================

def is_admin_user(user_id):
    """Check if a user is an admin."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM admin_users WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None


def add_admin_user(user_id):
    """Add a user to the admin list."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO admin_users (user_id) VALUES (?)
            """, (user_id,))
            return True
        except sqlite3.IntegrityError:
            return False  # User already exists


def remove_admin_user(user_id):
    """Remove a user from the admin list."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM admin_users WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0


def get_admin_users():
    """Get list of all admin user IDs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM admin_users")
        return [row['user_id'] for row in cursor.fetchall()]


# ============================================================================
# Banned Users Functions
# ============================================================================

def is_banned_user(user_id):
    """Check if a user is banned."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None


def ban_user(user_id, reason=None, banned_by=None):
    """Ban a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO banned_users (user_id, reason, banned_by)
                VALUES (?, ?, ?)
            """, (user_id, reason, banned_by))
            return True
        except sqlite3.IntegrityError:
            return False  # User already banned


def unban_user(user_id):
    """Unban a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        return cursor.rowcount > 0


def get_banned_users():
    """Get all banned users."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM banned_users")
        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# Ticket Functions
# ============================================================================

def create_ticket(ticket_id, user_id, user_name, guild_id, guild_name, message):
    """Create a new support ticket."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tickets (
                ticket_id, user_id, user_name, guild_id, guild_name, message, status
            ) VALUES (?, ?, ?, ?, ?, ?, 'open')
        """, (ticket_id, user_id, user_name, guild_id, guild_name, message))
        return ticket_id


def get_ticket(ticket_id):
    """Get a specific ticket by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def update_ticket(ticket_id, **updates):
    """Update a ticket with new information."""
    if not updates:
        return False
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Build dynamic UPDATE query
        set_clauses = [f"{key} = ?" for key in updates.keys()]
        values = list(updates.values())
        values.append(ticket_id)
        
        cursor.execute(f"""
            UPDATE tickets 
            SET {', '.join(set_clauses)}
            WHERE ticket_id = ?
        """, values)
        
        return cursor.rowcount > 0


def close_ticket(ticket_id, closed_by="admin", admin_response=None, admin_responder=None):
    """Close a ticket."""
    updates = {
        "status": f"closed_by_{closed_by}",
        "closed_timestamp": datetime.now().isoformat(),
        "closed_by": closed_by
    }
    
    if admin_response:
        updates["admin_response"] = admin_response
    if admin_responder:
        updates["admin_responder"] = admin_responder
        updates["response_timestamp"] = datetime.now().isoformat()
    
    return update_ticket(ticket_id, **updates)


def delete_ticket(ticket_id):
    """Permanently delete a ticket."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,))
        return cursor.rowcount > 0


def get_user_tickets(user_id, status_filter=None):
    """Get all tickets for a specific user, optionally filtered by status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if status_filter:
            cursor.execute("""
                SELECT * FROM tickets 
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
            """, (user_id, status_filter))
        else:
            cursor.execute("""
                SELECT * FROM tickets 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
        
        return {row['ticket_id']: dict(row) for row in cursor.fetchall()}


def get_all_tickets(status_filter=None):
    """Get all tickets, optionally filtered by status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if status_filter:
            cursor.execute("""
                SELECT * FROM tickets 
                WHERE status = ?
                ORDER BY created_at DESC
            """, (status_filter,))
        else:
            cursor.execute("""
                SELECT * FROM tickets 
                ORDER BY created_at DESC
            """)
        
        return {row['ticket_id']: dict(row) for row in cursor.fetchall()}


def get_open_tickets():
    """Get all open tickets."""
    return get_all_tickets(status_filter="open")


def get_guild_tickets(guild_id, status_filter=None):
    """Get all tickets for a specific guild."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if status_filter:
            cursor.execute("""
                SELECT * FROM tickets 
                WHERE guild_id = ? AND status = ?
                ORDER BY created_at DESC
            """, (guild_id, status_filter))
        else:
            cursor.execute("""
                SELECT * FROM tickets 
                WHERE guild_id = ?
                ORDER BY created_at DESC
            """, (guild_id,))
        
        return {row['ticket_id']: dict(row) for row in cursor.fetchall()}
