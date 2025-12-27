"""
Web Dashboard for UFO Sighting Bot
Provides a web interface to monitor bot status, metrics, and activity.
"""
from flask import Flask, render_template_string, jsonify
from threading import Thread
import psutil
import os
from datetime import datetime, timedelta
from collections import deque
import logging

app = Flask(__name__)

# Global reference to bot instance
bot_instance = None
bot_start_time = None

# Store recent logs (max 100 entries)
recent_logs = deque(maxlen=100)

class DashboardLogHandler(logging.Handler):
    """Custom log handler to capture logs for the dashboard."""
    def emit(self, record):
        # Filter out Flask/werkzeug HTTP access logs
        if record.name in ('werkzeug', 'flask.app') and 'GET' in record.getMessage():
            return
        
        log_entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': record.levelname,
            'message': self.format(record)
        }
        recent_logs.append(log_entry)

def set_bot_instance(bot, start_time):
    """Set the bot instance for the dashboard to monitor."""
    global bot_instance, bot_start_time
    bot_instance = bot
    bot_start_time = start_time
    
    # Set up logging handler
    handler = DashboardLogHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger().addHandler(handler)

def get_bot_stats():
    """Get current bot statistics."""
    if not bot_instance:
        return None
    
    # Process stats
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    cpu_percent = process.cpu_percent(interval=1)
    
    # Calculate uptime
    uptime = datetime.now() - bot_start_time if bot_start_time else timedelta(0)
    uptime_str = str(uptime).split('.')[0]  # Remove microseconds
    
    # Bot stats
    guild_count = len(bot_instance.guilds) if bot_instance.guilds else 0
    user_count = sum(guild.member_count for guild in bot_instance.guilds) if bot_instance.guilds else 0
    
    return {
        'status': 'online' if bot_instance.is_ready() else 'offline',
        'uptime': uptime_str,
        'memory_mb': round(memory_info.rss / 1024 / 1024, 2),
        'memory_percent': round(process.memory_percent(), 2),
        'cpu_percent': round(cpu_percent, 2),
        'guild_count': guild_count,
        'user_count': user_count,
        'latency_ms': round(bot_instance.latency * 1000, 2) if bot_instance.is_ready() else 0,
        'bot_name': bot_instance.user.name if bot_instance.user else 'Unknown',
        'bot_id': bot_instance.user.id if bot_instance.user else 'Unknown',
    }

def get_reaction_stats():
    """Get reaction statistics from data file."""
    try:
        import json
        reactions_file = 'data/reactions.json'
        if os.path.exists(reactions_file):
            with open(reactions_file, 'r') as f:
                reactions_data = json.load(f)
            
            total_reactions = 0
            total_users = 0
            guilds_tracking = len(reactions_data)
            
            for guild_id, users in reactions_data.items():
                if isinstance(users, dict):
                    total_users += len(users)
                    total_reactions += sum(users.values())
            
            return {
                'total_reactions': total_reactions,
                'total_users': total_users,
                'guilds_tracking': guilds_tracking
            }
    except Exception as e:
        logging.error(f"Error reading reaction stats: {e}")
    
    return {
        'total_reactions': 0,
        'total_users': 0,
        'guilds_tracking': 0
    }

def get_recent_logs(limit=50):
    """Get recent log entries."""
    return list(recent_logs)[-limit:]

