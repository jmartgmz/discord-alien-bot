"""
Configuration management utilities for the UFO Sighting Bot.
Now using SQLite database instead of JSON files.
"""
from .database import (
    get_guild_config,
    set_guild_config,
    get_all_guild_configs,
    get_global_setting,
    set_global_setting,
    get_user_reactions,
    increment_user_reactions,
    get_guild_reactions,
    get_all_reactions
)

# ============================================================================
# Configuration Functions
# ============================================================================

def load_config():
    """
    Load server configuration from database.
    Returns a dict compatible with old JSON format for backward compatibility.
    """
    configs = {}
    
    # Get global log channel
    global_log = get_global_setting("global_log_channel_id")
    if global_log:
        configs["global_log_channel_id"] = int(global_log)
    
    # Get all guild configs
    guild_configs = get_all_guild_configs()
    for guild_config in guild_configs:
        guild_id = str(guild_config['guild_id'])
        
        # If only channel_id is set, use simple format
        if guild_config['channel_id'] and not guild_config['log_channel_id'] and not guild_config['support_channel_id']:
            configs[guild_id] = guild_config['channel_id']
        else:
            # Use dict format for multiple channels
            config_dict = {}
            if guild_config['channel_id']:
                config_dict['channel_id'] = guild_config['channel_id']
            if guild_config['log_channel_id']:
                config_dict['log_channel_id'] = guild_config['log_channel_id']
            if guild_config['support_channel_id']:
                config_dict['support_channel_id'] = guild_config['support_channel_id']
            if config_dict:
                configs[guild_id] = config_dict
    
    return configs


def save_config(config):
    """
    Save server configuration to database.
    Accepts old JSON format dict for backward compatibility.
    """
    # Save global log channel if present
    if "global_log_channel_id" in config:
        set_global_setting("global_log_channel_id", config["global_log_channel_id"])
    
    # Save guild configs
    for guild_id, value in config.items():
        if guild_id == "global_log_channel_id":
            continue
        
        guild_id = int(guild_id)
        
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


# ============================================================================
# Reactions Functions
# ============================================================================

def load_reactions():
    """
    Load reaction tracking data from database.
    Returns dict compatible with old JSON format.
    """
    return get_all_reactions()


def save_reactions(data):
    """
    Save reaction tracking data to database.
    Accepts old JSON format dict for backward compatibility.
    Note: This rebuilds the entire reactions table. For incremental updates,
    use increment_user_reactions() directly.
    """
    # This is kept for backward compatibility but is less efficient
    # It's better to use increment_user_reactions() directly
    for guild_id, users in data.items():
        for user_id, count in users.items():
            # This will set the count to the exact value
            current_count = get_user_reactions(int(guild_id), int(user_id))
            diff = count - current_count
            if diff != 0:
                increment_user_reactions(int(guild_id), int(user_id), diff)


# ============================================================================
# Global Settings Functions
# ============================================================================

def get_global_log_channel_id():
    """Get the global logging channel ID that logs activity from all servers."""
    result = get_global_setting("global_log_channel_id")
    return int(result) if result else None


def set_global_log_channel_id(channel_id):
    """Set the global logging channel ID for all servers."""
    set_global_setting("global_log_channel_id", channel_id)