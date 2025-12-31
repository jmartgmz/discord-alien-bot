#!/usr/bin/env python3
"""
Migration script to convert JSON data files to SQLite database.
Run this script once to migrate your existing data.

Usage: python migrate_to_sqlite.py
"""
import json
import os
import sys
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from threading import Lock

# Database file path
DB_FILE = "data/ufo_bot.db"
db_lock = Lock()

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    with db_lock:
        os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

def init_database():
    """Initialize the database schema."""
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

def set_guild_config(guild_id, channel_id=None, log_channel_id=None, support_channel_id=None):
    """Set or update guild configuration."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO guild_config (guild_id, channel_id, log_channel_id, support_channel_id, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (guild_id, channel_id, log_channel_id, support_channel_id))

def set_global_setting(key, value):
    """Set a global setting."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO global_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, str(value)))

def add_user_reaction(guild_id, user_id, count):
    """Add user reactions."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_reactions (guild_id, user_id, reaction_count, last_reaction_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (guild_id, user_id, count))

def add_admin_user(user_id):
    """Add admin user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO admin_users (user_id) VALUES (?)", (user_id,))
            return True
        except sqlite3.IntegrityError:
            return False

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
            return False

def create_ticket(ticket_id, user_id, user_name, guild_id, guild_name, message):
    """Create a ticket."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tickets (ticket_id, user_id, user_name, guild_id, guild_name, message, status)
            VALUES (?, ?, ?, ?, ?, ?, 'open')
        """, (ticket_id, user_id, user_name, guild_id, guild_name, message))

def update_ticket(ticket_id, **updates):
    """Update a ticket."""
    if not updates:
        return False
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        set_clauses = [f"{key} = ?" for key in updates.keys()]
        values = list(updates.values())
        values.append(ticket_id)
        
        cursor.execute(f"""
            UPDATE tickets 
            SET {', '.join(set_clauses)}
            WHERE ticket_id = ?
        """, values)
        
        return cursor.rowcount > 0

# JSON file paths
CONFIG_FILE = "data/config.json"
REACTIONS_FILE = "data/reactions.json"
AUTH_FILE = "data/authorized_users.json"
BANNED_FILE = "data/banned.json"
TICKETS_FILE = "data/tickets.json"


def load_json(filepath):
    """Load JSON file, return empty dict if file doesn't exist."""
    if not os.path.exists(filepath):
        print(f"⚠️  {filepath} not found, skipping...")
        return {}
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error loading {filepath}: {e}")
        return {}


def migrate_config():
    """Migrate config.json to database."""
    print("\n📋 Migrating configuration...")
    config = load_json(CONFIG_FILE)
    
    if not config:
        print("  No config data to migrate")
        return
    
    # Migrate global log channel
    if "global_log_channel_id" in config:
        set_global_setting("global_log_channel_id", config["global_log_channel_id"])
        print(f"  ✓ Global log channel: {config['global_log_channel_id']}")
    
    # Migrate guild configs
    guild_count = 0
    for key, value in config.items():
        if key == "global_log_channel_id":
            continue
        
        guild_id = int(key)
        
        if isinstance(value, dict):
            # New format with multiple channels
            set_guild_config(
                guild_id,
                channel_id=value.get("channel_id"),
                log_channel_id=value.get("log_channel_id"),
                support_channel_id=value.get("support_channel_id")
            )
        else:
            # Old format with single channel
            set_guild_config(guild_id, channel_id=value)
        
        guild_count += 1
    
    print(f"  ✓ Migrated {guild_count} guild configurations")


def migrate_reactions():
    """Migrate reactions.json to database."""
    print("\n⭐ Migrating user reactions...")
    reactions = load_json(REACTIONS_FILE)
    
    if not reactions:
        print("  No reaction data to migrate")
        return
    
    total_entries = 0
    for guild_id, users in reactions.items():
        for user_id, count in users.items():
            add_user_reaction(int(guild_id), int(user_id), count)
            total_entries += 1
    
    print(f"  ✓ Migrated {total_entries} reaction entries across {len(reactions)} guilds")


def migrate_authorized_users():
    """Migrate authorized_users.json to database."""
    print("\n👥 Migrating admin users...")
    auth_data = load_json(AUTH_FILE)
    
    if not auth_data or "admin_users" not in auth_data:
        print("  No admin users to migrate")
        return
    
    admin_count = 0
    for user_id in auth_data["admin_users"]:
        if add_admin_user(user_id):
            admin_count += 1
    
    print(f"  ✓ Migrated {admin_count} admin users")


