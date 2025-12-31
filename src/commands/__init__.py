"""
Commands package for the UFO Sighting Bot.
"""
from .admin import setup_admin_commands
from .sightings import setup_sightings_commands
from .setup import setup_setup_commands
from .help import setup_help_commands
from .support import setup_support_commands
from .alien import setup_alien_commands
from .ban import setup_ban_commands

def setup_all_commands(bot, bot_start_time):
    """Set up all command modules."""
    setup_admin_commands(bot, bot_start_time)
    setup_sightings_commands(bot)
    setup_setup_commands(bot)
    setup_help_commands(bot)
    setup_support_commands(bot)
    setup_alien_commands(bot)
    setup_ban_commands(bot)

__all__ = ['setup_all_commands']