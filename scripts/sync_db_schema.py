import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loguru import logger
from database.session import db, client

async def sync_database():
    logger.info('Starting MongoDB schema sync and migration...')
    
    # 1. Backfill default language for existing users
    result_lang = await db['users'].update_many(
        {'language': {'$exists': False}},
        {'$set': {'language': 'en'}}
    )
    logger.info(f'Synced user language field: {result_lang.modified_count} users updated.')

    # 2. Backfill is_active for users if missing
    result_active = await db['users'].update_many(
        {'is_active': {'$exists': False}},
        {'$set': {'is_active': True}}
    )
    logger.info(f'Synced user is_active field: {result_active.modified_count} users updated.')

    # 3. Create indexes
    logger.info('Ensuring database indexes...')
    
    # Users
    await db['users'].create_index('telegram_id', unique=True, sparse=True)
    await db['users'].create_index('hotel_id')
    await db['users'].create_index('role')
    logger.info('  ✅ users indexes verified.')

    # Orders
    await db['orders'].create_index('order_number', unique=True, sparse=True)
    await db['orders'].create_index('customer_id')
    await db['orders'].create_index('hotel_id')
    await db['orders'].create_index('driver_id')
    await db['orders'].create_index('status')
    await db['orders'].create_index('created_at')
    logger.info('  ✅ orders indexes verified.')

    # Products & Categories
    await db['products'].create_index('category_id')
    await db['products'].create_index('is_active')
    await db['categories'].create_index('is_active')
    await db['hotels'].create_index('is_active')
    logger.info('  ✅ products/categories/hotels indexes verified.')

    logger.info('🎉 Database sync and indexing completed successfully!')

if __name__ == '__main__':
    try:
        asyncio.run(sync_database())
    except Exception as e:
        logger.warning(f'Database connection warning during sync: {e}')
