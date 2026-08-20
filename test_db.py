import asyncio
from database.session import client, db

async def main():
    try:
        # Send a ping to confirm a successful connection
        res = await client.admin.command('ping')
        print("MongoDB Atlas Ping Result:", res)
        collections = await db.list_collection_names()
        print(f"Database '{db.name}' collections:", collections)
    except Exception as e:
        print("MongoDB connection error:", e)

if __name__ == "__main__":
    asyncio.run(main())