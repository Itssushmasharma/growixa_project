import asyncio
import sys
import asyncpg
from alembic.config import Config
from alembic import command
import os

async def create_database():
    print("[1/3] Connecting to PostgreSQL cluster at 127.0.0.1:5433...")
    conn = await asyncpg.connect(user="growixa", host="127.0.0.1", port=5433, database="postgres")
    exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'growixa'")
    if not exists:
        await conn.execute("CREATE DATABASE growixa")
        print("[+] Created database 'growixa'.")
    else:
        print("[*] Database 'growixa' already exists.")
    await conn.close()

def run_migrations():
    print("[2/3] Running Alembic migrations...")
    ini_path = os.path.join(os.path.dirname(__file__), "..", "apps", "api", "alembic.ini")
    alembic_cfg = Config(ini_path)
    # Ensure DATABASE_URL is set in environment for alembic env.py
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://growixa@127.0.0.1:5433/growixa"
    command.upgrade(alembic_cfg, "head")
    print("[+] Alembic migrations completed successfully.")

if __name__ == "__main__":
    asyncio.run(create_database())
    run_migrations()
