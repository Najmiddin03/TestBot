from aiogram import Bot, Dispatcher, types
# from aiogram import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.utils import executor
from db import requests as db
from datetime import datetime
from aiogram.contrib.middlewares.logging import LoggingMiddleware



bot = Bot(token="7311726469:AAHD5xOq6EwAsd6ZjZ3o7g-ao67qzmoVh3I", ParseMode="HTML")
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

 
student_answers = []
studentSession = {}

  
@dp.message_handler(commands=['solve']) 
async def solve_cmd(message: types.Message):
    try:
        user_id = message.from_user.id
        teacher = db.validate_teacher(user_id)
        
        if teacher:
            await message.reply("⛔️ Kechirasiz, siz o'quvchi sifatida ro'yxatdan o'tmagansiz!", reply_markup=student_start_kb)
            return

        await message.reply("👇 Qaysi testni yechmoqchisiz? Sizga berilgan test IDsini 6 xonali ko'rinishda kiriting, masalan 000123:")
        await dp.register_next_step_handler(message, student_test_id)
    except Exception as e:
        await bot.send_message(LOGS_CHANNEL, f"Error in solve_cmd() handler: {e}")


async def student_test_id(message: types.Message):
    try:
        try:
            test_id = int(message.text)
        except:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await message.reply("Iltimos testID ni to'g'ri kiriting.", reply_markup=solve_again_markup)
            return

        is_before_participated = db.check_participation_status(message.from_user.id, test_id)
        if is_before_participated:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await message.reply("⛔️ Kechirasiz, siz bu testni oldin yechgan ekansiz. Testga faqat 1 marta qatnashish mumkin!", reply_markup=solve_again_markup)
            return

        is_test_started = db.is_test_started(test_id)
        if not is_test_started:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await message.reply("⛔️ Kechirasiz, bu test hali boshlanmagan yoki bunday test mavjud emas. Iltimos test raqamini yana bir marta tekshirib ko'ring.", reply_markup=solve_again_markup)
            return
        
        is_test_ended = db.is_test_ended(test_id)
        if is_test_ended:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await message.reply("⛔️ Kechirasiz, bu test vaqti tugagan.", reply_markup=solve_again_markup)
            return
        
        validation_result = db.validate_test_request(test_id)
        questions_list = validation_result[0]
        num_questions = validation_result[1]
        studentSession['questions_list'] = questions_list
        studentSession['num_questions'] = num_questions

        if num_questions:
            started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            studentSession['started_at'] = started_at
            await process_student_answers(message, test_id, num_questions, 1)
        else:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await message.reply("❌ Kechirasiz, siz istagan test bazamizda mavjud emas. Adashgan bo'lsangiz /solve komandasini qaytadan bosing.", reply_markup=student_start_kb)
    except Exception as e:
        await bot.send_message(LOGS_CHANNEL, f"Error in student_test_id() handler: {e}")


async def process_student_answers(message: types.Message, testID, num_questions, current_question):
    try:
        variants = types.InlineKeyboardMarkup(row_width=5)
        v1 = types.InlineKeyboardButton(text='A', callback_data=f"studentanswer_{testID}_{num_questions}_{current_question}_A")
        v2 = types.InlineKeyboardButton(text='B', callback_data=f"studentanswer_{testID}_{num_questions}_{current_question}_B")
        v3 = types.InlineKeyboardButton(text='C', callback_data=f"studentanswer_{testID}_{num_questions}_{current_question}_C")
        v4 = types.InlineKeyboardButton(text='D', callback_data=f"studentanswer_{testID}_{num_questions}_{current_question}_D")
        v5 = types.InlineKeyboardButton(text='E', callback_data=f"studentanswer_{testID}_{num_questions}_{current_question}_E")
        variants.row(v1, v2, v3, v4, v5)

        await message.reply(f"👇 <b>{current_question}-savol</b> uchun javobingizni kiriting:", reply_markup=variants, parse_mode=ParseMode.HTML)
    except Exception as e:
        await bot.send_message(LOGS_CHANNEL, f"Error in process_student_answers() handler: {e}")



@dp.callback_query_handler(lambda call: call.data.startswith('studentanswer_'))
async def process_answer(call: types.CallbackQuery):
    try:
        data = call.data.split('_')
        testID = int(data[1])
        total_questions = int(data[2])
        current_question = int(data[3])
        student_answer = data[4]

        await bot.delete_message(call.message.chat.id, call.message.message_id)

        student_answers.append(student_answer)

        if current_question < total_questions:
            await process_student_answers(call.message, testID, total_questions, current_question + 1)
        else:
            verify_answers = types.InlineKeyboardMarkup(row_width=2)
            verify_answers.row(types.InlineKeyboardButton(text="❌Bekor qilish", callback_data="verify_answer:cancel"), types.InlineKeyboardButton(text="✅Tasdiqlash", callback_data="verify_answer:verify"))
            answers = "".join(student_answers)
            await call.message.reply(f"🚀 Siz barcha javoblarni kiritib bo'ldingiz! Sizning javoblar: <b>{answers}</b>", reply_markup=verify_answers, parse_mode=ParseMode.HTML)
    except Exception as e:
        await bot.send_message(LOGS_CHANNEL, f"Error in process_answer() handler: {e}")



if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)