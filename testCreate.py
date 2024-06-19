import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import asyncio

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
BOT_TOKEN = '6029491691:AAFchAuoZT3OVTy4aSI_6ntVSnI7JxVaGWk'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

#Global variables
# testID=None
# ownerID=None
# subjectID=None
# questions_count=1
answers = []

# Define states
class Form(StatesGroup):
    waiting_for_custom_question_count = State()

# Handler for the /create command
@dp.message_handler(commands=['create'])
async def choose_subject(message: Message):
    # Inline keyboard for subjects
    ikb_subjects = InlineKeyboardMarkup(row_width=1)
    ikb_subjects.add(
        InlineKeyboardButton(text="Matematika", callback_data='sub_math'),
        InlineKeyboardButton(text="Ingliz tili", callback_data='sub_eng'),
        InlineKeyboardButton(text="Fizika", callback_data='sub_phy'),
        InlineKeyboardButton(text="Adabiyot", callback_data='sub_lit')
    )
    await message.reply("📚 Iltimos quyidagi fanlardan birini tanlang:", reply_markup=ikb_subjects)

# Callback query handler for subjects
@dp.callback_query_handler(lambda query: query.data.startswith('sub_'))
async def choose_question_count(callback_query: types.CallbackQuery):
    subject_id = {
        'math': 1,
        'eng': 2,
        'phy': 3,
        'lit': 4,
    }[callback_query.data.split('_')[1]]
    ownerID=callback_query.from_user.id
    subjectID=subject_id

    user_id = callback_query.from_user.id
    # Delete the previous message
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

    # Inline keyboard for number of questions
    ikb_question_count = InlineKeyboardMarkup(row_width=3)
    options = [5, 10, 15, 20, 25, 30]
    buttons = [InlineKeyboardButton(text=str(option), callback_data=f'count_{option}') for option in options]

    # Add the custom button
    custom_button = InlineKeyboardButton(text="Custom", callback_data='count_custom')
    buttons.append(custom_button)

    for i in range(0, len(buttons), 3):
        ikb_question_count.row(*buttons[i:i + 3])

    await bot.send_message(callback_query.from_user.id, "How many questions?", reply_markup=ikb_question_count)

# Callback query handler for question count
@dp.callback_query_handler(lambda query: query.data.startswith('count_'))
async def ask_custom_question_count(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data.split('_')[1] == 'custom':
        await Form.waiting_for_custom_question_count.set()
        # Delete the previous message
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
        await bot.send_message(callback_query.from_user.id, "Iltimos test savollari sonini o'zingiz kiriting. Test savollar miqdori 100 tadan oshmasligi kerak:")
    else:
        questions_amount = int(callback_query.data.split('_')[1])  # Extract question count from callback_data
        # Delete the previous message
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

        user_id = callback_query.from_user.id
        await give_answers(questions_amount, user_id)
        #await bot.send_message(user_id, f"Test created with {questions_amount} questions. Would you like to save this test?")

# Handler to receive custom question count
@dp.message_handler(state=Form.waiting_for_custom_question_count)
async def receive_custom_question_count(message: types.Message, state: FSMContext):
    try:
        questions_amount = int(message.text)
        if questions_amount > 100:
            await message.reply("Savollar miqdori 100 tadan oshmasligi kerak. Qayta urinib ko'ring.")
            return
        user_id = message.from_user.id
        await state.finish()
        #await message.reply(f"Test created with {questions_amount} questions. Would you like to save this test?")
        await give_answers(questions_amount,user_id)
    except ValueError:
        await message.reply("Iltimos, to'g'ri son kiriting.")


async def give_answers(questions_amount, user_id):
    options = ['A', 'B', 'C', 'D', 'E']
    responses = {}  # Dictionary to store user responses for each question

    for i in range(1, questions_amount + 1):
        # Inline keyboard for each question
        ikb_answers = InlineKeyboardMarkup(row_width=5)
        buttons = [InlineKeyboardButton(text=str(option), callback_data=f'variant_{option}_{i}') for option in options]
        ikb_answers.add(*buttons)

        # Send question with answer options
        message = await bot.send_message(user_id, f"{i}-savol uchun javobingizni tanlang:", reply_markup=ikb_answers)

        # Wait for user's response
        while True:
            response = await dp.current_state().get_state()

            if response:
                callback_data = response.split('_')

                if callback_data[0] == 'variant' and int(callback_data[2]) == i:
                    responses[i] = callback_data[1]
                    await bot.edit_message_text(chat_id=user_id, message_id=message.message_id,
                                                text=f"{i}-savol uchun javobingiz: {callback_data[1]}")
                    break
            else:
                await asyncio.sleep(1)  # Wait and try again if no response yet

        await asyncio.sleep(1)  # Optional delay before sending the next question

    # After all questions are answered, send final message
    await bot.send_message(user_id,
                           f"Test completed with {questions_amount} questions. Would you like to save this test?")

    # Optionally, return the responses for further processing if needed
    return responses


# async def give_answers(questions_amount, user_id):
#     # Inline keyboard for variants
#     ikb_answers = InlineKeyboardMarkup(row_width=5)
#     options = ['A', 'B', 'C', 'D', 'E']
#     buttons = [InlineKeyboardButton(text=str(option), callback_data=f'variant_{option}') for option in options]
#     ikb_answers.add(*buttons)
#
#     for i in range(1, questions_amount + 1):
#         await bot.send_message(user_id, f"{i}-savol uchun javobingizni kiriting:",reply_markup=ikb_answers)
#     await bot.send_message(chat_id=user_id,text=f"Test created with {questions_amount} questions. Would you like to save this test?")


# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
