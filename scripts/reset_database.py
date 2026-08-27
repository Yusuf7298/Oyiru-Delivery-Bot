import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.session import db
from database.repositories.hotel_repository import HotelRepository
from database.repositories.category_repository import CategoryRepository
from database.repositories.product_repository import ProductRepository
from database.repositories.settings_repository import SettingsRepository
from database.models.hotel import Hotel
from database.models.category import Category
from database.models.product import Product

HOTELS = [
    "Skylight Hotel",
    "Hilton Addis",
    "Harmony Hotel",
    "Capital Hotel",
    "Inter Luxury",
    "Best Western"
]

CATEGORIES = [
    "Vegetables",
    "Fruits",
    "Dry Foods",
    "Meat & Poultry",
    "Dairy",
    "Bakery & Pastry"
]

PRODUCTS = {
    "Vegetables": [
        ("Potato", "KG"), ("Onion", "KG"), ("Tomato", "KG"),
        ("Carrot", "KG"), ("Cabbage", "KG")
    ],
    "Fruits": [
        ("Apple", "KG"), ("Banana", "KG"), ("Orange", "KG"),
        ("Avocado", "KG"), ("Watermelon", "KG")
    ],
    "Dry Foods": [
        ("Rice", "KG"), ("Sugar", "KG"), ("Flour", "KG"),
        ("Pasta", "KG"), ("Lentils", "KG")
    ],
    "Meat & Poultry": [
        ("Beef", "KG"), ("Chicken", "KG"), ("Minced Meat", "KG")
    ],
    "Dairy": [
        ("Milk", "L"), ("Butter", "KG"), ("Cheese", "KG")
    ],
    "Bakery & Pastry": [
        ("Bread", "Pcs")
    ]
}

async def reset_database():
    print("1. Dropping existing collections...")
    collections = [
        "users", "hotels", "categories", "products",
        "orders", "order_items", "returned_items",
        "counters", "system_settings"
    ]
    for col in collections:
        await db[col].drop()
        print(f"   - Dropped collection: {col}")

    print("\n2. Seeding Hotels...")
    hotel_repo = HotelRepository(db)
    for name in HOTELS:
        h = await hotel_repo.create(Hotel(name=name, address="Addis Ababa, Ethiopia", is_active=True))
        print(f"   + Hotel: {name} (ID: {h.id})")

    print("\n3. Seeding Categories...")
    cat_repo = CategoryRepository(db)
    cat_map = {}
    for cname in CATEGORIES:
        c = await cat_repo.create(Category(name=cname, description=f"Fresh {cname}", is_active=True))
        cat_map[cname] = c.id
        print(f"   + Category: {cname} (ID: {c.id})")

    print("\n4. Seeding Products...")
    prod_repo = ProductRepository(db)
    total_prods = 0
    for cname, plist in PRODUCTS.items():
        cid = cat_map.get(cname)
        for pname, punit in plist:
            await prod_repo.create(Product(name=pname, category_id=cid, unit=punit, is_active=True))
            total_prods += 1
            print(f"   + Product: {pname} ({punit}) under {cname}")

    print("\n5. Initializing Dynamic Support Contact...")
    settings_repo = SettingsRepository(db)
    support = await settings_repo.reset_support_contact()
    print("   + Support Settings initialized:", support.get("phone"), support.get("email"))

    print(f"\n[OK] DATABASE RESET COMPLETE! ({len(HOTELS)} hotels, {len(CATEGORIES)} categories, {total_prods} products seeded)")

if __name__ == "__main__":
    asyncio.run(reset_database())
