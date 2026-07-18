
import asyncio
from database.session import AsyncSessionLocal
from database.models.product import Product
PRODUCTS = {
    1: [
        "Banana",
        "Apple",
        "Orange",
        "Avocado",
        "Mango",
    ],

    2: [
        "Tomato",
        "Onion",
        "Potato",
        "Carrot",
        "Cabbage",
    ],

    3: [
        "Garlic",
        "Pepper",
        "Turmeric",
        "Ginger",
    ],

    4: [
        "Rice",
        "Sugar",
        "Flour",
    ],

    5: [
        "Wheat",
        "Maize",
    ],

    6: [
        "Soap",
        "Tissue",
        "Plastic Bag",
    ],
}
async def main():
    async with AsyncSessionLocal() as session:
        for category_id, products in PRODUCTS.items():
            for product in products:
                session.add(Product(name=product,category_id=category_id,))
        await session.commit()
        print("✅ Products Seeded")
asyncio.run(main())