import logging
import sys
import asyncio

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher

from config import *
from functions.common import router as common_router
from functions.teacher import router as teacher_router
from functions.registration import router as registration_router
from functions.student import router as student_router
from db.models import init_models


async def main() -> None:
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(common_router)
    dp.include_router(registration_router)
    dp.include_router(teacher_router)
    dp.include_router(student_router)

    # await init_models()
    await dp.start_polling(bot)



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())