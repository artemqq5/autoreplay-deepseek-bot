import logging

from aiogram import Router
from aiogram.types import BusinessConnection

from bot.data.repository.AdminRepository import AdminRepository
from bot.domain.middleware.AdminBusinessMiddleware import AdminBusinessMiddleware

router = Router()

router.business_connection.middleware(AdminBusinessMiddleware())


@router.business_connection()
async def handle_business_con(business_connection: BusinessConnection):
    # logging.info(business_connection)
    result = await AdminRepository().update_business_id(business_id=business_connection.id, user_id=business_connection.user_chat_id)
    logging.info(f"Status update admin business_id: {result}")
