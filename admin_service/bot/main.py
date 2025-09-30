import asyncio
import logging
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
import httpx

from config import settings  
from admin_config import settings as admin_settings  


app = FastAPI()
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@app.post("/team-requests")
async def handle_team_request(request: Request):
    try:
        data = await request.json()
        required_fields = ["leader_id", "team_name", "org_name"]
        if not all(field in data for field in required_fields):
            raise HTTPException(status_code=400, detail="Missing required fields")

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Approve",
                        callback_data=f"approve:{data['team_name']}:{data['org_name']}:{data['leader_id']}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Reject",
                        callback_data=f"reject:{data['team_name']}"
                    )
                ]
            ]
        )

        errors = []
        for admin_id in admin_settings.admin_ids:
            try:
                await bot.send_message(
                    chat_id=int(admin_id),
                    text=f"🆕 Запрос на добавление команды:\n"
                         f"👤 User ID: {data['leader_id']}\n"
                         f"🏷 Team: {data['team_name']}\n"
                         f"🏢 Org: {data['org_name']}",
                    reply_markup=keyboard
                )
            except Exception as e:
                logging.error(f"Failed to send message to admin {admin_id}: {str(e)}")
                errors.append(f"{admin_id}: {str(e)}")

        if errors:
            return {"status": "partial_success", "errors": errors}

        return {"status": "success"}

    except Exception as e:
        logging.error(f"Error in handle_team_request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@dp.callback_query(lambda c: c.data.startswith("approve:"))
async def approve_team_request(callback: CallbackQuery):
    try:
        _, team_name, org_name, leader_id = callback.data.split(":")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{admin_settings.RSK_ORGS_URL}/organizations/create/",
                json={"name": org_name},
                headers={"X-Admin-Token": admin_settings.ADMIN_SECRET_KEY},
                timeout=10.0
            )
            if resp.status_code not in (200, 201):
                raise Exception(f"Organization creation failed: {resp.text}")

        await callback.message.edit_text("✅ Одобрено администратором")
        await callback.message.reply("Организация добавлена в БД")

    except Exception as e:
        logging.error(f"Error in approve_team_request: {str(e)}")
        await callback.answer("❌ Ошибка при обработке запроса")
        await callback.message.reply("Произошла ошибка при обработке вашего запроса")

@dp.callback_query(lambda c: c.data.startswith("reject:"))
async def reject_team_request(callback: CallbackQuery):
    try:
        _, team_name = callback.data.split(":")
        await callback.answer("❌ Запрос отклонен")
        await callback.message.edit_text(
            f"{callback.message.text}\n\n❌ Отклонено администратором",
            reply_markup=None
        )
    except Exception as e:
        logging.error(f"Error in reject_team_request: {str(e)}")
        await callback.answer("❌ Ошибка при обработке запроса")

@dp.message(Command("chat_id"))
async def cmd_chat_id(message):
    await message.reply(f"Ваш ID: {message.chat.id}, Тип чата: {message.chat.type}")

async def run_api():
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=8009, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def run_bot():
    await dp.start_polling(bot)

async def main():
    await asyncio.gather(run_api(), run_bot())

if __name__ == "__main__":
    asyncio.run(main())

