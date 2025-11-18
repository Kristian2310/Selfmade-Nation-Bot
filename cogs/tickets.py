import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite

DB_PATH = "database/bot.db"

TICKET_POINTS = {
    "Ultra Speaker Express": 8,
    "Ultra Gramiel Express": 7,
    "4-Man Ultra Daily Express": 4,
    "7-Man Ultra Daily Express": 10,
    "Ultra Weekly Express": 12,
    "Grim Express": 10,
    "Daily Temple Express": 6
}

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def add_ticket(self, user_id, channel_id, ticket_type):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO tickets (user_id, channel_id, ticket_type) VALUES (?, ?, ?)",
                (user_id, channel_id, ticket_type)
            )
            await db.commit()

    async def get_config(self, key: str):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT value FROM configs WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row[0] if row else None

    @app_commands.command(name="panel", description="Post ticket panel (Admin/Staff only)")
    async def panel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("You can't do this!", ephemeral=True)
        title = await self.get_config("panel_title") or "🎫 Support Tickets"
        color_hex = await self.get_config("panel_color") or "#00FF00"
        embed = discord.Embed(
            title=title,
            description="\n".join([f"**{k}** — {v} pts" for k,v in TICKET_POINTS.items()]),
            color=discord.Color(int(color_hex.replace("#",""),16))
        )
        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("🎟️")
        await interaction.response.send_message("Ticket panel posted!", ephemeral=True)

    @app_commands.command(name="verification_panel", description="Post verification panel (Admin only)")
    async def verification_panel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("You can't do this!", ephemeral=True)
        embed = discord.Embed(
            title="✅ Verification Panel",
            description="React with ✅ to verify yourself",
            color=discord.Color.blue()
        )
        message = await interaction.channel.send(embed=embed)
        await message.add_reaction("✅")
        await interaction.response.send_message("Verification panel posted!", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        channel = guild.get_channel(payload.channel_id)

        # Maintenance check
        maintenance = await self.get_config("maintenance_mode")
        if maintenance == "True":
            return

        if str(payload.emoji) == "🎟️":
            category_id = await self.get_config("ticket_category")
            category = guild.get_channel(int(category_id)) if category_id else None
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{member.name}",
                category=category,
                overwrites=overwrites
            )
            await ticket_channel.send(f"{member.mention}, your ticket has been created!")
            await self.add_ticket(member.id, ticket_channel.id, "Custom Ticket")

        if str(payload.emoji) == "✅":
            role_id = await self.get_config("role_verified")
            role = guild.get_role(int(role_id)) if role_id else None
            if role:
                await member.add_roles(role)
                await channel.send(f"{member.mention} has been verified!")

async def setup(bot):
    await bot.add_cog(Tickets(bot))