def migrate_banned_users():
    """Migrate banned.json to database."""
    print("\n🚫 Migrating banned users...")
    banned_data = load_json(BANNED_FILE)
    
    if not banned_data or "banned_users" not in banned_data:
        print("  No banned users to migrate")
        return
    
    banned_count = 0
    for user_id, details in banned_data["banned_users"].items():
        if isinstance(details, dict):
            ban_user(
                int(user_id),
                reason=details.get("reason"),
                banned_by=details.get("banned_by")
            )
        else:
            ban_user(int(user_id))
        banned_count += 1
    
    print(f"  ✓ Migrated {banned_count} banned users")


def migrate_tickets():
    """Migrate tickets.json to database."""
    print("\n🎫 Migrating support tickets...")
    tickets = load_json(TICKETS_FILE)
    
    if not tickets:
        print("  No tickets to migrate")
        return
    
    ticket_count = 0
    for ticket_id, ticket_data in tickets.items():
        # Create the ticket with basic info
        create_ticket(
            ticket_id=ticket_id,
            user_id=ticket_data["user_id"],
            user_name=ticket_data["user_name"],
            guild_id=ticket_data["guild_id"],
            guild_name=ticket_data["guild_name"],
            message=ticket_data["message"]
        )
        
        # Update with additional fields if they exist
        updates = {}
        
        if "status" in ticket_data:
            updates["status"] = ticket_data["status"]
        
        # Handle timestamp vs created_at
        if "created_at" in ticket_data:
            updates["created_at"] = ticket_data["created_at"]
        elif "timestamp" in ticket_data:
            updates["created_at"] = ticket_data["timestamp"]
        
        if "admin_response" in ticket_data:
            updates["admin_response"] = ticket_data["admin_response"]
        
        if "admin_responder" in ticket_data:
            updates["admin_responder"] = ticket_data["admin_responder"]
        
        if "response_timestamp" in ticket_data:
            updates["response_timestamp"] = ticket_data["response_timestamp"]
        
        if "closed_by" in ticket_data:
            updates["closed_by"] = ticket_data["closed_by"]
        
        if "closed_timestamp" in ticket_data:
            updates["closed_timestamp"] = ticket_data["closed_timestamp"]
        
        if updates:
            update_ticket(ticket_id, **updates)
        
        ticket_count += 1
    
    print(f"  ✓ Migrated {ticket_count} tickets")


def backup_json_files():
    """Create backups of JSON files before migration."""
    print("\n💾 Creating backup of JSON files...")
    backup_dir = "data/json_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(backup_dir, exist_ok=True)
    
    files_backed_up = 0
    for filepath in [CONFIG_FILE, REACTIONS_FILE, AUTH_FILE, BANNED_FILE, TICKETS_FILE]:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            backup_path = os.path.join(backup_dir, filename)
            with open(filepath, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            files_backed_up += 1
    
    print(f"  ✓ Backed up {files_backed_up} files to {backup_dir}")
    return backup_dir


def main():
    """Run the migration process."""
    print("=" * 70)
    print("🛸 UFO Bot - JSON to SQLite Migration Script")
    print("=" * 70)
    
    # Check if database already exists
    if os.path.exists("data/ufo_bot.db"):
        response = input("\n⚠️  Database already exists. Overwrite? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return
        print("\n🗑️  Removing existing database...")
        os.remove("data/ufo_bot.db")
    
    # Create backup
    backup_dir = backup_json_files()
    
    # Initialize database
    print("\n🔧 Initializing database schema...")
    init_database()
    print("  ✓ Database schema created")
    
    # Run migrations
    migrate_config()
    migrate_reactions()
    migrate_authorized_users()
    migrate_banned_users()
    migrate_tickets()
    
    print("\n" + "=" * 70)
    print("✅ Migration completed successfully!")
    print("=" * 70)
    print(f"\n📦 Original JSON files backed up to: {backup_dir}")
    print("🗄️  SQLite database created at: data/ufo_bot.db")
    print("\nNext steps:")
    print("  1. Test the bot to ensure everything works correctly")
    print("  2. If all is well, you can remove the JSON backup files")
    print("  3. Update your bot to use the new database functions")
    print("\n⚠️  Note: The bot code has been updated to use SQLite.")
    print("   JSON files are no longer used but kept as backup.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
