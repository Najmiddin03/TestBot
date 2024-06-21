from aiogram.utils import executor

from db.config import *
from functions import setup_teacher_handlers

setup_teacher_handlers(dp)

# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
