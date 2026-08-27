import asyncio
import asyncpg
import os
from dotenv import load_dotenv
load_dotenv()
DSN = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
async def reset():
    conn = await asyncpg.connect(dsn=DSN)
    try:
        tables = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
        if tables:
            names = ", ".join(f'"{r["tablename"]}"' for r in tables)
            await conn.execute(f"DROP TABLE IF EXISTS {names} CASCADE")
            print(f"Dropped {len(tables)} tables: {', '.join(r['tablename'] for r in tables)}")
        else:
            print("No tables to drop.")
        types = await conn.fetch(
            "SELECT typname FROM pg_type "
            "WHERE typtype = 'e' "
            "AND typnamespace = ("
            "  SELECT oid FROM pg_namespace WHERE nspname = 'public'"
            ")"
        )
        for t in types:
            await conn.execute(f'DROP TYPE IF EXISTS "{t["typname"]}" CASCADE')
            print(f"Dropped enum type: {t['typname']}")

        print("\nDatabase fully reset. Run: python -m alembic upgrade head")
    finally:
        await conn.close()

asyncio.run(reset())
