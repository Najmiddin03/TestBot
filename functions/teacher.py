from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from states.test import TestCreation, TestManage
from config import *
from db import requests


router = Router()


@router.message(Command("create"))
async def create_test(message: types.Message, state: FSMContext):
    is_teacher = await requests.validate_teacher(message.chat.id)

    if is_teacher == 1:
        await message.answer("Fanni kiriting, masalan <b>Matematika</b>:", parse_mode="HTML", reply_markup=None)
        await state.set_state(TestCreation.waiting_for_subject)
    elif is_teacher == 2:
        await message.answer("Hurmatli foydalanuvchi, siz o'quvchi sifatida ro'yxatdan o'tgansiz. Siz test yarata olmaysiz!")
    else:
        await message.answer("Hurmatli foydalanuvchi, siz botda ro'yxatdan o'tmagansiz. Ro'yxatdan o'tish uchun /register komandasini bosing.")


@router.message(TestCreation.waiting_for_subject)
async def get_subject(message: types.Message, state: FSMContext):
    subject = message.text.lower().capitalize()
    await state.update_data(subject=subject)
    await message.answer("Test javoblarini kiriting, masalan <b>AABDC</b>: ", parse_mode="HTML", reply_markup=None)
    await state.set_state(TestCreation.waiting_for_answers)


@router.message(TestCreation.waiting_for_answers)
async def get_answers(message: types.Message, state: FSMContext):
    answers = message.text.upper()
    await state.update_data(answers=answers)
    await message.answer(f"Javoblaringiz: <b>{answers}</b>.", parse_mode="HTML", reply_markup=verify_buttons.as_markup())
    await state.set_state(TestCreation.waiting_for_verify)


@router.callback_query(TestCreation.waiting_for_verify)
async def get_verification(call: types.CallbackQuery, state: FSMContext):
    is_verified = 1 if call.data == "verify" else 0
    await call.message.edit_text(f"✅ Tasdiqlandi." if is_verified else "❌ Bekor qilindi.")

    data = await state.get_data()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if is_verified:
        is_test_created = await requests.create_test_on_db(call.message.chat.id, data['subject'], created_at, data['answers'])
        # are_questions_created = await requests.create_questions(testID, data['answers'])

        if is_test_created:
            testID_repr = test_id_repr(is_test_created)
            await call.message.answer(f"""Test IDsi: <b>{testID_repr}</b>.
                                      
Testni boshlash uchun /starttest komandasini bosing.""", parse_mode="HTML")
            state.clear()
        else:
            await call.message.answer(f"Test yaratish jarayonida muammo yuzaga keldi.")
            state.clear()
    else:
        await call.message.answer("Yangi test yaratish uchun /create komandasini bosing.")
        state.clear()


@router.message(Command("starttest"))
async def start_test(message: types.Message, state: FSMContext):
    all_active_tests = await requests.get_all_active_tests(message.chat.id)
    own_tests_markup = InlineKeyboardBuilder()

    if all_active_tests:
        for test in all_active_tests:
            print(test)
            test_repr = test_id_repr(test)
            own_tests_markup.add(types.InlineKeyboardButton(text=test_repr, callback_data=f"active_test:{test}"))
        own_tests_markup.adjust(2)

        await message.answer("Qaysi testni boshlamoqchisiz?", reply_markup=own_tests_markup.as_markup())
        await state.set_state(TestManage.waiting_for_test_id_to_start)
    else:
        await message.answer("Kechirasiz, siz hali test yaratmagansiz, yoki barcha testlaringiz tugatilgan.")


@router.callback_query(TestManage.waiting_for_test_id_to_start)
async def get_start_test(call: types.CallbackQuery, state: FSMContext):
    test = call.data.split(":")[1]
    test_repr = test_id_repr(test)

    is_started = await requests.start_test(test)

    if is_started:
        await call.message.edit_text(f"{test_repr}-test boshlandi.")
    else:
        await call.message.edit_text("Testni boshlashda muammo yuzaga keldi.")


@router.message(Command("finishtest"))
async def finish_test(message: types.Message, state: FSMContext):
    own_tests_markup = InlineKeyboardBuilder()
    all_ongoing_tests = await requests.get_all_ongoing_tests(message.chat.id)

    if all_ongoing_tests:
        for test in all_ongoing_tests:
            test_repr = test_id_repr(test)
            own_tests_markup.add(types.InlineKeyboardButton(text=test_repr, callback_data=f"ongoing_test:{test}"))
        own_tests_markup.adjust(2)

        await message.answer("Qaysi testni tugatmoqchisiz?", reply_markup=own_tests_markup.as_markup())
        await state.set_state(TestManage.waiting_for_test_id_to_finish)
    else:
        await message.answer("Kechirasiz, hozir sizda davom etayotgan test mavjud emas.")


@router.callback_query(TestManage.waiting_for_test_id_to_finish)
async def get_finish_test(call: types.CallbackQuery, state: FSMContext):
    test = call.data.split(":")[1]
    test_repr = test_id_repr(test)

    is_finished = await requests.finish_test(test)

    if is_finished:
        await call.message.edit_text(f"{test_repr}-test yakunlandi.")

        await requests.generate_test_report(call.message, test)
        await state.clear()
    else:
        await call.message.edit_text("Testni tugatishda muammo yuzaga keldi.")