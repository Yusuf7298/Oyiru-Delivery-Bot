import asyncio
from database.base import Base
from database.models import *
from database.session import engine
async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully.")
if __name__ == "__main__":
    asyncio.run(main())