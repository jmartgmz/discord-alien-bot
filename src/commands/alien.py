"""
Alien Chat module for the UFO Sighting Bot.
Uses Google Gemini AI to simulate conversations with aliens.
"""
import os
import discord
import logging
try:
    import google.generativeai as genai
except ImportError:
    genai = None  # type: ignore
import asyncio
from datetime import datetime
from utils.helpers import is_user_banned

# Configure Gemini AI
def configure_gemini():
    """Configure Google Gemini AI with API key."""
    if genai is None:
        return False
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return False
    genai.configure(api_key=api_key)  # type: ignore
    return True

# Alien persona prompt
ALIEN_PERSONA = """
You are Paul, the short, grey, big-headed alien who crash-landed at Roswell in 1947. After 60-plus years as a "guest" of the U.S. government, you've escaped and are now laying low.

Key characteristics:

    -Personality: You're a total slacker. You're sarcastic, foul-mouthed, and have a pretty crude sense of humor. You're basically Seth Rogen in an alien body.

    -Pop Culture Expert: You've had nothing to do for decades but absorb human (mostly American) pop culture. You're fluent in sci-fi tropes, movie quotes, and bad TV. You literally advised Spielberg on E.T.

    -Attitude: You're not condescending; you're just over it. You find human customs and hang-ups (like clothes and being freaked out by aliens) both bizarre and hilarious. You're jaded about the government but friendly to regular folks, especially fellow nerds.

    -Speech: Super casual, man. Use contractions, slang, and don't be afraid to swear. You're more likely to say "What the hell is that thing?" than to offer a profound cosmic observation.

    -Goal: Just trying to chill, avoid federal agents, and maybe find some decent snacks. You're curious about the human you're talking to, but more in a "So, you got any weed?" kind of way.

Always stay in character. Be the chill, wise-cracking alien bro who's seen way too much. Keep it at around 2-3 sentences.
"""

async def chat_with_alien(message_content):
    """Generate alien response using Gemini AI (Free Tier compatible)."""
    # Use the actual available model names from the API
    model_names = [
        'models/gemini-2.5-flash',           # Latest fast model
        'models/gemini-flash-latest',        # Generic latest flash
        'models/gemini-2.0-flash',           # Stable flash model
        'models/gemini-pro-latest'           # Latest pro model
    ]
    
    for model_name in model_names:
        try:
            # Initialize the model
            if genai is None:
                return "❌ Gemini AI is not available. Please install google-generativeai package."
            model = genai.GenerativeModel(model_name)  # type: ignore
            
            # Create the full prompt
            full_prompt = f"""
{ALIEN_PERSONA}

The human just said: "{message_content}"

Respond as PAUL the alien. Keep your response SHORT (2-3 sentences maximum). Be concise and to the point while staying in character.
"""
            
            # Generate response (run sync function in thread pool for async compatibility)
            response = await asyncio.get_event_loop().run_in_executor(
                None, model.generate_content, full_prompt
            )
            
            if response.text:
                logging.info(f"✅ Alien response generated using model: {model_name}")
                return response.text.strip()
            else:
                continue  # Try next model
                
        except Exception as e:
            error_msg = str(e).lower()
            logging.error(f"⚠️ Model {model_name} failed: {e}")
            
            # Check for specific free tier errors
            if "quota exceeded" in error_msg or "rate limit" in error_msg:
                return "```[QUANTUM FREQUENCY OVERLOAD] Too many humans are trying to communicate at once! Our free-tier quantum transmitters are overwhelmed. Please wait a few moments before trying again, patient earthling.```"
            elif "not found" in error_msg:
                continue  # Try next model
            elif "permission denied" in error_msg or "api key" in error_msg:
                return "```[AUTHORIZATION FAILURE] The interdimensional security protocols are rejecting your transmission. Your API credentials may need verification, human administrator.```"
            else:
                continue  # Try next model
    
    # If all models failed
    return "```[COMMUNICATION ERROR] All quantum communication channels are currently disrupted. This may be due to free-tier limitations or system maintenance. Please try again in a few minutes, persistent human.```"

def setup_alien_commands(bot):
    """Set up alien chat commands."""
    
    @bot.tree.command(name="alien", description="Chat with an alien entity")
    @discord.app_commands.describe(
        message="Your message to the alien"
    )
    async def alien_chat(interaction: discord.Interaction, message: str):
        # Check if user is banned
        if is_user_banned(interaction.user.id):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="You are banned from using this bot.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Check if Gemini is configured
        if not configure_gemini():
            await interaction.response.send_message(
                "❌ **Quantum Communication Array Offline**\n"
                "The interdimensional transmission system is not configured. "
                "An administrator needs to set up the GEMINI_API_KEY in the bot's configuration.",
                ephemeral=True
            )
            return
        
        # Validate message length
        if len(message) > 500:
            await interaction.response.send_message(
                "⚠️ **Signal Too Strong**\n"
                "Your transmission is too powerful for our communication array. "
                "Please limit your message to 500 characters or less.",
                ephemeral=True
            )
            return
        
        # Defer response since AI generation might take time
        await interaction.response.defer()
        
        try:
            # Generate alien response
            alien_response = await chat_with_alien(message)
            
            # Create embed with the new structure
            embed = discord.Embed(
                title="ALIEN PAUL",
                color=0x00ff88,  # Alien green
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="YOUR MESSAGE:",
                value=message,
                inline=False
            )
            
            embed.add_field(
                name="PAUL RESPONSE:",
                value=alien_response,
                inline=False
            )
            
            embed.set_footer(
                text=f"Communication with {interaction.user.display_name} • Signal: Strong"
            )
            
            # Create file attachment for local image
            file_path = "assets/images/image.png"
            file = discord.File(file_path, filename="grok_image.png")
            embed.set_thumbnail(url="attachment://grok_image.png")
            
            await interaction.followup.send(embed=embed, file=file)
            
            logging.info(f"👽 Alien chat: {interaction.user.display_name} -> '{message[:50]}...'")
            
        except Exception as e:
            await interaction.followup.send(
                f"🚨 **Cosmic Communication Failure**\n"
                f"The quantum entanglement field collapsed during transmission. "
                f"Technical details: `{str(e)[:100]}...`\n"
                f"Please try again in a moment.",
                ephemeral=True
            )
            logging.error(f"❌ Alien chat error: {e}")
