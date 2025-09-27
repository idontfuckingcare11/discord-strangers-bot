import sys
import os

# Mock the audioop module to prevent import errors in Python 3.13
class MockAudioop:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules['audioop'] = MockAudioop()

# Import discord.py with app_commands for slash commands
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

# Your bot token - loaded from environment variable for security
TOKEN = os.getenv("DISCORD_TOKEN")

# Channel ID where alerts should be posted
ALERT_CHANNEL_ID = 1421584594943082517

# Define schedule (UTC times)
# Format: (day_of_week, hour, minute, "Event Name")
# day_of_week: 0=Monday ... 6=Sunday
EVENT_SCHEDULE = [
    (0, 0, 0, "Team Deathmatch"),
    (0, 1, 0, "Faction Battlegrounds"),
    (0, 2, 0, "FFA (Infinite)"),
    (0, 4, 0, "Conquest"),
    (0, 6, 0, "FFA (Lives)"),
    (0, 7, 0, "Faction Battlegrounds"),
    (0, 8, 0, "Team Deathmatch"),
    (0, 10, 0, "FFA (Infinite)"),
    (0, 12, 0, "Conquest"),
    (0, 13, 0, "Faction Battlegrounds"),
    (0, 14, 0, "FFA (Lives)"),
    (0, 16, 0, "Team Deathmatch"),
    (0, 18, 0, "Guild Siege"),
    (0, 19, 0, "Faction Battlegrounds"),
    (0, 20, 0, "Conquest"),
    (0, 22, 0, "FFA (Infinite)"),
    # Add the rest of the week here (Tuesday–Sunday) as needed
]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Store active timers for each channel
active_timers = {}

async def send_event_alert(event_name, channel_id):
    channel = bot.get_channel(channel_id)
    if channel:
        await channel.send(f"⏰ Prepare! 5 minutes from now: **{event_name}**")

