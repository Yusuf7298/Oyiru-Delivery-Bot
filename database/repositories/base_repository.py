from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    async def add(self, obj):
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj
    async def delete(self, obj):
        await self.session.delete(obj)
        await self.session.commit()
    async def commit(self):
        await self.session.commit()
    async def refresh(self, obj):
        await self.session.refresh(obj)
    async def get_by_id(self, model, obj_id):
        return await self.session.get(model, obj_id)
    async def get_all(self, model):
        result = await self.session.execute(
            select(model)
        )
        return result.scalars().all()