# HTML Template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #2a2a2a;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        .header {
            border-bottom: 2px solid #3a3a3a;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2em;
            margin-bottom: 10px;
            color: #ffffff;
        }
        .status-badge {
            display: inline-block;
            padding: 6px 16px;
            border-radius: 4px;
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.85em;
        }
        .status-online {
            background: #4caf50;
            color: white;
        }
        .status-offline {
            background: #f44336;
            color: white;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: #333333;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 20px;
        }
        .card-title {
            color: #999;
            font-size: 0.9em;
            margin-bottom: 12px;
            font-weight: 500;
        }
        .card-value {
            font-size: 2em;
            font-weight: 600;
            margin-bottom: 5px;
            color: #ffffff;
        }
        .card-label {
            color: #888;
            font-size: 0.85em;
        }
        .section {
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            background: #333333;
        }
        .section-title {
            color: #ffffff;
            font-size: 1.3em;
            margin-bottom: 20px;
            font-weight: 600;
        }
        .progress-bar {
            width: 100%;
            height: 24px;
            background: #1a1a1a;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
            position: relative;
        }
        .progress-fill {
            height: 100%;
            background: #2196f3;
            transition: width 0.3s;
        }
        .progress-text {
            position: absolute;
            top: 50%;
            left: 8px;
            transform: translateY(-50%);
            font-size: 0.85em;
            font-weight: 500;
            color: #ffffff;
            z-index: 1;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #3a3a3a;
        }
        .info-row:last-child {
            border-bottom: none;
        }
        .info-label {
            color: #999;
            font-weight: 500;
        }
        .info-value {
            color: #ffffff;
            font-weight: 600;
        }
        .refresh-notice {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #3a3a3a;
        }
        .logs-container {
            background: #1a1a1a;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }
        .log-entry {
            padding: 6px 0;
            border-bottom: 1px solid #2a2a2a;
            display: flex;
            gap: 10px;
        }
        .log-entry:last-child {
            border-bottom: none;
        }
        .log-time {
            color: #666;
            min-width: 70px;
        }
        .log-level {
            min-width: 60px;
            font-weight: 600;
        }
        .log-level-INFO {
            color: #2196f3;
        }
        .log-level-WARNING {
            color: #ff9800;
        }
        .log-level-ERROR {
            color: #f44336;
        }
        .log-level-DEBUG {
            color: #9c27b0;
        }
        .log-message {
            color: #e0e0e0;
            flex: 1;
        }
        .logs-container::-webkit-scrollbar {
            width: 8px;
        }
        .logs-container::-webkit-scrollbar-track {
            background: #1a1a1a;
        }
        .logs-container::-webkit-scrollbar-thumb {
            background: #3a3a3a;
            border-radius: 4px;
        }
        .logs-container::-webkit-scrollbar-thumb:hover {
            background: #4a4a4a;
        }
    </style>
    <script>
        setInterval(() => {
            location.reload();
        }, 5000);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Discord Bot Dashboard</h1>
            <span class="status-badge status-{{ stats.status }}">{{ stats.status }}</span>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-title">Uptime</div>
                <div class="card-value">{{ stats.uptime }}</div>
            </div>
            <div class="card">
                <div class="card-title">Memory Usage</div>
                <div class="card-value">{{ stats.memory_mb }} MB</div>
                <div class="card-label">{{ stats.memory_percent }}% of system</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ stats.memory_percent }}%"></div>
                    <div class="progress-text">{{ stats.memory_percent }}%</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">CPU Usage</div>
                <div class="card-value">{{ stats.cpu_percent }}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ stats.cpu_percent }}%"></div>
                    <div class="progress-text">{{ stats.cpu_percent }}%</div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Guilds</div>
                <div class="card-value">{{ stats.guild_count }}</div>
                <div class="card-label">Servers connected</div>
            </div>
            <div class="card">
                <div class="card-title">Users</div>
                <div class="card-value">{{ stats.user_count }}</div>
                <div class="card-label">Total members</div>
            </div>
            <div class="card">
                <div class="card-title">Latency</div>
                <div class="card-value">{{ stats.latency_ms }} ms</div>
                <div class="card-label">Discord API</div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Reaction Statistics</div>
            <div class="grid">
                <div class="card">
                    <div class="card-title">Total Reactions</div>
                    <div class="card-value">{{ reaction_stats.total_reactions }}</div>
                    <div class="card-label">All-time sightings</div>
                </div>
                <div class="card">
                    <div class="card-title">Active Users</div>
                    <div class="card-value">{{ reaction_stats.total_users }}</div>
                    <div class="card-label">Users tracking</div>
                </div>
                <div class="card">
                    <div class="card-title">Tracking Servers</div>
                    <div class="card-value">{{ reaction_stats.guilds_tracking }}</div>
                    <div class="card-label">Servers with reactions</div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Bot Information</div>
            <div class="info-row">
                <span class="info-label">Bot Name</span>
                <span class="info-value">{{ stats.bot_name }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Bot ID</span>
                <span class="info-value">{{ stats.bot_id }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Status</span>
                <span class="info-value">{{ stats.status }}</span>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Recent Logs (Last 50)</div>
            <div class="logs-container" id="logs">
                {% for log in logs %}
                <div class="log-entry">
                    <span class="log-time">{{ log.time }}</span>
                    <span class="log-level log-level-{{ log.level }}">{{ log.level }}</span>
                    <span class="log-message">{{ log.message }}</span>
                </div>
                {% else %}
                <div class="log-entry">
                    <span class="log-message" style="color: #666;">No logs yet...</span>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="refresh-notice">
            Auto-refreshes every 5 seconds
        </div>
    </div>
    <script>
        const logsContainer = document.getElementById('logs');
        if (logsContainer) {
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Render the main dashboard."""
    stats = get_bot_stats()
    if not stats:
        return "Bot not initialized yet. Please wait...", 503
    
    reaction_stats = get_reaction_stats()
    logs = get_recent_logs()
    
    return render_template_string(DASHBOARD_HTML, stats=stats, reaction_stats=reaction_stats, logs=logs)

@app.route('/api/stats')
def api_stats():
    """API endpoint for bot statistics (JSON)."""
    stats = get_bot_stats()
    if not stats:
        return jsonify({'error': 'Bot not initialized'}), 503
    
    reaction_stats = get_reaction_stats()
    return jsonify({
        'bot': stats,
        'reactions': reaction_stats
    })

@app.route('/health')
def health():
    """Health check endpoint."""
    if bot_instance and bot_instance.is_ready():
        return jsonify({'status': 'healthy'}), 200
    return jsonify({'status': 'unhealthy'}), 503

def run_dashboard(host='0.0.0.0', port=5000):
    """Run the Flask dashboard server."""
    app.run(host=host, port=port, debug=False, use_reloader=False)

def start_dashboard_thread(bot, start_time, host='0.0.0.0', port=5000):
    """Start the dashboard in a separate thread."""
    set_bot_instance(bot, start_time)
    thread = Thread(target=run_dashboard, args=(host, port), daemon=True)
    thread.start()
    logging.info(f"📋 Dashboard started at http://{host}:{port}")
    return thread
