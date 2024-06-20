import asyncio
import os

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from data.config import *
from db import requests as db
import logging

API_TOKEN = 'YOUR_API_TOKEN'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
router = Router()

userData = {}
LOGS_CHANNEL = 'YOUR_LOGS_CHANNEL_ID'
LOGS_CHANNEL = os.getenv("LOGS_CHANNEL")


@router.callback_query(F.data.startswith("role:"))
async def get_role(call: CallbackQuery):
    try:
        role = call.data.split(":")[1]
        userData['role'] = 1 if role == "O'qituvchi" else 2
        await call.message.answer("Ism familiyangizni kiriting, masalan <i>Alijon Valiyev</i>: ", parse_mode="HTML")
    except Exception as e:
        await bot.send_message(LOGS_CHANNEL, f"Error in get_role() handler: {e}")


@router.message(F.text)
async def get_name(message: Message):
    try:
        name = message.text
        userData['name'] = name
        keyboard = InlineKeyboardMarkup()
        for region in regions:
            button = InlineKeyboardButton(text=region, callback_data="region:" + region)
            keyboard.add(button)
        await message.answer("Qaysi viloyatdansiz?", reply_markup=keyboard)
    except Exception as e:
        await bot.send_message(LOGS_CHANNEL, f"Error in get_name() handler: {e}")


@router.callback_query(F.data.startswith("region:"))
async def region_handler(call: CallbackQuery):
    try:
        selected_region = call.data.split(":")[1]
        userData['region'] = selected_region
        await call.message.edit_text(f"Demak siz yashaydigan viloyat: {selected_region}")

        districts = regions.get(selected_region)
        if districts:
            keyboard = InlineKeyboardMarkup()
            for district in districts:
                button = InlineKeyboardButton(text=district, callback_data="district:" + district)
                keyboard.add(button)
            await call.message.answer("Tumaningizni tanlang:", reply_markup=keyboard)
        else:
            await call.message.answer("Bu viloyat uchun tuman ma'lumotlari mavjud emas.")
    except Exception as e:
        await bot.send_message(LOGS_CHANNEL, f"Error in region_handler() handler: {e}")


@router.callback_query(F.data.startswith("district:"))
async def district_handler(call: CallbackQuery):
    try:
        selected_district = call.data.split(":")[1]
        userData['district'] = selected_district
        await call.message.edit_text(f"Demak sizning tumaningiz: {selected_district}")
        await call.message.answer("Maktabingizni kiriting, masalan 5-maktab: ")
    except Exception as e:
        await bot.send_message(LOGS_CHANNEL, f"Error in district_handler() handler: {e}")


@router.message(F.text)
async def get_school(message: Message):
    try:
        school = message.text
        userData['school'] = school
        joined_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        await db.register_user(message, message.chat.id, userData['name'], userData['region'], userData['district'],
                               userData['school'], userData['role'], joined_at)
        userData.clear()
        # Finish the registration
        await bot.delete_state(user=message.from_user.id)
        await message.answer("Ro'yxatdan muvaffaqiyatli o'tdingiz!")
    except Exception as e:
        await bot.send_message(LOGS_CHANNEL, f"Error in get_school() handler: {e}")


# if __name__ == '__main__':
#     dp.include_router(router)
#     executor.start_polling(dp, skip_updates=True)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')