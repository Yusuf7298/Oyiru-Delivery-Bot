import os
from motor.motor_asyncio import AsyncIOMotorClient
from config import DATABASE_URL

mongo_uri = DATABASE_URL or "mongodb://localhost:27017"
db_name = os.getenv("MONGODB_DB_NAME", "oyiru_delivery_bot")

client: AsyncIOMotorClient = AsyncIOMotorClient(mongo_uri)
db = client[db_name]

class AsyncSessionContext:
    def __init__(self, database):
        self.db = database
    async def __aenter__(self):
        return self.db
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

def AsyncSessionLocal():
    return AsyncSessionContext(db)

async def get_db():
    yield db

async def get_next_sequence_value(sequence_name: str) -> int:
    doc = await db["counters"].find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return doc["sequence_value"]