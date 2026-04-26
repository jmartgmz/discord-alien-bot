# 🛸 UFO Sighting Bot

This bot randomly sends UFO images to configured channels and tracks user reactions.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- A Discord application and bot token

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/jmartgmz/ufo-sighting-bot.git
   cd ufo-sighting-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your Discord bot token
   ```

4. **Run the bot**
   ```bash
   python run_bot.py
   ```
   
   Or run directly from the src directory:
   ```bash
   python src/ufo_main.py
   ```

### Discord Bot Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section and create a bot
4. Copy the bot token and add it to your `.env` file
5. Go to "OAuth2" > "URL Generator"
6. Select scopes: `bot`, `applications.commands`
7. Select permissions: `Send Messages`, `Add Reactions`, `Manage Messages`, `Use Slash Commands`
8. Invite the bot to your server using the generated URL

### How to Use

1. Use `/setchannel` in the channel where you want UFO images to appear
2. The bot will start sending random UFO images at random intervals
3. React with 👽 to the images to track your sightings
4. Check your progress with `/usersightings` or `/globalsightings`

## 📁 Project Structure

```
ufo-sighting-bot/
├── src/                        # Source code
│   ├── commands/              # Command modules
│   │   ├── __init__.py       # Commands package init
│   │   ├── admin.py          # Bot info and admin commands
│   │   ├── setup.py          # Channel setup and testing
│   │   └── sightings.py      # Reaction tracking and leaderboards
│   ├── utils/                # Utility modules
│   │   ├── __init__.py       # Utils package init
│   │   ├── auth.py           # User authorization management
│   │   ├── config.py         # Configuration management
│   │   └── helpers.py        # Helper functions and constants
│   ├── ufo_main.py           # Main bot file
│   └── ufo_main_backup.py    # Backup of original monolithic file
├── data/                     # Data directory (gitignored)
│   ├── ufo_bot.db            # SQLite database for persistent storage
│   └── tickets.json          # Support tickets tracking
├── logs/                     # Log files
├── docs/                     # Documentation
├── run_bot.py                # Bot launcher script

├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 🛠️ Configuration

The bot automatically creates and manages a SQLite database (`data/ufo_bot.db`) for **persistent storage**. The database holds:

- Channel configurations for each server
- User reaction counts across all servers (survives bot restarts)
- User authorizations and ban lists

### 🔐 Authorization System

The bot includes a built-in authorization system for sensitive commands:

**Admin Users** - Can manage other users' permissions and use all admin commands
**Botinfo Users** - Can use the `/botinfo` command to view bot statistics

**Default Setup:**
1. On first run, the bot initializes the SQLite database with your Discord ID as an admin
2. Admins can use `/authorize @user` to grant botinfo access
3. Use `/deauthorize @user` to remove access
4. Use `/listauthorized` to see all authorized users

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.