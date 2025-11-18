import discord
from discord.ext import commands
import os
import asyncio
from database.init_db import init_db
from dotenv import load_dotenv
from flask import Flask
import threading

# ---------------- Environment ----------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ---------------- Database ----------------
asyncio.run(init_db())

# ---------------- Bot Setup ----------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Flask Health Check ----------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=3000)

threading.Thread(target=run_flask).start()

# ---------------- Cog Loading ----------------
COGS = ["cogs.tickets", "cogs.points", "cogs.setup"]

async def load_cogs():
    for cog in COGS:
        try:
            await bot.load_extension(cog)  # <-- fixed: await
            print(f"Loaded cog {cog}")
        except Exception as e:
            print(f"Failed to load cog {cog}: {e}")

# ---------------- On Ready ----------------
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# ---------------- Main Async Runner ----------------
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

# ---------------- Run Bot ----------------
asyncio.run(main())
