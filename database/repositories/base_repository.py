from typing import TypeVar, Type, List, Optional, Any
from database.session import get_next_sequence_value

T = TypeVar("T")

MODEL_COLLECTION_MAP = {
    "User": "users",
    "Hotel": "hotels",
    "Category": "categories",
    "Product": "products",
    "Order": "orders",
    "OrderItem": "order_items",
    "DeliveryPartner": "delivery_partners",
    "ReturnedItem": "returned_items"
}

def get_collection_name(model_or_obj: Any) -> str:
    name = model_or_obj.__name__ if isinstance(model_or_obj, type) else model_or_obj.__class__.__name__
    return MODEL_COLLECTION_MAP.get(name, f"{name.lower()}s")

class BaseRepository:
    def __init__(self, session: Any):
        self.session = session
        self.db = session

    async def add(self, obj: Any) -> Any:
        col_name = get_collection_name(obj)
        if not getattr(obj, "id", None):
            obj.id = await get_next_sequence_value(col_name)
        doc = obj.to_dict()
        doc["_id"] = obj.id
        await self.db[col_name].update_one(
            {"_id": obj.id},
            {"$set": doc},
            upsert=True
        )
        return obj

    async def delete(self, obj: Any) -> None:
        col_name = get_collection_name(obj)
        obj_id = getattr(obj, "id", None)
        if obj_id is not None:
            await self.db[col_name].delete_one({"_id": obj_id})

    async def commit(self) -> None:
        pass

    async def refresh(self, obj: Any) -> Any:
        col_name = get_collection_name(obj)
        obj_id = getattr(obj, "id", None)
        if obj_id is not None:
            doc = await self.db[col_name].find_one({"_id": obj_id})
            if doc and hasattr(obj.__class__, "from_dict"):
                refreshed = obj.__class__.from_dict(doc)
                for k, v in refreshed.__dict__.items():
                    setattr(obj, k, v)
        return obj

    async def get_by_id(self, model: Type[T], obj_id: Any) -> Optional[T]:
        col_name = get_collection_name(model)
        doc = await self.db[col_name].find_one({"_id": obj_id})
        if doc and hasattr(model, "from_dict"):
            return model.from_dict(doc)
        return None

    async def get_all(self, model: Type[T]) -> List[T]:
        col_name = get_collection_name(model)
        cursor = self.db[col_name].find({})
        items = []
        async for doc in cursor:
            if hasattr(model, "from_dict"):
                items.append(model.from_dict(doc))
        return items