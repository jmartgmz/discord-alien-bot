"""
Helper utilities and constants for the UFO Sighting Bot.
"""
import random
import discord
import io
import aiohttp
import json
import os
import logging
from PIL import Image, ImageOps, ImageEnhance
from datetime import datetime

# UFO image URLs
IMAGE_URLS = [
    "https://s.hdnux.com/photos/01/25/20/06/22348185/4/rawImage.jpg",
    "https://brobible.com/wp-content/uploads/2023/08/ufo-over-city-clouds.png",
    "https://api.time.com/wp-content/uploads/2016/02/150222-ufo-sightings-06.jpg",
    "https://www.washingtonpost.com/news/morning-mix/wp-content/uploads/sites/21/2015/01/UFO-04-1024x666.jpg",
    "https://hips.hearstapps.com/hmg-prod/images/vintage-old-black-and-white-ufo-photo-royalty-free-image-1677115000.jpg?resize=1200:*",
    "https://assets.newsweek.com/wp-content/uploads/2025/08/2097556-ufo-calvine-photo.jpg",
    "https://platform.vox.com/wp-content/uploads/sites/2/chorus/uploads/chorus_asset/file/25440927/GettyImages_875509_001.jpg?quality=90&strip=all&crop=0.078124999999993%2C0%2C99.84375%2C100&w=750",
    "https://cdn.britannica.com/57/200357-050-EC210F98/Ufo-alien-space-trees.jpg?w=300",

]

# Image effects that can be applied randomly
IMAGE_EFFECTS = [""
    "normal",      # 60% chance - no effect (most common)
    "normal",
    "normal", 
    "normal",
    "normal",
    "normal",
    "invert",      # 15% chance - invert colors
    "invert",
    "greenscale",  # 10% chance - green tint (alien theme) - reduced frequency
    "vintage",     # 10% chance - sepia/vintage look
    "enhanced"     # 5% chance - enhanced contrast/brightness
]

# Random intervals for image posting (in seconds) - Ultra-rare encounters
INTERVALS = [2.5 * 60 * 60, 3 * 60 * 60, 3.5 * 60 * 60, 4 * 60 * 60]  # 2.5h, 3h, 3.5h, 4h

async def apply_image_effect(image_url, effect):
    """Apply visual effects to UFO images for enhanced alien atmosphere."""
    if effect == "normal":
        return image_url
    
    try:
        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status != 200:
                    return image_url  # Return original URL if download fails
                
                image_data = await response.read()
        
        # Process the image with PIL
        with Image.open(io.BytesIO(image_data)) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Apply the selected effect
            if effect == "invert":
                img = ImageOps.invert(img)
            elif effect == "greenscale":
                # Convert to grayscale then tint green (alien theme)
                img = ImageOps.grayscale(img)
                img = img.convert('RGB')
                # Apply green tint
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(0.3)  # Reduce saturation
                # Add green overlay
                green_overlay = Image.new('RGB', img.size, (0, 255, 0))
                img = Image.blend(img, green_overlay, 0.2)
            elif effect == "vintage":
                # Sepia/vintage effect
                img = ImageOps.grayscale(img)
                img = img.convert('RGB')
                # Apply sepia tint
                sepia_overlay = Image.new('RGB', img.size, (255, 218, 185))
                img = Image.blend(img, sepia_overlay, 0.3)
            elif effect == "enhanced":
                # Enhance contrast and brightness
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.2)
            
            # Save processed image to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG', quality=95)
            img_bytes.seek(0)
            
            # Return the processed image as Discord file
            return discord.File(img_bytes, filename=f"ufo_{effect}.png")
            
    except Exception as e:
        logging.error(f"⚠️ Failed to apply image effect '{effect}': {e}")
        return image_url  # Return original URL if processing fails

async def get_random_image_with_effect():
    """Get a random UFO image with a randomly applied effect."""
    base_url = random.choice(IMAGE_URLS)
    effect = random.choice(IMAGE_EFFECTS)
    
    logging.info(f"🎨 Applying effect '{effect}' to UFO image")
    
    # Apply effect and return either URL or Discord File
    return await apply_image_effect(base_url, effect)

