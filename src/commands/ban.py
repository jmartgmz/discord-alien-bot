"""
Ban management commands for the UFO Sighting Bot.
"""
import discord
from discord.ext import commands
from utils.helpers import (
    is_user_banned, ban_user, unban_user, get_ban_info
)
from utils.auth import is_admin_user
from datetime import datetime

def setup_ban_commands(bot):
    """Set up ban management commands."""
    
    @bot.command(name="ban")
    async def ban_user_command(ctx, user: discord.User, *, reason: str = "No reason provided"):
        """Ban a user from using the bot (admin)"""
        # Check if user is admin
        if not is_admin_user(ctx.author.id):
            await ctx.send("❌ You need admin permissions to ban users.")
            return

        # Prevent banning administrators
        if ctx.guild:
            try:
                member = ctx.guild.get_member(user.id)
                if member and member.guild_permissions.administrator:
                    await ctx.send("❌ You cannot ban users with administrator permissions.")
                    return
            except:
                pass  # User might not be in the server

        # Check if user is already banned
        if is_user_banned(user.id):
            await ctx.send(f"⚠️ {user.mention} is already banned from using the bot.")
            return

        # Ban the user
        ban_user(user.id, reason, ctx.author.id)

        embed = discord.Embed(
            title="🔨 User Banned",
            description=f"{user.mention} has been banned from using the UFO Sighting Bot.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Banned by", value=ctx.author.mention, inline=True)
        embed.add_field(name="Date", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=True)
        embed.set_footer(text=f"User ID: {user.id}")

        await ctx.send(embed=embed)

    @bot.command(name="unban")
    async def unban_user_command(ctx, user: discord.User):
        """Unban a user from using the bot (admin)"""
        # Check if user is admin
        if not is_admin_user(ctx.author.id):
            await ctx.send("❌ You need admin permissions to unban users.")
            return

        # Check if user is banned
        if not is_user_banned(user.id):
            await ctx.send(f"⚠️ {user.mention} is not currently banned.")
            return

        # Get ban info before unbanning
        ban_info = get_ban_info(user.id)
        
        # Unban the user
        if unban_user(user.id):
            embed = discord.Embed(
                title="✅ User Unbanned",
                description=f"{user.mention} has been unbanned and can now use the UFO Sighting Bot.",
                color=discord.Color.green()
            )
            embed.add_field(name="Unbanned by", value=ctx.author.mention, inline=True)
            embed.add_field(name="Date", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=True)
            
            if ban_info:
                embed.add_field(name="Original Ban Reason", value=ban_info.get("reason", "Unknown"), inline=False)
            
            embed.set_footer(text=f"User ID: {user.id}")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to unban the user. Please try again.")