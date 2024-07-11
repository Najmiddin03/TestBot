from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states.test import TestSolve
from config import *
from db import requests
from db import messages
from certigen import generate_certificate


router = Router()


@router.message(Command("solve"))
async def solve_test(message: types.Message, state: FSMContext):
    is_student = await requests.validate_teacher(message.chat.id)

    if is_student:
        await message.answer("Test IDsini 6 xonali son ko'rinishida kiriting, masalan <b>000123</b>:", parse_mode="HTML")
        await state.set_state(TestSolve.waiting_for_test_id_to_solve)
    else:
        await message.answer("Hurmatli foydalanuvchi, siz botda ro'yxatdan o'tmagansiz. Ro'yxatdan o'tish uchun /register komandasini bosing.")


@router.message(TestSolve.waiting_for_test_id_to_solve)
async def get_test_id(message: types.Message, state: FSMContext):
    testID = int(message.text)
    test_exists = await requests.validate_test_request(testID)
    is_test_started = await requests.is_test_started(testID)
    is_test_ended = await requests.is_test_ended(testID)
    is_participated_before = await requests.check_participation_status(message.chat.id, testID)

    if test_exists and is_test_started and not is_test_ended:
        if is_participated_before:
            await message.answer("Kechirasiz, testga faqat 1 marta qatnashish mumkin.")
        else:
            await state.update_data(testID=testID)
            await message.answer("Javoblaringizni kiriting, masalan <b>AABDC</b>:", parse_mode="HTML")
            await state.set_state(TestSolve.waiting_for_answers_solution)
    else:
        await message.answer("Bunday test mavjud emas, yoki bu test boshlanmagan/yakunlangan. Iltimos yana tekshirib ko'ring va qaytadan /solve komandasini bosing.")


@router.message(TestSolve.waiting_for_answers_solution)
async def get_answer_solution(message: types.Message, state: FSMContext):
    answers = message.text.upper()
    await state.update_data(answers=answers)
    await message.answer(f"Javoblaringiz: <b>{answers}</b>.", parse_mode="HTML", reply_markup=verify_buttons.as_markup())
    await state.set_state(TestSolve.waiting_for_verify_solutions)


@router.callback_query(TestSolve.waiting_for_verify_solutions)
async def verify_solution(call: types.CallbackQuery, state: FSMContext):
    is_verified = 1 if call.data == "verify" else 0
    await call.message.edit_text(f"✅ Tasdiqlandi." if is_verified else "❌ Bekor qilindi.")

    data = await state.get_data()
    submitted_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    correct_answers = await requests.get_all_correct_answers(data['testID'])
    student_answers = data['answers']
    score = 0

    if len(correct_answers) == len(student_answers):
        for i in range(0, len(correct_answers)):
            if correct_answers[i] == student_answers[i]:
                score+=1
    else:
        await call.message.answer("Kiritilgan javoblar soni savollar soniga to'g'ri kelmadi. Iltimos /solve komandasi orqali boshidan testni yeching.")
        await state.clear()
        return

    if is_verified and correct_answers:
        are_solutions_submitted = await requests.save_participation(call.message.chat.id, data['testID'], score, submitted_at)
        if are_solutions_submitted:
            await call.message.answer("Javoblaringiz qabul qilindi!")
            await state.clear()

            user_data = await requests.user_is_registered(call.message.chat.id)
            fullname = user_data[0]
            school = user_data[3]
        
            score_p = str((score / len(student_answers)) * 100)[:5]
            print(user_data)
            await call.message.answer(messages.student_report(fullname, school, data['testID'], student_answers, score, score_p, submitted_at), parse_mode="HTML")
            await generate_certificate(call.message.chat.id, data['testID'])
        else:
            call.message.answer("Javoblarni tekshirishda muammo yuzaga keldi.")
            await state.clear()
    else:
        await call.message.answer("Yangi test yaratish uchun /create komandasini bosing.")
        await state.clear()