def get_random_image():
    """Get a random UFO image URL (legacy function for compatibility)."""
    return random.choice(IMAGE_URLS)

def get_random_interval():
    """Get a random interval for image posting."""
    return random.choice(INTERVALS)

def format_uptime(uptime_delta):
    """Format a timedelta object into a readable uptime string."""
    days = uptime_delta.days
    hours = uptime_delta.seconds // 3600
    minutes = (uptime_delta.seconds // 60) % 60
    seconds = uptime_delta.seconds % 60
    return f"{days}d {hours}h {minutes}m {seconds}s"

def create_welcome_embed():
    """Create the welcome message embed for new servers."""
    embed = discord.Embed(
        title="🛸 Welcome to UFO Sighting Bot!",
        description="Thanks for adding me to your server! Let's get you set up to start tracking alien encounters.",
        color=0x00ff41,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="🚀 Quick Setup",
        value="To get started, an admin needs to run `/setchannel` in the channel where you want UFO images to appear.",
        inline=False
    )
    
    embed.add_field(
        name="📋 What I Do",
        value="• Send random UFO images at random intervals\n"
              "• Track any emoji reactions as \"sightings\"\n"
              "• Provide leaderboards for top alien spotters\n"
              "• Offer admin tools for bot management",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Essential Commands",
        value="**Setup:**\n"
              "`/setchannel` - Set the UFO images channel\n"
              "`/help` - View all available commands\n\n"
              "**For Users:**\n"
              "`/localsightings` - Server leaderboard\n"
              "`/globalsightings` - Global leaderboard\n"
              "`/support` - Get help or report issues",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ Admin Features",
        value="Admins can access additional commands like `/botinfo`, `/setlogchannel`, and more. Use `/helpadmin` to see all admin commands.",
        inline=False
    )
    
    embed.add_field(
        name="🎯 How It Works",
        value="1. Set a channel with `/setchannel`\n"
              "2. I'll start posting UFO images randomly\n"
              "3. Users react with any emoji to log sightings\n"
              "4. Check leaderboards to see top spotters!",
        inline=False
    )
    
    embed.set_footer(
        text="Need help? Use /support or /help • Ready to start? Use /setchannel!",
        icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png"  # UFO emoji if available
    )
    
    return embed

# Ban System Functions - Now using SQLite database
from .database import (
    is_banned_user as db_is_banned_user,
    ban_user as db_ban_user,
    unban_user as db_unban_user,
    get_banned_users as db_get_banned_users
)

def load_banned_users():
    """
    Load banned users from database.
    Returns dict compatible with old JSON format for backward compatibility.
    """
    banned_list = db_get_banned_users()
    result = {}
    for user_info in banned_list:
        result[str(user_info['user_id'])] = {
            "reason": user_info.get('reason', 'No reason provided'),
            "banned_at": user_info.get('banned_at', ''),
            "banned_by": str(user_info.get('banned_by', 'Unknown'))
        }
    return result

def save_banned_users(banned_users):
    """
    Save banned users to database.
    Accepts old JSON format dict for backward compatibility.
    Note: This is not recommended - use ban_user/unban_user instead.
    """
    # This is kept for backward compatibility but is not efficient
    # It's better to use ban_user/unban_user directly
    pass  # Database operations are atomic, no bulk save needed

def is_user_banned(user_id):
    """Check if a user is banned."""
    return db_is_banned_user(user_id)

def ban_user(user_id, reason="No reason provided", banned_by=None):
    """Ban a user with reason and timestamp."""
    return db_ban_user(user_id, reason, banned_by)

def unban_user(user_id):
    """Unban a user."""
    return db_unban_user(user_id)

def get_ban_info(user_id):
    """Get ban information for a user."""
    banned_users = load_banned_users()
    return banned_users.get(str(user_id), None)