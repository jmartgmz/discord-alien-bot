#!/usr/bin/env python3
"""
UFO Sighting Bot Launcher
Simple launcher script to run the bot from the project root.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the bot
if __name__ == "__main__":
    from ufo_main import bot, token
    if token is None:
        raise ValueError("DISCORD_TOKEN environment variable is not set")
    bot.run(token)