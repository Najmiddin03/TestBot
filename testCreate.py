import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from db import requests

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
correct_answers = []
testData = {}


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
    ownerID = callback_query.from_user.id
    subjectID = subject_id

    user_id = callback_query.from_user.id
    # Delete the previous message
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    subjectID=requests.get_subject_id()
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
        await bot.send_message(callback_query.from_user.id,
                               "Iltimos test savollari sonini o'zingiz kiriting. Test savollar miqdori 100 tadan "
                               "oshmasligi kerak:")
    else:
        questions_amount = int(callback_query.data.split('_')[1])  # Extract question count from callback_data
        # Delete the previous message
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)

        user_id = callback_query.from_user.id
        await process_question_creation(callback_query.message, questions_amount, 1)
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
        # await message.reply(f"Test created with {questions_amount} questions. Would you like to save this test?")
        await process_question_creation(message, questions_amount, 1)
    except ValueError:
        await message.reply("Iltimos, to'g'ri son kiriting.")


async def process_question_creation(message, num_questions, current_question):
    variants = types.InlineKeyboardMarkup(row_width=5)
    v1 = types.InlineKeyboardButton(text='A', callback_data=f"teacheranswer_{num_questions}_{current_question}_A")
    v2 = types.InlineKeyboardButton(text='B', callback_data=f"teacheranswer_{num_questions}_{current_question}_B")
    v3 = types.InlineKeyboardButton(text='C', callback_data=f"teacheranswer_{num_questions}_{current_question}_C")
    v4 = types.InlineKeyboardButton(text='D', callback_data=f"teacheranswer_{num_questions}_{current_question}_D")
    v5 = types.InlineKeyboardButton(text='E', callback_data=f"teacheranswer_{num_questions}_{current_question}_E")
    variants.row(v1, v2, v3, v4, v5)
    if current_question != 1:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    await bot.send_message(message.chat.id, f"👇 <b>{current_question}-savol</b> uchun javobingizni kiriting:",
                           reply_markup=variants, parse_mode="HTML")


@dp.callback_query_handler(lambda query: query.data.startswith('teacheranswer_'))
async def process_answer(call):
    data = call.data.split('_')
    # testID = int(data[1])
    total_questions = int(data[1])
    current_question = int(data[2])
    correct_answers.append(data[3])

    if current_question < total_questions:
        await process_question_creation(call.message, total_questions, current_question + 1)
    else:
        validate_correct_answers_markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton(text="❌Bekor qilish", callback_data="validate_answer:cancel")
        btn2 = types.InlineKeyboardButton(text="✅Tasdiqlash", callback_data="validate_answer:verify")
        validate_correct_answers_markup.row(btn1, btn2)
        answers_str = "".join(correct_answers)
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await bot.send_message(call.message.chat.id, f"""Siz kiritgan javoblar: <b>{answers_str}</b>Tasdiqlaysizmi?""",
                               parse_mode="HTML", reply_markup=validate_correct_answers_markup)


@dp.callback_query_handler(lambda query: query.data.startswith('validate_answer:'))
async def save_questions(call):
    validate_message = call.data.split(":")[1]
    if validate_message == "cancel":
        correct_answers.clear()
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await bot.send_message(call.from_user.id, f"❌ Testingiz bekor qilindi.", parse_mode="HTML")
        return
    else:
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        testID = requests.create_test_on_db(call.message.chat.id, subjectID, created_at)
        #questionData['testID'] = int(testID)

        #testID_repr = test_id_repr(testID)
        #are_questions_created = db.create_questions(questionData['testID'], correct_answers)

        #if testID and are_questions_created:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        await bot.send_message(call.from_user.id,
                               f"✅ Test va barcha savollar muvaffaqiyatli yaratildi. Testingiz IDsi: <b>{0}</b>",
                               parse_mode="HTML")
        correct_answers.clear()
        # elif not testID:
        #     bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        #     bot.send_message(call.from_user.id,
        #                      "⏳ Testni yaratishda muammo yuzaga keldi. Tez orada bu muammoni to'g'rilaymiz!")
        #     correct_answers.clear()
        # elif not are_questions_created:
        #     bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        #     bot.send_message(call.from_user.id,
        #                      "⏳ Savollarni yaratishda muammo yuzaga keldi. Tez orada bu muammoni to'g'rilaymiz!")
        #     correct_answers.clear()


# Start the bot
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