@bot.event
async def on_ready():
    print(f"[*] Bot logged in as {bot.user}")
    print(f"[*] Bot ID: {bot.user.id}")
    
    # Sync slash commands with Discord
    try:
        synced = await bot.tree.sync()
        print(f"[*] Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"[!] Failed to sync commands: {e}")
    
    # Check bot permissions
    guild_count = len(bot.guilds)
    print(f"[*] Bot is in {guild_count} server(s)")
    
    if guild_count > 0:
        for guild in bot.guilds:
            print(f"[*] Server: {guild.name} (ID: {guild.id})")
            bot_member = guild.get_member(bot.user.id)
            if bot_member:
                perms = bot_member.guild_permissions
                print(f"    - Send Messages: {perms.send_messages}")
                print(f"    - Mention Everyone: {perms.mention_everyone}")
                print(f"    - Embed Links: {perms.embed_links}")
    
    print("[*] Bot is ready! Try /wb <time> to start a timer or /wbstop to cancel it!")
    print("[*] Commands available: /wb and /wbstop")
    
    # Initialize scheduler for event alerts
    scheduler = AsyncIOScheduler(timezone=pytz.utc)
    
    for day, hour, minute, name in EVENT_SCHEDULE:
        # Schedule 5 minutes before
        alert_minute = (minute - 5) % 60
        alert_hour = hour if minute >= 5 else (hour - 1) % 24
        scheduler.add_job(
            send_event_alert,
            "cron",
            day_of_week=day,
            hour=alert_hour,
            minute=alert_minute,
            args=[name, ALERT_CHANNEL_ID],
        )
    
    scheduler.start()
    print("[*] Scheduler started with weekly event alerts") 

# Command to start world boss timer with custom duration
@bot.tree.command(name="wb", description="Start StrangersAlert world boss timer with custom duration")
@app_commands.describe(duration="Timer duration (e.g. 2h7m, 90m, 50m)")
async def wb(interaction: discord.Interaction, duration: str):
    # Check if command is used in a server (not DM)
    if interaction.guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server, not in DMs!", ephemeral=True)
        return
    
    # Check if bot has necessary permissions in the channel
    bot_member = interaction.guild.get_member(bot.user.id)
    if not bot_member:
        await interaction.response.send_message("❌ I can't access my permissions information. Please try again later.", ephemeral=True)
        return
    
    if not bot_member.guild_permissions.send_messages:
        await interaction.response.send_message("❌ I don't have permission to send messages in this server.", ephemeral=True)
        return
    
    if not bot_member.guild_permissions.mention_everyone:
        await interaction.response.send_message("❌ I need 'Mention Everyone' permission to notify everyone when the timer ends.", ephemeral=True)
        return
    
    duration = duration.lower()
    
    # Parse duration format (supports 50m, 2h, 1h3m)
    hours, minutes = 0, 0
    if "h" in duration:
        parts = duration.split("h")
        hours = int(parts[0]) if parts[0] else 0
        if "m" in parts[1]:
            minutes = int(parts[1].replace("m", "")) if parts[1].replace("m", "") else 0
    elif "m" in duration:
        minutes = int(duration.replace("m", ""))
    else:
        await interaction.response.send_message("❌ Please use format like `2h7m` or `50m`.", ephemeral=True)
        return
    
    total_seconds = hours * 3600 + minutes * 60
    if total_seconds <= 0:
        await interaction.response.send_message("❌ Invalid time. Must be greater than 0.", ephemeral=True)
        return
    
    # Cancel existing timer in this channel if one is running
    if interaction.channel_id in active_timers:
        active_timers[interaction.channel_id]["cancel"] = True
    
    # Calculate end time
    end_time = datetime.datetime.now() + datetime.timedelta(seconds=total_seconds)
    
    # Initial response with countdown
    embed = discord.Embed(
        title="🐉 World Boss Timer Started!",
        description=f"⏰ **Countdown: {hours}h {minutes}m**\n📅 **Ends at:** {end_time.strftime('%H:%M:%S')}",
        color=0xff6b35
    )
    embed.add_field(name="⚔️ Get Ready!", value="I'll notify @everyone when it's time!", inline=False)
    
    # Send initial message
    await interaction.response.send_message(embed=embed)
    # Get the message object to edit
    message = await interaction.original_response()
    
    # Track this timer in the active_timers dictionary
    timer_data = {"cancel": False}
    active_timers[interaction.channel_id] = timer_data
    
    # Main countdown loop
    while total_seconds > 0 and not timer_data["cancel"]:
        # Calculate time components
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        
        # Format time string
        time_str = f"{h:02d}:{m:02d}:{s:02d}"
        
        # Determine color based on remaining time
        if total_seconds <= 10:
            color = 0xff0000  # Red for final 10 seconds
        elif total_seconds <= 60:
            color = 0xff6600  # Orange for final minute
        elif total_seconds <= 300:
            color = 0xffaa00  # Yellow for final 5 minutes
        else:
            color = 0xff6b35  # Default orange
        
        # Create updated embed
        update_embed = discord.Embed(
            title="🐉 World Boss Timer",
            description=f"⏰ **Time Remaining: {time_str}**\n📅 **Ends at:** {end_time.strftime('%H:%M:%S')}",
            color=color
        )
        
        # Add appropriate field based on remaining time
        if total_seconds <= 10:
            update_embed.add_field(name="🚨 FINAL COUNTDOWN!", value=f"**{total_seconds}** seconds left!", inline=False)
        elif total_seconds <= 60:
            update_embed.add_field(name="🚨 ALMOST TIME!", value="Get ready for battle!", inline=False)
        elif total_seconds <= 300:
            update_embed.add_field(name="⚡ 5 MINUTES LEFT!", value="Prepare your gear and gather your team!", inline=False)
        else:
            update_embed.add_field(name="⚔️ Get Ready!", value="Prepare your gear and gather your team!", inline=False)
        
        # Update the message
        try:
            await message.edit(embed=update_embed)
        except Exception as e:
            print(f"Update error (may be rate limit, continuing): {e}")
        
        # Wait 1 second
        await asyncio.sleep(1)
        total_seconds -= 1
    
    # If not cancelled, send final alert
    if not timer_data["cancel"]:
        try:
            await interaction.followup.send("🐉 **WORLD BOSS TIME!** @everyone\nPrepare for world boss @everyone")
        except discord.Forbidden:
            # Fallback message if @everyone mention fails
            await interaction.followup.send("🐉 **WORLD BOSS TIME!**\n(Note: I don't have permission to mention everyone. Please notify your team manually.)")
        except Exception as e:
            print(f"Error sending final notification: {e}")
            await interaction.followup.send("🐉 **WORLD BOSS TIME!**\n(There was an error with the notification. Please notify your team.)")
    else:
        await interaction.followup.send("🛑 World Boss timer was stopped.")
    
    # Clean up the timer from active_timers dictionary
    if interaction.channel_id in active_timers:
        del active_timers[interaction.channel_id] 

        # Update strategy 
# Command to stop the world boss timer
@bot.tree.command(name="wbstop", description="Stop the current StrangersAlert world boss timer")
async def wbstop(interaction: discord.Interaction):
    # Check if command is used in a server (not DM)
    if interaction.guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server, not in DMs!", ephemeral=True)
        return
    
    # Check if there's an active timer in this channel
    if interaction.channel_id in active_timers:
        # Cancel the timer
        active_timers[interaction.channel_id]["cancel"] = True
        
        # Create a confirmation embed
        embed = discord.Embed(
            title="🛑 Timer Stopped",
            description="The world boss timer has been cancelled.",
            color=0xff0000
        )
        embed.add_field(name="Status", value="✅ Successfully stopped", inline=False)
        
        await interaction.response.send_message(embed=embed)
    else:
        # No active timer found
        embed = discord.Embed(
            title="❌ No Active Timer",
            description="There is no active world boss timer in this channel.",
            color=0xff6600
        )
        embed.add_field(name="Tip", value="Use `/wb <duration>` to start a new timer", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(TOKEN)
