"""
UFO Sighting Bot - Main bot file.
A Discord bot that sends random UFO images and tracks user reactions.
"""
import discord
from discord.ext import commands
import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Import our custom modules
from utils import load_config, load_reactions, save_reactions, get_random_image, get_random_interval, get_global_log_channel_id, create_welcome_embed
from utils.helpers import get_random_image_with_effect, is_user_banned
from utils.database import init_database
from commands import setup_all_commands

# Load environment variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Bot start time for uptime tracking
bot_start_time = datetime.now()

# Duplicate reaction prevention - track recent reactions
recent_reactions = {}  # Format: {(user_id, message_id, emoji): timestamp}

# Track bot's UFO messages (message_id -> guild_id) for reaction tracking
# We keep messages in memory for 60 seconds after deletion to handle late reactions
bot_ufo_messages = {}

async def log_image_sent(channel, message, image_url):
    """Log when the bot sends a UFO image to the global logging channel."""
    global_log_channel_id = get_global_log_channel_id()
    if not global_log_channel_id:
        return
    
    global_log_channel = bot.get_channel(global_log_channel_id)
    if not global_log_channel or not isinstance(global_log_channel, discord.TextChannel):
        return
    
    try:
        # Create embed for image sent log
        log_embed = discord.Embed(
            title="🛸 UFO Image Sent",
            description=f"Bot sent a UFO image to track alien sightings",
            color=0x9370DB,  # Purple color for image sent logs
            timestamp=datetime.now()
        )
        
        log_embed.add_field(
            name="📺 Channel",
            value=f"{channel.mention} (`{channel.name}`)",
            inline=True
        )
        
        log_embed.add_field(
            name="🏛️ Server",
            value=f"**{channel.guild.name}**\n`{channel.guild.id}`",
            inline=True
        )
        
        log_embed.add_field(
            name="🔗 Message ID",
            value=f"`{message.id}`",
            inline=True
        )
        
        log_embed.add_field(
            name="🖼️ Image URL",
            value=f"[View Image]({image_url})",
            inline=False
        )
        
        log_embed.set_footer(text="UFO Image Deployment System")
        log_embed.set_thumbnail(url=image_url)  # Show the image as thumbnail
        
        await global_log_channel.send(embed=log_embed)
        logging.info(f"   📡 Image send logged to global channel")
        
    except Exception as e:
        logging.error(f"Failed to log image send to global channel: {e}")

