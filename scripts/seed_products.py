import asyncio
from database.session import AsyncSessionLocal
from database.models.product import Product
from database.repositories.product_repository import ProductRepository

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
        repo = ProductRepository(session)
        for category_id, products in PRODUCTS.items():
            for product_name in products:
                existing = await repo.get_by_name_in_category(product_name, category_id)
                if not existing:
                    await repo.create(Product(name=product_name, category_id=category_id))
        print("Products Seeded Successfully")

if __name__ == "__main__":
    asyncio.run(main())