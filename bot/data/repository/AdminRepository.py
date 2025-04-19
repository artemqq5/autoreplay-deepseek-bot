from sqlalchemy import select, update

from bot.data.BaseRepository import BaseRepository
from bot.data.sqlmodels import AdminsModel


class AdminRepository(BaseRepository[AdminsModel]):

    async def admin(self, user_id):
        query = select(AdminsModel).where(AdminsModel.user_id == user_id).limit(1)
        return await self._select(query)

    async def admin_by_business_id(self, business_id):
        query = select(AdminsModel).where(AdminsModel.business_id == business_id).limit(1)
        return await self._select(query)

    async def update_business_id(self, user_id, business_id):
        query = update(AdminsModel).values(business_id=business_id).where(AdminsModel.user_id == user_id)
        return await self._update(query)
