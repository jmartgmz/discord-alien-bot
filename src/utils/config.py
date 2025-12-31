"""
Configuration management utilities for the UFO Sighting Bot.
"""
import json
import os

CONFIG_FILE = "data/config.json"
REACTIONS_FILE = "data/reactions.json"

def load_config():
    """Load server configuration from JSON file."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    """Save server configuration to JSON file."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def load_reactions():
    """Load reaction tracking data from JSON file."""
    if not os.path.exists(REACTIONS_FILE):
        return {}
    with open(REACTIONS_FILE, "r") as f:
        return json.load(f)

def save_reactions(data):
    """Save reaction tracking data to JSON file."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(REACTIONS_FILE), exist_ok=True)
    with open(REACTIONS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_global_log_channel_id():
    """Get the global logging channel ID that logs activity from all servers."""
    config = load_config()
    return config.get("global_log_channel_id")

def set_global_log_channel_id(channel_id):
    """Set the global logging channel ID for all servers."""
    config = load_config()
    config["global_log_channel_id"] = channel_id
    save_config(config)