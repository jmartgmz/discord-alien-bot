"""
Support system commands for the UFO Sighting Bot.
Allows users to send support requests to admins and receive replies.
"""
import discord
from datetime import datetime
from utils.auth import is_admin_user
from utils import (
    load_config, save_config, load_reactions, save_reactions, is_admin_user,
    create_ticket, get_ticket, delete_ticket, get_open_tickets
)
from utils.helpers import is_user_banned

def setup_support_commands(bot):
    """Set up support-related commands."""
    
    @bot.tree.command(name="support", description="Get help from administrators")
    async def support_request(interaction: discord.Interaction, message: str):
        # Check if user is banned
        if is_user_banned(interaction.user.id):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="You are banned from using this bot.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Load config to find support channel
        config = load_config()
        support_channel_id = None
        
        # Look for any guild with a support_channel_id configured
        for guild_config in config.values():
            if isinstance(guild_config, dict) and "support_channel_id" in guild_config:
                support_channel_id = guild_config["support_channel_id"]
                break
        
        if not support_channel_id:
            await interaction.response.send_message(
                "❌ No support channel has been configured. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        support_channel = bot.get_channel(support_channel_id)
        if not support_channel:
            await interaction.response.send_message(
                "❌ Support channel not found. Please contact an administrator.",
                ephemeral=True
            )
            return
        
        # Create the support ticket using the new system
        ticket_id = create_ticket(
            user_id=interaction.user.id,
            user_name=interaction.user.display_name,
            guild_id=interaction.guild.id if interaction.guild else None,
            guild_name=interaction.guild.name if interaction.guild else "Direct Message",
            message=message
        )
        
        # Create embed for support channel
        support_embed = discord.Embed(
            title="🎫 New Support Request",
            color=0xff6600,
            timestamp=datetime.now()
        )
        
        support_embed.add_field(
            name="📋 Ticket ID",
            value=f"`{ticket_id}`",
            inline=True
        )
        
        support_embed.add_field(
            name="👤 User",
            value=f"**{interaction.user.display_name}**\n`{interaction.user.id}`",
            inline=True
        )
        
        support_embed.add_field(
            name="🏛️ Server",
            value=interaction.guild.name if interaction.guild else "Direct Message",
            inline=True
        )
        
        support_embed.add_field(
            name="💬 Message",
            value=message,
            inline=False
        )
        
        support_embed.add_field(
            name="📝 Reply Instructions",
            value=f"Use `!reply {ticket_id} <your response>` to respond to this ticket.",
            inline=False
        )
        
        support_embed.set_footer(text="UFO Sighting Bot Support System")
        
        # Send to support channel first
        try:
            await support_channel.send(embed=support_embed)
            success = True
            error_message = None
        except discord.Forbidden:
            success = False
            error_message = "❌ Unable to send support request. The bot may not have permission to send messages to the support channel."
        except Exception as e:
            success = False
            error_message = f"❌ An error occurred while sending your support request: {str(e)}"
        
        # Send response to user based on success/failure
        if success:
            # Confirm to user
            user_embed = discord.Embed(
                title="✅ Support Request Sent",
                description=f"Your support request has been sent to the administrators.",
                color=0x00ff41,
                timestamp=datetime.now()
            )
            
            user_embed.add_field(
                name="🎫 Ticket ID",
                value=f"`{ticket_id}`",
                inline=True
            )
            
            user_embed.add_field(
                name="⏰ Status",
                value="Open - Awaiting Response",
                inline=True
            )
            
            user_embed.add_field(
                name="💬 Your Message",
                value=message,
                inline=False
            )
            
            user_embed.set_footer(text="You will receive a DM when an admin responds")
            
            await interaction.response.send_message(embed=user_embed, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)

    @bot.command(name="supportchannel")
    async def set_support_channel(ctx, channel: discord.TextChannel | None = None):
        """Set support ticket channel (admin)"""
        # Check if user is admin
        if not is_admin_user(ctx.author.id):
            await ctx.send("❌ You need admin permissions to set the support channel.")
            return

        if ctx.guild is None:
            await ctx.send("❌ This command must be used in a server.")
            return

        # If no channel specified, use current channel
        if channel is None:
            channel = ctx.channel
        
        # Ensure channel is a TextChannel
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Invalid channel type. Please specify a text channel.")
            return

        guild_id = str(ctx.guild.id)
        
        # Load config and update support channel
        config = load_config()
        
        if guild_id not in config:
            config[guild_id] = {}
        elif not isinstance(config[guild_id], dict):
            # Convert old format to new format
            old_value = config[guild_id]
            config[guild_id] = {"channel_id": old_value}
        
        config[guild_id]["support_channel_id"] = channel.id
        save_config(config)

        embed = discord.Embed(
            title="🎫 Support Channel Set",
            description=f"Support requests will now be sent to {channel.mention}",
            color=0x00ff41,
            timestamp=datetime.now()
        )

        embed.add_field(
            name="📋 What gets sent here:",
            value="• User support requests\n• Ticket IDs for replies\n• User and server information\n• Timestamps",
            inline=False
        )

        embed.add_field(
            name="📝 How to reply:",
            value="Use `!reply <ticket_id> <your response>` to respond to support tickets.",
            inline=False
        )

        embed.add_field(
            name="ℹ️ Note:",
            value="The bot needs **Send Messages** permission in the support channel.",
            inline=False
        )

        embed.set_footer(
            text=f"Set by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)

        # Send a test message to the support channel
        try:
            test_embed = discord.Embed(
                title="🎫 Support Channel Activated",
                description="This channel is now receiving UFO Sighting Bot support requests.",
                color=0x4169E1,
                timestamp=datetime.now()
            )
            test_embed.add_field(
                name="🚀 Ready to help users with:",
                value="Bug reports, feature requests, questions, and more!",
                inline=False
            )
            test_embed.set_footer(text="UFO Sighting Bot Support System")
            
            await channel.send(embed=test_embed)
        except discord.Forbidden:
            # Send error message back to user if bot can't send to support channel
            error_embed = discord.Embed(
                title="⚠️ Permission Issue",
                description=f"I cannot send messages to {channel.mention}. Please ensure I have **Send Messages** permission in that channel.",
                color=0xff6600
            )
            await ctx.send(embed=error_embed)

    @bot.command(name="reply")
    async def reply_to_ticket(ctx, ticket_id: str, *, response: str):
        """Reply to support ticket (admin)"""
        # Check if user is admin
        if not is_admin_user(ctx.author.id):
            await ctx.send("❌ You need admin permissions to reply to support tickets.")
            return
        
        # Get the ticket using new system
        ticket = get_ticket(ticket_id)
        
        if not ticket:
            await ctx.send(f"❌ Ticket `{ticket_id}` not found. Please check the ticket ID.")
            return
        
        # Check if ticket is already closed
        if ticket["status"] != "open":
            await ctx.send(
                f"❌ Ticket `{ticket_id}` is already closed. Cannot reply to closed tickets.\n"
                f"Status: `{ticket['status']}`\n"
                f"Use `!alltickets` to see open tickets only."
            )
            return
        
        user_id = ticket["user_id"]
        
        # Get the user to send DM
        user = bot.get_user(user_id)
        if not user:
            await ctx.send(f"❌ Could not find user for ticket `{ticket_id}`. They may have left Discord or blocked the bot.")
            return
        
        # Create response embed for user
        user_embed = discord.Embed(
            title="📬 Support Response Received",
            color=0x00ff41,
            timestamp=datetime.now()
        )
        
        user_embed.add_field(
            name="🎫 Ticket ID",
            value=f"`{ticket_id}`",
            inline=True
        )
        
        user_embed.add_field(
            name="📅 Original Request",
            value=ticket["timestamp"][:10],  # Just the date
            inline=True
        )
        
        user_embed.add_field(
            name="💬 Your Original Message",
            value=ticket["message"],
            inline=False
        )
        
        user_embed.add_field(
            name="📝 Admin Response",
            value=response,
            inline=False
        )
        
        user_embed.add_field(
            name="🔄 Need More Help?",
            value="Use `/support <message>` to create a new support request if you need further assistance.",
            inline=False
        )
        
        user_embed.set_footer(text=f"Responded by {ctx.author.display_name}")
        
        try:
            await user.send(embed=user_embed)
            
            # Delete ticket after admin response (ticket is resolved)
            delete_ticket(ticket_id)
            
            # Confirm to admin
            admin_embed = discord.Embed(
                title="✅ Reply Sent Successfully",
                description=f"Your response has been sent to **{ticket['user_name']}** via DM.",
                color=0x00ff41,
                timestamp=datetime.now()
            )
            
            admin_embed.add_field(
                name="🎫 Ticket ID",
                value=f"`{ticket_id}`",
                inline=True
            )
            
            admin_embed.add_field(
                name="👤 User",
                value=f"**{ticket['user_name']}**",
                inline=True
            )
            
            admin_embed.add_field(
                name="📝 Your Response",
                value=response,
                inline=False
            )
            
            admin_embed.set_footer(text="Ticket has been marked as closed")
            
            await ctx.send(embed=admin_embed)
            
        except discord.Forbidden:
            await ctx.send(f"❌ Could not send DM to **{ticket['user_name']}**. They may have DMs disabled or have blocked the bot.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred while sending the reply: {str(e)}")
    @bot.command(name="ticketstats")
    async def ticket_stats(ctx):
        """View support ticket statistics (admin)"""
        # Check if user is admin
        if not is_admin_user(ctx.author.id):
            await ctx.send("❌ You need admin permissions to view ticket statistics.")
            return
        
        from utils.tickets import load_tickets
        all_tickets = load_tickets()
        open_tickets = get_open_tickets()
        
        embed = discord.Embed(
            title="📊 Support Ticket Statistics",
            color=0x4169E1,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📈 Total Tickets",
            value=str(len(all_tickets)),
            inline=True
        )
        
        embed.add_field(
            name="🟢 Open Tickets",
            value=str(len(open_tickets)),
            inline=True
        )
        
        embed.add_field(
            name="🔴 Closed Tickets",
            value=str(len(all_tickets) - len(open_tickets)),
            inline=True
        )
        
        # Show recent open tickets
        if open_tickets:
            recent_open = []
            for ticket_id, ticket in list(open_tickets.items())[:5]:
                recent_open.append(f"`{ticket_id}` - **{ticket['user_name']}**")
            
            embed.add_field(
                name="🕐 Recent Open Tickets",
                value="\n".join(recent_open),
                inline=False
            )
        
        embed.set_footer(text="Use !reply <ticket_id> <response> to respond to tickets")
        
        await ctx.send(embed=embed)

    @bot.command(name="alltickets")
    async def all_tickets(ctx):
        """View all support tickets (admin)"""
        # Check if user is admin
        if not is_admin_user(ctx.author.id):
            await ctx.send("❌ You need admin permissions to view all tickets.")
            return
        
        open_tickets = get_open_tickets()
        
        if not open_tickets:
            await ctx.send("📭 No open support tickets.")
            return
        
        embed = discord.Embed(
            title="🎫 All Open Support Tickets",
            color=0xFF6B35,
            timestamp=datetime.now()
        )
        
        ticket_list = []
        for ticket_id, ticket in open_tickets.items():
            # Truncate long messages
            message = ticket["message"]
            if len(message) > 100:
                message = message[:97] + "..."
            
            ticket_info = f"**`{ticket_id}`** - {ticket['user_name']}\n*{message}*\n*{ticket['timestamp'][:10]}*"
            ticket_list.append(ticket_info)
        
        # Split into multiple fields if too many tickets
        for i in range(0, len(ticket_list), 5):
            field_tickets = ticket_list[i:i+5]
            field_name = f"Tickets ({i+1}-{min(i+5, len(ticket_list))})"
            embed.add_field(
                name=field_name,
                value="\n\n".join(field_tickets),
                inline=False
            )
        
        embed.set_footer(text=f"Total open tickets: {len(open_tickets)} | Use !reply <ticket_id> <response>")
        
        await ctx.send(embed=embed)