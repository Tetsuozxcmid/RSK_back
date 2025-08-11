from aiogram import Router, types
from aiogram.filters import CommandStart
from config import settings
from admin_config import settings as admin_settings
router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    if message.from_user.id not in admin_settings.admin_ids_list:  
        await message.answer("Доступ запрещен")
        return
    
    await message.answer("Доступ разрешен")