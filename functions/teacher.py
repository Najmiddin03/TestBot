from datetime import datetime

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import Message

from db import requests as db
from db.config import *

subjectID = None
questionData = {}
correct_answers = []


# Define states
class Form(StatesGroup):
    waiting_for_custom_question_count = State()


def setup_teacher_handlers(dp):
    # Handler for the /create command
    @dp.message_handler(commands=['create'])
    async def choose_subject(message: Message):
        try:
            # Inline keyboard for subjects
            subject_markup = types.InlineKeyboardMarkup(row_width=2)
            subjects = await db.get_subjects()
            for subject in subjects:
                subject_markup.add(
                    types.InlineKeyboardButton(text=subject.name, callback_data="subject:" + subject.name))
            await bot.send_message(message.chat.id, "📚 Iltimos quyidagi fanlardan birini tanlang:",
                                   reply_markup=subject_markup)
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in choose_subject() handler: {e}")

    # Callback query handler for subjects
    @dp.callback_query_handler(lambda query: query.data.startswith('subject:'))
    async def choose_question_count(callback_query: types.CallbackQuery):
        try:
            global subjectID
            subjectID = await db.get_subject_id(callback_query.data.split(':')[1])
            # Delete the previous message
            await bot.delete_message(chat_id=callback_query.message.chat.id,
                                     message_id=callback_query.message.message_id)

            test_count_inline = types.InlineKeyboardMarkup(row_width=3)
            btn1 = types.InlineKeyboardButton(text="5", callback_data="test_count:" + "5")
            btn2 = types.InlineKeyboardButton(text="10", callback_data="test_count:" + "10")
            btn3 = types.InlineKeyboardButton(text="15", callback_data="test_count:" + "15")
            btn4 = types.InlineKeyboardButton(text="20", callback_data="test_count:" + "20")
            btn5 = types.InlineKeyboardButton(text="25", callback_data="test_count:" + "25")
            btn6 = types.InlineKeyboardButton(text="30", callback_data="test_count:" + "30")
            btn7 = types.InlineKeyboardButton(text="Boshqa son", callback_data="test_count:" + "other")

            test_count_inline.row(btn1, btn2, btn3)
            test_count_inline.row(btn4, btn5, btn6)
            test_count_inline.row(btn7)

            await bot.send_message(callback_query.message.chat.id, f"❓ Testingiz nechta savoldan iborat?",
                                   reply_markup=test_count_inline, parse_mode='HTML')
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in choose_question_count() handler: {e}")

    # Callback query handler for question count
    @dp.callback_query_handler(lambda query: query.data.startswith('test_count:'))
    async def ask_question_count(callback_query: types.CallbackQuery, state: FSMContext):
        try:
            if callback_query.data.split(':')[1] == 'other':
                await Form.waiting_for_custom_question_count.set()
                # Delete the previous message
                await bot.delete_message(chat_id=callback_query.message.chat.id,
                                         message_id=callback_query.message.message_id)
                await bot.send_message(callback_query.from_user.id,
                                       "Iltimos test savollari sonini o'zingiz kiriting. Test savollar miqdori 100 tadan "
                                       "oshmasligi kerak:")
            else:
                questions_amount = int(callback_query.data.split(':')[1])  # Extract question count from callback_data
                # Delete the previous message
                await bot.delete_message(chat_id=callback_query.message.chat.id,
                                         message_id=callback_query.message.message_id)

                user_id = callback_query.from_user.id
                await process_question_creation(callback_query.message, questions_amount, 1)
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in ask_question_count() handler: {e}")

    # Handler to receive custom question count
    @dp.message_handler(state=Form.waiting_for_custom_question_count)
    async def ask_custom_question_count(message: types.Message, state: FSMContext):
        try:
            try:
                questions_amount = int(message.text)
                if questions_amount > 100:
                    await message.reply("Savollar miqdori 100 tadan oshmasligi kerak. Qayta urinib ko'ring.")
                    return
                await state.finish()
                await process_question_creation(message, questions_amount, 1)
            except ValueError:
                await message.reply("Iltimos, to'g'ri son kiriting.")
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in ask_custom_question_count() handler: {e}")

    async def process_question_creation(message, num_questions, current_question):
        try:
            variants = types.InlineKeyboardMarkup(row_width=5)
            v1 = types.InlineKeyboardButton(text='A',
                                            callback_data=f"teacheranswer_{num_questions}_{current_question}_A")
            v2 = types.InlineKeyboardButton(text='B',
                                            callback_data=f"teacheranswer_{num_questions}_{current_question}_B")
            v3 = types.InlineKeyboardButton(text='C',
                                            callback_data=f"teacheranswer_{num_questions}_{current_question}_C")
            v4 = types.InlineKeyboardButton(text='D',
                                            callback_data=f"teacheranswer_{num_questions}_{current_question}_D")
            v5 = types.InlineKeyboardButton(text='E',
                                            callback_data=f"teacheranswer_{num_questions}_{current_question}_E")
            variants.row(v1, v2, v3, v4, v5)
            if current_question != 1:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            await bot.send_message(message.chat.id, f"👇 <b>{current_question}-savol</b> uchun javobingizni kiriting:",
                                   reply_markup=variants, parse_mode="HTML")
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in process_question_creation() handler: {e}")

    @dp.callback_query_handler(lambda query: query.data.startswith('teacheranswer_'))
    async def process_answer(call):
        try:
            data = call.data.split('_')
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
                await bot.send_message(call.message.chat.id,
                                       f"""Siz kiritgan javoblar: <b>{answers_str}</b>Tasdiqlaysizmi?""",
                                       parse_mode="HTML", reply_markup=validate_correct_answers_markup)
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in process_answer() handler: {e}")

    @dp.callback_query_handler(lambda query: query.data.startswith('validate_answer:'))
    async def save_questions(call):
        try:
            validate_message = call.data.split(":")[1]
            if validate_message == "cancel":
                correct_answers.clear()
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                await bot.send_message(call.from_user.id, f"❌ Testingiz bekor qilindi.", parse_mode="HTML")
                return
            else:
                created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                testID = await db.create_test_on_db(1, subjectID, created_at)
                questionData['testID'] = testID

                testID_repr = test_id_repr(testID)
                are_questions_created = await db.create_questions(testID, correct_answers)

                if testID and are_questions_created:
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    await bot.send_message(call.from_user.id,
                                           f"✅ Test va barcha savollar muvaffaqiyatli yaratildi. Testingiz IDsi: <b>{testID_repr}</b>",
                                           parse_mode='HTML')
                    correct_answers.clear()
                elif not testID:
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    await bot.send_message(call.from_user.id,
                                           "⏳ Testni yaratishda muammo yuzaga keldi. Tez orada bu muammoni to'g'rilaymiz!")
                    correct_answers.clear()
                elif not are_questions_created:
                    await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                    await bot.send_message(call.from_user.id,
                                           "⏳ Savollarni yaratishda muammo yuzaga keldi. Tez orada bu muammoni to'g'rilaymiz!")
                    correct_answers.clear()
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in save_questions() handler: {e}")

    def test_id_repr(testID):
        # This method converts integer test ID to string representation: 12 -> 000012
        return "0" * (6 - len(str(testID))) + str(testID)

    # TEST MANAGEMENT
    @dp.message_handler(commands=['starttest'])
    async def teacher_start_test(message):
        try:
            # Start the test
            own_tests_markup = types.InlineKeyboardMarkup(row_width=3)
            all_active_tests = db.get_all_active_tests(message.chat.id)

            if all_active_tests:
                for test in all_active_tests:
                    print(test[0])
                    test_repr = test_id_repr(test[0])
                    own_tests_markup.add(
                        types.InlineKeyboardButton(text=f"{test_repr}", callback_data=f"active_test:{test_repr}"))

                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                await bot.send_message(message.chat.id, "Qaysi testni boshlamoqchisiz?", reply_markup=own_tests_markup)
            else:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                await bot.send_message(message.chat.id,
                                       "Kechirasiz, siz hali test yaratmagansiz yoki barcha testlaringiz oldin o'tib ketgan. Ularni qayta boshlay olmaysiz.",
                                       reply_markup=own_tests_markup)
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in teacher_start_test() handler: {e}")

    @dp.callback_query_handler(lambda query: query.data.startswith('active_test:'))
    async def process_start_test(call):
        try:
            start_testID = int(call.data.split(":")[1])
            start_testID_repr = test_id_repr(start_testID)
            is_started = db.start_test(start_testID)

            if is_started:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                await bot.send_message(call.message.chat.id, f"{start_testID_repr}-test boshlandi!", parse_mode="HTML")
            else:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                await bot.send_message(call.message.chat.id,
                                       "Kechirasiz, testni boshlashda muammo yuzaga keldi. Iltimos admin bilan aloqaga chiqing: @cacnos_jangchisi")
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in process_start_test() handler: {e}")

    @dp.message_handler(commands=['finishtest'])
    async def teacher_finish_test(message):
        try:
            # Finish the test
            own_tests_markup = types.InlineKeyboardMarkup(row_width=3)
            all_ongoing_tests = db.get_all_ongoing_tests(message.chat.id)

            if all_ongoing_tests:
                for test in all_ongoing_tests:
                    test_repr = test_id_repr(test[0])
                    own_tests_markup.add(
                        types.InlineKeyboardButton(text=f"{test_repr}", callback_data=f"ongoing_test:{test_repr}"))

                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                await bot.send_message(message.chat.id, "Qaysi testni tugatmoqchisiz?", reply_markup=own_tests_markup)
            else:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
                await bot.send_message(message.chat.id,
                                       "Kechirasiz, hozirda sizning davom etib turgan testingiz mavjud emas.",
                                       reply_markup=own_tests_markup)
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in teacher_finish_test() handler: {e}")

    @dp.callback_query_handler(lambda query: query.data.startswith('ongoing_test:'))
    async def process_finish_test(call):
        try:
            finish_testID = int(call.data.split(":")[1])
            finish_testID_repr = test_id_repr(finish_testID)
            is_finished = db.finish_test(finish_testID)

            if is_finished:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                await bot.send_message(call.message.chat.id, f"{finish_testID_repr}-test yakunlandi!",
                                       parse_mode="HTML")
            else:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
                await bot.send_message(call.message.chat.id,
                                       "Kechirasiz, testni tugatishda muammo yuzaga keldi. Iltimos admin bilan aloqaga chiqing: @cacnos_jangchisi")
        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in process_finish_test() handler: {e}")
