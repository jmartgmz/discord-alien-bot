"""
Help commands for the UFO Sighting Bot.
"""
import discord
from datetime import datetime
from utils.auth import is_admin_user, load_authorized_users

def setup_help_commands(bot):
    """Set up help-related commands."""
    
    @bot.tree.command(name="help", description="Show available commands")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="UFO Sighting Bot Commands",
            description="Here are all the commands you can use:",
            color=0x00ff41,
            timestamp=datetime.now()
        )

        # User commands
        user_commands = [
            "`/usersightings` - See your UFO sightings across all servers (or check another user)",
            "`/localsightings` - See your UFO sightings in this server",
            "`/globalsightings` - See your total sightings across all servers",
            "`/alien <message>` - Chat with an alien from Kepler-442b using AI",
            "`/support <message>` - Send a support request to administrators",
            "`/help` - Show this help message",
            "`/helpadmin` - Show admin commands (if you're an admin)"
        ]

        embed.add_field(
            name="🛸 User Commands",
            value="\n".join(user_commands),
            inline=False
        )

        # Setup commands (if in a server)
        if interaction.guild:
            setup_commands = [
                "`/setchannel` - Set this channel for UFO image messages"
            ]

            embed.add_field(
                name="⚙️ Setup Commands",
                value="\n".join(setup_commands),
                inline=False
            )

        embed.add_field(
            name="ℹ️ How it works",
            value="React to UFO images with any emoji to track your sightings!\nUse `/usersightings` to see your progress across all servers.",
            inline=False
        )

        # Created by section - get admin users
        try:
            auth_data = load_authorized_users()
            admin_users = auth_data.get("admin_users", [])
            
            if admin_users:
                admin_info = []
                for admin_id in admin_users:
                    try:
                        admin_user = bot.get_user(admin_id)
                        if admin_user:
                            admin_info.append(f"**{admin_user.display_name}**")
                        else:
                            admin_info.append(f"**Admin** `{admin_id}`")
                    except:
                        admin_info.append(f"**Admin** `{admin_id}`")
                
                if admin_info:
                    embed.add_field(
                        name="👑 Created by",
                        value="\n".join(admin_info),
                        inline=False
                    )
                    
                    # Set thumbnail to first admin's avatar if available
                    try:
                        first_admin = bot.get_user(admin_users[0])
                        if first_admin:
                            embed.set_thumbnail(url=first_admin.display_avatar.url)
                    except:
                        pass
        except:
            # If there's any error loading admin info, just skip this section
            pass

        embed.set_footer(
            text=f"Requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="helpadmin", description="Show admin commands (admin)")
    async def helpadmin_command(interaction: discord.Interaction):
        # Check if user is admin or owner
        if not is_admin_user(interaction.user.id):
            embed = discord.Embed(
                title="Access Denied",
                description="You need admin permissions to view admin commands.",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="UFO Sighting Bot - Admin Commands",
            description="Administrative and owner-only commands:",
            color=0xff6600,
            timestamp=datetime.now()
        )

        # Admin commands
        admin_commands = [
            "`!botinfo` - Display bot system information and stats",
            "`!authorize <user>` - Add user to the admin list",
            "`!deauthorize <user>` - Remove user from the admin list",
            "`!listauthorized` - List all admin users",
            "`!setlogchannel [channel]` - Set global logging channel (logs all servers)",
            "`!supportchannel [channel]` - Set channel for support requests",
            "`!reply <ticket_id> <response>` - Reply to a support ticket",
            "`!ban <user> [reason]` - Ban a user from using the bot",
            "`!unban <user>` - Unban a user from using the bot",
            "`!globalmessage <message>` - Send a message to all servers",
            "`!testimage` - Send a test UFO image",
            "`!testsetup` - Replay the welcome setup message"
        ]

        embed.add_field(
            name="🔧 Admin Commands",
            value="\n".join(admin_commands),
            inline=False
        )

        # Owner commands
        owner_commands = [
            "`!sync` - Manually sync slash commands (Owner only)"
        ]

        embed.add_field(
            name="👑 Owner Commands",
            value="\n".join(owner_commands),
            inline=False
        )

        embed.add_field(
            name="ℹ️ Admin Info",
            value="Admin commands require special permissions.\nContact the bot owner if you need access.",
            inline=False
        )

        embed.set_footer(
            text=f"Admin help requested by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)