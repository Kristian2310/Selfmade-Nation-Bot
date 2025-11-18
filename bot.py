import discord
from discord.ext import commands
import os
import asyncio
from database.init_db import init_db
from dotenv import load_dotenv
from flask import Flask
import threading

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Initialize database
asyncio.run(init_db())

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Health check for Render
app = Flask("")
@app.route("/")
def home():
    return "Bot is running!"
def run():
    app.run(host="0.0.0.0", port=3000)
threading.Thread(target=run).start()

# On ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# Load cogs
for cog in ["cogs.tickets", "cogs.points", "cogs.setup"]:
    try:
        bot.load_extension(cog)
        print(f"Loaded cog {cog}")
    except Exception as e:
        print(f"Failed to load cog {cog}: {e}")

bot.run(TOKEN)
