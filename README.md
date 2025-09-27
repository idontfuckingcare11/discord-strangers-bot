# Discord World Boss Timer Bot

This is a Discord bot that allows users to start world boss timers with custom durations and receive alerts when the timer ends.

## Features
- `/wb <time>` - Start a world boss timer with a custom duration (supports formats like 50m, 2h, or 1h3m)
- `/wbstop` - Cancel the current countdown early
- Timer updates every minute initially, then switches to every second during the last 10 minutes
- Shows remaining time in an embed that updates periodically
- Pings @everyone with a world boss alert when the timer ends
- Each channel can have its own timer tracked separately

## Setup

### 1. Install Dependencies
```
pip install -r requirements.txt
```

### 2. Configure Bot Token
Open `bot.py` and replace `YOUR_BOT_TOKEN` with your actual Discord bot token:
```python
TOKEN = "YOUR_BOT_TOKEN"
```

### 3. Invite the Bot to Your Server
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Go to the "OAuth2" tab
4. Under "Scopes", select "bot" and "applications.commands"
5. Under "Bot Permissions", select the necessary permissions (Send Messages, Mention Everyone, Use Slash Commands)
6. Copy the generated URL and paste it into your browser to invite the bot to your server

### 4. Run the Bot
```
python bot.py
```

## Usage

### Starting a Timer
Use the `/wb` command followed by a duration:
- `/wb 50m` - Starts a 50-minute timer
- `/wb 2h` - Starts a 2-hour timer
- `/wb 1h3m` - Starts a 1-hour and 3-minute timer

### Stopping a Timer
Use the `/wbstop` command to cancel the current timer in your channel.

## Notes
- If you start a new timer while one is already running, the old timer will be stopped automatically
- The bot will ping @everyone when the timer ends
- Make sure the bot has the necessary permissions to send messages and mention everyone in your server