# --- Independent image loop per guild ---
async def send_images_to_guild(guild_id: str):
    """Send UFO images to a specific guild at random intervals."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        config = load_config()
        if guild_id not in config:
            await asyncio.sleep(30)  # check again later
            continue

        # Handle both old format (integer) and new format (dictionary)
        guild_config = config[guild_id]
        if isinstance(guild_config, dict):
            channel_id = guild_config.get("channel_id")
        else:
            # Old format - guild_config is just the channel ID integer
            channel_id = guild_config
            
        if channel_id is None:
            await asyncio.sleep(30)
            continue

        channel = bot.get_channel(channel_id)
        if channel is None:
            await asyncio.sleep(30)
            continue

        # Wait for random interval before sending first image
        interval = get_random_interval()
        await asyncio.sleep(interval)

        # Get image with random effect applied
        image_content = await get_random_image_with_effect()
        try:
            # Ensure channel is a text channel that can send messages
            if not isinstance(channel, discord.TextChannel):
                continue
            
            # Send either URL string or Discord File
            if isinstance(image_content, str):
                message = await channel.send(image_content)
                image_url = image_content
            else:  # Discord File object
                message = await channel.send(file=image_content)
                image_url = f"[Processed UFO Image with effects]"
            
            # Track this message ID so we know it's from the bot even after deletion
            bot_ufo_messages[message.id] = guild_id
            logging.info(f"📤 Sent UFO image in guild {guild_id}, message ID: {message.id} - now tracking for reactions")
            
            # Log image sending to global channel
            await log_image_sent(channel, message, image_url)
            
            await message.add_reaction("👽")
            logging.info(f"🤖 Bot added 👽 reaction to UFO message {message.id}")
            await asyncio.sleep(4)  # how long the image stays
            await message.delete()
            logging.info(f"🗑️ UFO message {message.id} deleted after 4 seconds")
            
            # Keep message ID in memory for 60 more seconds to catch late reactions
            await asyncio.sleep(60)
            if message.id in bot_ufo_messages:
                del bot_ufo_messages[message.id]
                logging.info(f"🧹 Cleaned up message ID {message.id} from tracking after 60s")
        except discord.HTTPException as e:
            logging.error(f"⚠️ Failed in guild {guild_id}: {e}")

        # Each guild gets its own random interval
        interval = get_random_interval()
        await asyncio.sleep(interval)

@bot.event
async def on_ready():
    """Called when the bot is ready."""
    # Initialize database
    try:
        init_database()
        logging.info("✅ Database initialized")
    except Exception as e:
        logging.error(f"❌ Database initialization failed: {e}")
    
    if bot.user:
        logging.info(f"🤖 Bot is online as {bot.user.name}")
    else:
        logging.info("🤖 Bot is online")
    
    # Start web dashboard
    try:
        from utils.dashboard import start_dashboard_thread
        port = int(os.getenv('DASHBOARD_PORT', '5000'))
        start_dashboard_thread(bot, bot_start_time, port=port)
    except Exception as e:
        logging.error(f"⚠️ Failed to start dashboard: {e}")
    
    # Set bot status to DND and activity to "watching for ufos"
    activity = discord.Activity(type=discord.ActivityType.watching, name="Watching for Aliens")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)
    
    try:
        synced = await bot.tree.sync()
        logging.info(f"Slash commands synced: {len(synced)} commands")
        for cmd in synced:
            logging.info(f"  - /{cmd.name}: {cmd.description}")
    except Exception as e:
        logging.error(f"Failed to sync commands: {e}")

    # Start a separate task for each guild
    for g in bot.guilds:
        bot.loop.create_task(send_images_to_guild(str(g.id)))

@bot.event
async def on_guild_join(guild):
    """Send welcome message when bot joins a new server."""
    logging.info(f"🌟 Joined new guild: {guild.name} (ID: {guild.id})")
    
    # Create welcome embed
    welcome_embed = create_welcome_embed()
    
    # Try to find a suitable channel to send the welcome message
    # Priority: general > announcements > bot-commands > first text channel with permissions
    target_channel = None
    
    # Try common channel names first
    for channel in guild.text_channels:
        if channel.name.lower() in ['general', 'announcements', 'bot-commands', 'welcome']:
            if channel.permissions_for(guild.me).send_messages:
                target_channel = channel
                break
    
    # If no common channel found, use the first text channel we can send to
    if not target_channel:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                target_channel = channel
                break
    
    # If we found a suitable channel, send the welcome message
    if target_channel:
        try:
            await target_channel.send(embed=welcome_embed)
            logging.info(f"✅ Sent welcome message to {guild.name} in #{target_channel.name}")
        except discord.HTTPException as e:
            logging.error(f"❌ Failed to send welcome message to {guild.name}: {e}")
    else:
        logging.warning(f"⚠️ No suitable channel found in {guild.name} to send welcome message")

@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    """Handle reaction tracking for UFO sightings."""
    # Debug logging
    logging.info(f"🔍 Reaction detected: {payload.emoji} by user {payload.user_id} on message {payload.message_id}")
    
    # Check if user is banned from using the bot
    if is_user_banned(payload.user_id):
        logging.warning(f"🚫 Banned user {payload.user_id} attempted to react - ignoring")
        return
    
    # Accept any emoji, not just alien emoji (this was the bug!)
    # Original code only tracked 👽 but users react with any emoji
    # if str(payload.emoji) != "👽":
    #     return
    
    if bot.user and payload.user_id == bot.user.id:
        logging.info(f"⏭️ Skipping bot's own reaction")
        return

    # Prevent duplicate reactions within 5 seconds
    import time
    global recent_reactions
    current_time = time.time()
    reaction_key = (payload.user_id, payload.message_id, str(payload.emoji))
    
    if reaction_key in recent_reactions:
        time_diff = current_time - recent_reactions[reaction_key]
        if time_diff < 5:  # 5 second window
            logging.info(f"🔄 Duplicate reaction detected (within {time_diff:.1f}s) - skipping")
            return
    
    # Record this reaction
    recent_reactions[reaction_key] = current_time
    
    # Clean up old entries (older than 10 seconds)
    cutoff_time = current_time - 10
    recent_reactions = {k: v for k, v in recent_reactions.items() if v > cutoff_time}

    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        logging.error(f"❌ Channel {payload.channel_id} not found")
        return

    # Check if this message is in our tracked UFO messages (even if deleted)
    is_bot_ufo_message = payload.message_id in bot_ufo_messages
    
    if is_bot_ufo_message:
        # This is definitely one of our UFO messages (even if deleted now)
        logging.info(f"✅ Reaction to tracked UFO message {payload.message_id} (deleted: likely)")
    else:
        # Try to fetch the message to verify it's from the bot
        try:
            if not isinstance(channel, discord.TextChannel):
                return
            message = await channel.fetch_message(payload.message_id)
            if bot.user and message.author.id != bot.user.id:
                logging.info(f"⏭️ Skipping reaction to non-bot message from {message.author.id}")
                return
            print(f"✅ Found message from bot, content: {message.content[:50]}...")
        except discord.NotFound:
            # Message was deleted and we don't have it tracked - skip it
            print(f"⏭️ Skipping reaction to deleted untracked message {payload.message_id}")
            return
        except Exception as e:
            print(f"❌ Could not fetch message {payload.message_id}: {e}")
            return

    user_id = str(payload.user_id)
    guild_id = str(payload.guild_id) if payload.guild_id else "dm"

    # Load current reactions data from file
    reactions_data = load_reactions()
    if guild_id not in reactions_data:
        reactions_data[guild_id] = {}
    
    # Check current count before incrementing
    current_count = reactions_data[guild_id].get(user_id, 0)
    print(f"📊 User {user_id} current count: {current_count} -> {current_count + 1}")
    
    if user_id not in reactions_data[guild_id]:
        reactions_data[guild_id][user_id] = 0

    reactions_data[guild_id][user_id] += 1
    # Save updated data back to file
    save_reactions(reactions_data)
    
    # Console log with more detail
    print(f"👽 SIGHTING TRACKED! Reaction by {user_id} in guild {guild_id}. Total: {reactions_data[guild_id][user_id]}")
    print(f"   Emoji: {payload.emoji}, Message ID: {payload.message_id}")
    
    # Create log embed (used for both per-server and global logging)
    if payload.guild_id:  # Only for guild messages, not DMs
        # Get user and guild info for better logging
        user = bot.get_user(payload.user_id)
        guild = bot.get_guild(payload.guild_id)
        
        user_name = user.display_name if user else f"User {payload.user_id}"
        guild_name = guild.name if guild else f"Guild {payload.guild_id}"
        
        log_embed = discord.Embed(
            title="👽 UFO Sighting Logged",
            color=0x00ff41,
            timestamp=datetime.now()
        )
        
        log_embed.add_field(
            name="👤 User",
            value=f"**{user_name}**\n`{payload.user_id}`",
            inline=True
        )
        
        log_embed.add_field(
            name="🏛️ Server", 
            value=f"**{guild_name}**\n`{payload.guild_id}`",
            inline=True
        )
        
        log_embed.add_field(
            name="📊 Total Count",
            value=f"**{reactions_data[guild_id][user_id]}** sightings",
            inline=True
        )
        
        log_embed.add_field(
            name="📍 Channel",
            value=f"<#{payload.channel_id}>",
            inline=False
        )
        
        log_embed.add_field(
            name="😀 Emoji Used",
            value=f"{payload.emoji}",
            inline=True
        )
        
        log_embed.set_footer(text="UFO Reaction Tracking System")
        
        # Send to global logging channel if configured (logs all servers)
        global_log_channel_id = get_global_log_channel_id()
        if global_log_channel_id:
            global_log_channel = bot.get_channel(global_log_channel_id)
            if global_log_channel and isinstance(global_log_channel, discord.TextChannel):
                try:
                    await global_log_channel.send(embed=log_embed)
                    print(f"   ✅ Logged to global channel")
                except Exception as e:
                    print(f"Failed to send log to global log channel: {e}")

# Set up all command modules
setup_all_commands(bot, bot_start_time)

if __name__ == "__main__":
    if token is None:
        raise ValueError("DISCORD_TOKEN environment variable is not set")
    bot.run(token)