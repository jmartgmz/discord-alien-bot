# Docker Deployment Guide

This guide explains how to run the Discord Alien Bot using Docker.

> **Note**: For CosmosCloud/Cosmos Server deployment, see [COSMOS_DEPLOYMENT.md](COSMOS_DEPLOYMENT.md)

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- A `.env` file with your bot credentials

## Quick Start

### 1. Create Environment File

Create a `.env` file in the project root:

```bash
DISCORD_TOKEN=your_discord_token_here
GEMINI_API_KEY=your_gemini_api_key_here
DASHBOARD_PORT=8080  # Optional, defaults to 8080
```

### 2. Build and Run with Docker Compose (Recommended)

```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Access web dashboard
# Open http://localhost:8080 in your browser

# Stop the bot
docker-compose down

# Restart the bot
docker-compose restart
```

### 3. Or Build and Run with Docker Commands

```bash
# Build the image
docker build -t discord-alien-bot .

# Run the container
docker run -d \
  --name discord-alien-bot \
  --env-file .env \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/assets:/app/assets:ro \
  --restart unless-stopped \
  discord-alien-bot

# View logs
docker logs -f discord-alien-bot

# Stop the container
docker stop discord-alien-bot

# Remove the container
docker rm discord-alien-bot
```

## Web Dashboard

The bot includes a web dashboard for monitoring:

- **URL**: http://localhost:8080 (or your server's IP:8080)
- **Features**:
  - Real-time bot status (online/offline)
  - Memory and CPU usage
  - Uptime tracking
  - Connected guilds and users
  - Discord API latency
  - Total reaction statistics
  - Active user counts

The dashboard auto-refreshes every 5 seconds.

### API Endpoints

- `GET /` - Web dashboard UI
- `GET /api/stats` - JSON statistics endpoint
- `GET /health` - Health check endpoint

## Data Persistence

The following directories are mounted as volumes to persist data:

- `./data` - Bot configuration, reactions, tickets, authorized users, etc.
- `./assets` - UFO images (read-only by default)

Your data will persist even if you rebuild or restart the container.

## Managing the Bot

### View Logs
```bash
docker-compose logs -f discord-bot
# or
docker logs -f discord-alien-bot
```

### Restart Bot
```bash
docker-compose restart
# or
docker restart discord-alien-bot
```

### Update Bot
```bash
# Pull latest code changes
git pull

# Rebuild and restart
docker-compose up -d --build
```

### Stop Bot
```bash
docker-compose down
# or
docker stop discord-alien-bot
```

### Access Bot Shell (for debugging)
```bash
docker-compose exec discord-bot /bin/bash
# or
docker exec -it discord-alien-bot /bin/bash
```

## Resource Limits

By default, the bot is limited to:
- CPU: 1 core max, 0.25 cores reserved
- Memory: 512MB max, 128MB reserved

You can adjust these in `docker-compose.yml` under the `deploy.resources` section.

## Troubleshooting

### Bot won't start
1. Check logs: `docker-compose logs`
2. Verify `.env` file has correct tokens
3. Ensure data directory has write permissions

### Permission issues
```bash
# Fix data directory permissions
chmod -R 755 data/
```

### Out of memory
Increase memory limit in `docker-compose.yml`:
```yaml
memory: 1G  # instead of 512M
```

### Rebuild from scratch
```bash
# Remove old containers and images
docker-compose down
docker rmi discord-alien-bot

# Rebuild
docker-compose up -d --build
```

## Production Deployment

For production, consider:

1. **Use a process manager** - Docker will restart the bot if it crashes
2. **Monitor logs** - Set up log aggregation (e.g., via Docker logging drivers)
3. **Backup data** - Regularly backup the `./data` directory
4. **Update regularly** - Keep dependencies and base image updated
5. **Use secrets** - Consider Docker secrets instead of env files for sensitive data

## Advanced Configuration

### Custom Port Mapping (if needed in future)
```yaml
ports:
  - "8080:8080"
```

### Multiple Bots
To run multiple instances, duplicate the service in `docker-compose.yml` with different names and env files.

### Network Configuration
The bot runs on the default bridge network. For advanced networking, modify `docker-compose.yml`.
