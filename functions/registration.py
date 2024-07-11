from datetime import datetime
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models import AsyncSession, User
from states.registration import Registration
from config import *
from db import requests, messages

router = Router()


@router.message(Command("register"))
async def register_start(message: types.Message, state: FSMContext):
    is_user_registered = await requests.user_is_registered(message.chat.id)
    if is_user_registered:
        await message.answer("🚫 Hurmatli foydalanuvchi, siz botda ro'yxatdan o'tgansiz. Yordam uchun /help komandasini bosing.", parse_mode="HTML")
    else:
        await message.answer("Ism familiyangizni kiriting, masalan <b>Alijon Valiyev</b>:", parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Registration.waiting_for_name)


@router.message(Registration.waiting_for_name)
async def register_name(message: types.Message, state: FSMContext):
    role_builder_kb = InlineKeyboardBuilder()
    role_builder_kb.button(text="O'qituvchi", callback_data="role:O'qituvchi")
    role_builder_kb.button(text="O'quvchi", callback_data="role:O'quvchi")
    role_builder_kb.adjust(2)
    await state.update_data(name=message.text)
    await message.answer("O'qituvchimisiz yoki o'quvchi?", reply_markup=role_builder_kb.as_markup())
    await state.set_state(Registration.waiting_for_role)


@router.callback_query(Registration.waiting_for_role)
async def register_role(callback_query: types.CallbackQuery, state: FSMContext):
    role = callback_query.data.split(":")[1]
    await callback_query.message.edit_text(f"Sizning rolingiz: <b>{role}</b>.", parse_mode="HTML")
    region_builder_kb = InlineKeyboardBuilder()
    for region in regions:
        region_builder_kb.button(text=region, callback_data="region:"+region)
    region_builder_kb.adjust(2)
    await state.update_data(role=role)
    await callback_query.message.answer("Qaysi viloyatdansiz?", reply_markup=region_builder_kb.as_markup())
    await state.set_state(Registration.waiting_for_region)


@router.callback_query(Registration.waiting_for_region)
async def register_region(callback_query: types.CallbackQuery, state: FSMContext):
    region = callback_query.data.split(":")[1]
    await callback_query.message.edit_text(f"Sizning hududingiz: <b>{region}</b>.", parse_mode="HTML")
    await state.update_data(region=region)
    
    districts = regions.get(region)
    if districts:
        district_builder_kb = InlineKeyboardBuilder()
        for district in districts:
            district_builder_kb.button(text=district, callback_data="district:"+district)
        district_builder_kb.adjust(2)
    
    await callback_query.message.answer("Tumaningizni tanlang:", reply_markup=district_builder_kb.as_markup())
    await state.set_state(Registration.waiting_for_district)


@router.callback_query(Registration.waiting_for_district)
async def register_district(callback_query: types.CallbackQuery, state: FSMContext):
    district = callback_query.data.split(":")[1]
    await callback_query.message.edit_text(f"Sizning tumaningiz: <b>{district}</b>.", parse_mode="HTML")
    await state.update_data(district=district)
    await callback_query.message.answer("Maktabingizni kiriting, masalan <b>5-maktab</b>:", parse_mode="HTML")
    await state.set_state(Registration.waiting_for_school)


@router.message(Registration.waiting_for_school)
async def register_school(message: types.Message, state: FSMContext):
    await state.update_data(school=message.text)
    
    data = await state.get_data()
    userID = message.chat.id
    fullname = data['name']
    roleID = 1 if data['role'] == "O'qituvchi" else 2
    region = data['region']
    district = data['district']
    school = data['school']
    joined_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save user to database
    await requests.register_user(message=message, userID=userID, fullname=fullname, region=region, district=district, school=school, role=roleID, joined_at=joined_at)
    await state.clear()


@router.message(Command("cancel"))
async def cancel_registration(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state in [
        Registration.waiting_for_name.state, 
        Registration.waiting_for_role.state, 
        Registration.waiting_for_region.state, 
        Registration.waiting_for_district.state, 
        Registration.waiting_for_school.state]:
        await state.clear()
        await message.answer("🛑 Siz ro'yxatdan o'tish jarayonini to'xtatdingiz.", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("☝️ Siz hozir ro'yxatdan o'tish jarayonida emassiz. Iltimos to'g'ri komandani kiriting.")