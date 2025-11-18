import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite

DB_PATH = "database/bot.db"

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_points(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT points FROM points WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def set_points(self, user_id, points):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO points (user_id, points) VALUES (?, ?)", (user_id, points))
            await db.commit()

    @app_commands.command(name="points", description="Check someone's points")
    @app_commands.describe(user="User to check points")
    async def points(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        pts = await self.get_points(user.id)
        await interaction.response.send_message(f"{user.display_name} has {pts} points.")

    @app_commands.command(name="leaderboard", description="View top helpers")
    @app_commands.describe(page="Page number")
    async def leaderboard(self, interaction: discord.Interaction, page: int = 1):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT user_id, points FROM points ORDER BY points DESC LIMIT 10 OFFSET ?", ((page-1)*10,))
            rows = await cursor.fetchall()
            embed = discord.Embed(title="🏆 Leaderboard", color=discord.Color.gold())
            description = ""
            for i, row in enumerate(rows, start=1 + (page-1)*10):
                user = interaction.guild.get_member(row[0])
                description += f"**{i}. {user.display_name if user else 'Unknown'}** — {row[1]} pts\n"
            embed.description = description or "No data found."
            await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Points(bot))
