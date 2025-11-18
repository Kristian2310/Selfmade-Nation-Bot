import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite

DB_PATH = "database/bot.db"

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def set_config(self, key: str, value: str):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT OR REPLACE INTO configs (key, value) VALUES (?, ?)", (key, value))
            await db.commit()

    async def get_config(self, key: str):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT value FROM configs WHERE key = ?", (key,))
            row = await cursor.fetchone()
            return row[0] if row else None

    # ---------------- Roles ----------------
    @app_commands.command(name="setup_roles", description="Configure server roles")
    async def setup_roles(self, interaction: discord.Interaction, verified: discord.Role, staff: discord.Role):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("You need admin permissions.", ephemeral=True)
        await self.set_config("role_verified", str(verified.id))
        await self.set_config("role_staff", str(staff.id))
        await interaction.response.send_message(f"Roles saved: Verified={verified.name}, Staff={staff.name}", ephemeral=True)

    @app_commands.command(name="setup_roles_show", description="Show current roles")
    async def setup_roles_show(self, interaction: discord.Interaction):
        verified_id = await self.get_config("role_verified")
        staff_id = await self.get_config("role_staff")
        guild = interaction.guild
        verified_role = guild.get_role(int(verified_id)) if verified_id else None
        staff_role = guild.get_role(int(staff_id)) if staff_id else None
        await interaction.response.send_message(
            f"Verified role: {verified_role.name if verified_role else 'Not set'}\n"
            f"Staff role: {staff_role.name if staff_role else 'Not set'}",
            ephemeral=True
        )

    # ---------------- Ticket Category ----------------
    @app_commands.command(name="setup_ticket_category", description="Set parent category for tickets")
    async def setup_ticket_category(self, interaction: discord.Interaction, category: discord.CategoryChannel):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("Admin only.", ephemeral=True)
        await self.set_config("ticket_category", str(category.id))
        await interaction.response.send_message(f"Ticket category set to: {category.name}", ephemeral=True)

    @app_commands.command(name="setup_category_add", description="Add a ticket sub-category")
    async def setup_category_add(self, interaction: discord.Interaction, category_name: str):
        existing = await self.get_config("ticket_subcategories") or ""
        categories = existing.split(",") if existing else []
        if category_name in categories:
            return await interaction.response.send_message("Category already exists.", ephemeral=True)
        categories.append(category_name)
        await self.set_config("ticket_subcategories", ",".join(categories))
        await interaction.response.send_message(f"Added sub-category: {category_name}", ephemeral=True)

    @app_commands.command(name="setup_category_remove", description="Remove a ticket sub-category")
    async def setup_category_remove(self, interaction: discord.Interaction, category_name: str):
        existing = await self.get_config("ticket_subcategories") or ""
        categories = existing.split(",") if existing else []
        if category_name not in categories:
            return await interaction.response.send_message("Category not found.", ephemeral=True)
        categories.remove(category_name)
        await self.set_config("ticket_subcategories", ",".join(categories))
        await interaction.response.send_message(f"Removed sub-category: {category_name}", ephemeral=True)

    @app_commands.command(name="setup_category_list", description="List ticket sub-categories")
    async def setup_category_list(self, interaction: discord.Interaction):
        existing = await self.get_config("ticket_subcategories") or ""
        categories = existing.split(",") if existing else []
        await interaction.response.send_message(f"Sub-categories: {', '.join(categories) if categories else 'None'}", ephemeral=True)

    # ---------------- Panel ----------------
    @app_commands.command(name="setup_panel", description="Customize panel text/color")
    async def setup_panel(self, interaction: discord.Interaction, title: str = None, color: str = None):
        if title:
            await self.set_config("panel_title", title)
        if color:
            await self.set_config("panel_color", color)
        await interaction.response.send_message("Panel settings updated.", ephemeral=True)

    # ---------------- Transcript ----------------
    @app_commands.command(name="setup_transcript", description="Set transcript channel")
    async def setup_transcript(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.set_config("transcript_channel", str(channel.id))
        await interaction.response.send_message(f"Transcript channel set to {channel.name}", ephemeral=True)

    # ---------------- Audit ----------------
    @app_commands.command(name="setup_audit_channel", description="Set audit log channel")
    async def setup_audit_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await self.set_config("audit_channel", str(channel.id))
        await interaction.response.send_message(f"Audit log channel set to {channel.name}", ephemeral=True)

    # ---------------- Maintenance ----------------
    @app_commands.command(name="setup_maintenance", description="Toggle ticket availability")
    async def setup_maintenance(self, interaction: discord.Interaction, mode: bool):
        await self.set_config("maintenance_mode", str(mode))
        await interaction.response.send_message(f"Maintenance mode set to {mode}", ephemeral=True)

    # ---------------- Custom Commands ----------------
    @app_commands.command(name="custom_add", description="Add a custom slash command")
    async def custom_add(self, interaction: discord.Interaction, command_name: str, response_text: str):
        existing = await self.get_config("custom_commands") or ""
        commands_dict = dict([pair.split("::") for pair in existing.split("|") if pair])
        commands_dict[command_name] = response_text
        await self.set_config("custom_commands", "|".join([f"{k}::{v}" for k,v in commands_dict.items()]))
        await interaction.response.send_message(f"Custom command `{command_name}` added.", ephemeral=True)

    @app_commands.command(name="custom_remove", description="Remove a custom command")
    async def custom_remove(self, interaction: discord.Interaction, command_name: str):
        existing = await self.get_config("custom_commands") or ""
        commands_dict = dict([pair.split("::") for pair in existing.split("|") if pair])
        if command_name not in commands_dict:
            return await interaction.response.send_message("Command not found.", ephemeral=True)
        commands_dict.pop(command_name)
        await self.set_config("custom_commands", "|".join([f"{k}::{v}" for k,v in commands_dict.items()]))
        await interaction.response.send_message(f"Custom command `{command_name}` removed.", ephemeral=True)

    @app_commands.command(name="custom_list", description="List custom commands")
    async def custom_list(self, interaction: discord.Interaction):
        existing = await self.get_config("custom_commands") or ""
        commands_dict = dict([pair.split("::") for pair in existing.split("|") if pair])
        if not commands_dict:
            return await interaction.response.send_message("No custom commands.", ephemeral=True)
        await interaction.response.send_message("\n".join([f"{k}: {v}" for k,v in commands_dict.items()]), ephemeral=True)

async def setup(bot):
    await bot.add_cog(Setup(bot))
