import aiosqlite
import asyncio
import os

DB_PATH = "database/bot.db"

async def init_db():
    os.makedirs("database", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        # Points
        await db.execute("""
        CREATE TABLE IF NOT EXISTS points (
            user_id INTEGER PRIMARY KEY,
            points INTEGER DEFAULT 0
        )
        """)
        # Tickets
        await db.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            channel_id INTEGER,
            ticket_type TEXT,
            status TEXT DEFAULT 'open'
        )
        """)
        # Configs
        await db.execute("""
        CREATE TABLE IF NOT EXISTS configs (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        await db.commit()
        print("Database initialized!")

if __name__ == "__main__":
    asyncio.run(init_db())
