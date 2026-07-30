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
)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session