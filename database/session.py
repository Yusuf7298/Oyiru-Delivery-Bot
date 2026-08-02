import os
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL, # type: ignore
    echo=os.getenv("DEV_MODE", "false").lower() == "true",  # SQL logging only in dev
    future=True,
    pool_pre_ping=True,   # Re-connects automatically if Neon DB drops idle connections
    pool_recycle=300,    # Recycles connections every 5 minutes
    pool_timeout=30,
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session