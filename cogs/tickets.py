import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite

DB_PATH = "database/bot.db"

TICKET_TYPES = [
    "UltraSpeaker Express",
    "Ultra Gramiel Express",
    "Daily 4-Man Express",
    "Daily 7-Man Express",
    "Weekly Ultra Express",
    "GrimChallenge Express",
    "Daily Temple Express"
]

class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent buttons

        for ticket in TICKET_TYPES:
            self.add_item(discord.ui.Button(label=ticket, style=discord.ButtonStyle.primary, custom_id=f"ticket_{ticket}"))

    @discord.ui.button(label="Test", style=discord.ButtonStyle.green, custom_id="dummy_button")
    async def dummy(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass  # Placeholder for class init

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Optional: you can restrict who can press buttons
        return True

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

    @app_commands.command(name="panel", description="Post the in-game assistance ticket panel")
    async def panel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("You can't do this!", ephemeral=True)

        embed = discord.Embed(
            title="🎮 IN-GAME ASSISTANCE 🎮",
            description=(
                "CHOOSE YOUR TICKET TYPE🚂 💨\n"
                "Pick the ticket type that fits your request📜\n"
                "⁠🎫📄︱𝙏𝙞𝙘𝙠𝙚𝙩-𝘿𝙚𝙨𝙘𝙧𝙞𝙥𝙩𝙞𝙤𝙣𝙨…\n"
                "------------------------------------------------------------\n"
                "UltraSpeaker Express — The First Speaker\n"
                "Ultra Gramiel Express — Ultra Gramiel\n"
                "Daily 4-Man Express — Daily 4-Man Ultra Bosses\n"
                "Daily 7-Man Express — Daily 7-Man Ultra Bosses\n"
                "Weekly Ultra Express — Weekly Ultra Bosses (excluding speaker, grim and gramiel)\n"
                "GrimChallenge Express — Mechabinky & Raxborg 2.0\n"
                "Daily Temple Express — Daily TempleShrine\n"
                "-----------------------------------------------------------\n"
                "How it works📢\n"
                "✅ Select a \"ticket type\"\n"
                "📝 Fill out the form\n"
                "💁 Helpers join\n"
                "🎉 Get help in your private ticket"
            ),
            color=discord.Color.blue()
        )

        view = TicketButton()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        custom_id = interaction.data.get("custom_id")
        if custom_id and custom_id.startswith("ticket_"):
            ticket_type = custom_id.replace("ticket_", "")
            guild = interaction.guild
            member = interaction.user

            # Optional: Get parent category from your config table
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute("SELECT value FROM configs WHERE key='ticket_category'")
                row = await cursor.fetchone()
                category = guild.get_channel(int(row[0])) if row else None

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{member.name}",
                category=category,
                overwrites=overwrites
            )

            await self.add_ticket(member.id, ticket_channel.id, ticket_type)
            await ticket_channel.send(f"{member.mention}, your ticket **{ticket_type}** has been created!")
            await interaction.response.send_message(f"Ticket created: {ticket_channel.mention}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Tickets(bot))
