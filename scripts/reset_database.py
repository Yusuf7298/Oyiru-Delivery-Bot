import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config.settings import DATABASE_URL, MONGODB_DB_NAME

async def reset_db():
    print(f"Connecting to MongoDB database: {MONGODB_DB_NAME}")
    client = AsyncIOMotorClient(DATABASE_URL)
    db = client[MONGODB_DB_NAME]
    
    collections = await db.list_collection_names()
    print(f"Collections found: {collections}")
    
    for col in collections:
        await db[col].drop()
        print(f"Dropped collection: {col}")
        
    print("Database reset successfully completed.")
    client.close()

if __name__ == "__main__":
    asyncio.run(reset_db())
