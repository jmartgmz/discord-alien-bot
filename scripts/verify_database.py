#!/usr/bin/env python3
"""
Quick verification script to check SQLite migration was successful.
"""
import sqlite3
import os

DB_FILE = "data/ufo_bot.db"

def verify_database():
    """Verify the database and migration."""
    if not os.path.exists(DB_FILE):
        print("❌ Database file not found at:", DB_FILE)
        return False
    
    print("=" * 70)
    print("🔍 SQLite Database Verification")
    print("=" * 70)
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['guild_config', 'global_settings', 'user_reactions', 
                          'admin_users', 'banned_users', 'tickets']
        
        print("\n📊 Tables:")
        for table in expected_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - MISSING!")
        
        # Count records
        print("\n📈 Record Counts:")
        
        cursor.execute("SELECT COUNT(*) FROM guild_config")
        print(f"  • Guild configs: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM global_settings")
        print(f"  • Global settings: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM user_reactions")
        print(f"  • User reactions: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM admin_users")
        print(f"  • Admin users: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM banned_users")
        print(f"  • Banned users: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM tickets")
        print(f"  • Tickets: {cursor.fetchone()[0]}")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        print(f"\n🔍 Indexes: {len(indexes)} indexes created")
        for idx in indexes:
            if not idx.startswith('sqlite_'):  # Skip auto-generated indexes
                print(f"  • {idx}")
        
        # Sample data verification
        print("\n🔬 Sample Data:")
        
        cursor.execute("SELECT * FROM admin_users LIMIT 3")
        admins = cursor.fetchall()
        if admins:
            print(f"  • Admin users: {len(admins)} found")
        
        cursor.execute("SELECT ticket_id, status FROM tickets LIMIT 3")
        tickets = cursor.fetchall()
        if tickets:
            print(f"  • Sample tickets:")
            for ticket_id, status in tickets:
                print(f"    - {ticket_id}: {status}")
        
        # Check global settings
        cursor.execute("SELECT key, value FROM global_settings")
        settings = cursor.fetchall()
        if settings:
            print(f"  • Global settings:")
            for key, value in settings:
                print(f"    - {key}: {value}")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ Database verification PASSED!")
        print("=" * 70)
        print("\nYour database is ready to use! The bot should work correctly.")
        print("Next step: Run 'python3 run_bot.py' to test the bot.\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_database()
