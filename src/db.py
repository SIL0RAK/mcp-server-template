import asyncpg
import os

MIGRATIONS_FOLDER = os.path.join(os.path.dirname(__file__), '../migrations')
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://user:password@localhost:5432/mydb"
)

_pool: asyncpg.Pool | None = None

async def init_db():
    try:
        pool = await asyncpg.create_pool(DATABASE_URL, max_size=10)
        print ("Connected to database")
        return pool
    except Exception as e:
        print(f"⚠️ Warning: Failed to connect to database: {e}") 
    return None

async def get_db():
    global _pool
    if _pool is None:
        _pool = await init_db()
    return _pool


async def run_migrations():
    pool = await init_db()
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

    # Apply migrations one by one, each in its own connection
    for filename in sorted(os.listdir(MIGRATIONS_FOLDER)):
        if filename.endswith(".sql") and filename not in applied:
            path = os.path.join(MIGRATIONS_FOLDER, filename)
            sql = open(path).read()
            async with pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(sql)
                    await conn.execute(
                        "INSERT INTO migrations (filename) VALUES ($1)", filename
                    )
                    print(f"Applied migration: {filename}")

    await pool.close()
