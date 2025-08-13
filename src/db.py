import asyncpg
import os

MIGRATIONS_FOLDER = os.path.join(os.path.dirname(__file__), '../migrations')
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost:5432/mydb"
)

_pool: asyncpg.Pool | None = None

async def init_db():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool

async def get_db():
    if _pool is None:
        await init_db()
    return _pool


async def run_migrations():
    pool = await get_db()

    print("Running migrations...")

    async with pool.acquire() as conn:
        # Ensure migrations table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                filename TEXT UNIQUE,
                applied_at TIMESTAMP DEFAULT NOW()
            )
        """)
        # Get already applied migrations
        applied = {row['filename'] for row in await conn.fetch("SELECT filename FROM migrations")}

        # Apply pending migrations
        for filename in sorted(os.listdir(MIGRATIONS_FOLDER)):
            if filename.endswith(".sql") and filename not in applied:
                path = os.path.join(MIGRATIONS_FOLDER, filename)
                sql = open(path).read()
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO migrations (filename) VALUES ($1)", filename
                )
                print(f"Applied migration: {filename}")