from datetime import datetime
import pandas as pd

from aiogram.types import Message, FSInputFile
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select

from config import *
from db.models import User, Test, Participation, AsyncSession
from .messages import myinfo_msg


# Functions
async def register_user(message: Message, userID, fullname, region, district, school, role, joined_at):
    async with AsyncSession() as session:
        try:
            new_user = User(id = userID, fullname=fullname, region=region, district=district, school=school,
                            role=role, joined_at=joined_at)
            session.add(new_user)
            await session.commit()

            await message.answer("✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz!")
        except SQLAlchemyError as err:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error registering user: {err}")
            await message.answer("❌ Ro'yxatdan o'tish amalga oshmadi. Yana urinib ko'ring, balki qaysidir ma'lumot noto'g'ri kiritilgan bo'lishi mumkin.")


async def user_is_registered(userID):
    async with AsyncSession() as session:
        try:
            user = await session.execute(select(User).where(User.id == userID))
            user_data = user.scalars().first()
            
            if user_data:
                data = (user_data.fullname, user_data.region, user_data.district, user_data.school, user_data.role)
                print(data)
                print("Foydalanuvchi bazada mavjud.")
                return data
            else:
                print("Foydalanuvchi bazada mavjud emas.")
        except SQLAlchemyError as err:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in checking user is registered: {err}")
            return None


async def get_user_data(message: Message, userID):
    async with AsyncSession() as session:
        async with session.begin():
            user = await session.execute(
                select(User).where(User.id == userID)
            )
            print(user)
            user_data = user.scalars().first()
            print(user_data)

            if user_data:
                data = (user_data.fullname, user_data.region, user_data.district, user_data.school,
                user_data.role)
                msg = myinfo_msg(*data)
                await message.answer(msg, parse_mode="HTML")
            else:
                await message.answer("🚫 Kechirasiz, siz ro'yxatdan o'tmagansiz. Ro'yxatdan o'tish uchun /register komandasini bosing.", reply_markup=menu_buttons.as_markup(resize_keyboard=True))
                

async def get_teacher_name(testID):
    async with AsyncSession() as session:
        try:
            user = await session.execute(
                select(Test.ownerID).where(Test.testID == testID)
            )
            user_id = user.scalars().first()
            teacher = await session.execute(
                select(User.fullname).where(User.id == user_id)
            )
            teacher_name = teacher.scalars().first()
            return teacher_name
        except SQLAlchemyError as e:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in getting teacher name: {e}")
            return None


async def validate_teacher(userID):
    async with AsyncSession() as session:
        async with session.begin():
            try:
                role = await session.execute(
                    select(User.role).where(User.id == userID)
                )
                role_result = role.scalars().first()
                print("Role: ", role_result)
                return role_result
            except SQLAlchemyError as e:
                await session.rollback()
                await bot.send_message(LOGS_CHANNEL, f"Error validating teacher: {e}")


async def create_test_on_db(ownerID: int, subject: str, created_at: str, answers: str):
    async with AsyncSession() as session:
        try:
            new_test = Test(ownerID=ownerID, subject=subject, created_at=created_at, answers=answers)
            session.add(new_test)
            await session.commit()
            return new_test.testID
        except SQLAlchemyError as err:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in creating test on db: {err}")
            return None


# start test function
async def start_test(testID):
    started_at = datetime.now()
    async with AsyncSession() as session:
        try:
            stmt = update(Test).where(Test.testID == testID, Test.ended_at.is_(None)).values(is_ongoing=True,
                                                                                             started_at=started_at)
            await session.execute(stmt)
            await session.commit()
            print(f"Test-{testID} boshlandi!")
            return True
        except SQLAlchemyError as e:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in start_test(): {e}")
            return False


async def get_all_active_tests(teacherID):
    async with AsyncSession() as session:
        try:
            result = await session.execute(
                select(Test.testID).where(Test.ownerID == teacherID, Test.is_active == True, Test.is_ongoing == False))
            active_tests_by_this_user = result.scalars().all()
            return list(active_tests_by_this_user)
        except SQLAlchemyError as e:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in get_all_active_tests(): {e}")
            return []


async def get_all_ongoing_tests(teacherID):
    async with AsyncSession() as session:
        try:
            result = await session.execute(select(Test.testID).where(Test.ownerID == teacherID, Test.is_ongoing == True))
            ongoing_tests_by_this_user = result.scalars().all()
            return ongoing_tests_by_this_user
        except SQLAlchemyError as e:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in get_all_ongoing_tests(): {e}")
            return []


async def is_test_started(testID):
    async with AsyncSession() as session:
        try:
            result = await session.execute(select(Test.started_at).where(Test.testID == testID))
            started_test = result.scalar_one_or_none()
            return started_test
        except SQLAlchemyError as e:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in is_test_started(): {e}")
            return None


async def is_test_ended(testID):
    async with AsyncSession() as session:
        try:
            result = await session.execute(
                select(Test.ended_at).where(Test.testID == testID, Test.is_ongoing == False, Test.ended_at.isnot(None)))
            ended_test = result.scalar_one_or_none()
            return ended_test
        except SQLAlchemyError as e:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in is_test_ended(): {e}")
            return None


# finish test function
async def finish_test(testID):
    finished_at = datetime.now()
    async with AsyncSession() as session:
        try:
            stmt = update(Test).where(Test.testID == testID, Test.ended_at.is_(None)).values(ended_at=finished_at,
                                                                                             is_ongoing=False,
                                                                                             is_active=False)
            await session.execute(stmt)
            await session.commit()
            print(f"Test-{testID} yakunlandi!")
            return True
        except SQLAlchemyError as e:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in finish_test(): {e}")
            return False


async def get_all_correct_answers(testID):
    async with AsyncSession() as session:
        try:
            stmt = select(Test.answers).where(Test.testID == testID)
            result = await session.execute(stmt)
            correct_answers = result.scalars().all()

            return correct_answers[0]
        except SQLAlchemyError as e:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in finish_test(): {e}")
            return False


async def validate_test_request(testID):
    async with AsyncSession() as session:
        try:
            result = await session.execute(select(Test.testID).where(Test.testID == testID))
            is_test_exists = result.scalars().first()
            return is_test_exists
        except SQLAlchemyError as e:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in validate_test_request(): {e}")
            return []


async def check_participation_status(userID, testID):
    async with AsyncSession() as session:
        try:
            result = await session.execute(
                select(Participation).where(Participation.userID == userID, Participation.testID == testID))
            return result.scalar_one_or_none() is not None
        except SQLAlchemyError as e:
            session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in check_participation_status(): {e}")
            return []

async def save_participation(userID, testID, score, submitted_at):
    async with AsyncSession() as session:
        try:
            new_participation = Participation(userID=userID, testID=testID, score=score, submitted_at=submitted_at)
            session.add(new_participation)
            await session.commit()
            return True
        except SQLAlchemyError as err:
            await session.rollback()
            await bot.send_message(LOGS_CHANNEL, f"Error in save_participation(): {err}")
            return False
        

async def generate_test_report(message: types.Message, testID: int):
    async with AsyncSession() as session:
        stmt = select(
        Participation.userID, User.fullname, User.region, User.district, User.school, Test.subject, 
        Test.testID, Participation.submitted_at, Participation.score
        ).join(
            User, Participation.userID == User.id
        ).join(
            Test, Participation.testID == Test.testID
        ).where(Test.testID == testID)
        try:
            result = await session.execute(stmt)
            results = result.fetchall()

            data = [{
                'userID': row.userID,
                'fullname': row.fullname,
                'region': row.region,
                'district': row.district,
                'school': row.school,
                'subject': row.subject,
                'testID': row.testID,
                'submitted_at': row.submitted_at,
                'score': row.score
            } for row in results]

            df = pd.DataFrame(data)
            csv_path = f"{prod_dir}assets/excel/test{test_id_repr(testID)}.csv"

            if not df.empty:
                df.to_csv(csv_path, index=False)
                print(f"Data exported to 'data.csv' successfully!")
                csv_inputfile = FSInputFile(csv_path)
                await bot.send_document(message.chat.id, csv_inputfile, caption="📊 Natijalarni yuklab oling.")
            else:
                await bot.send_message(message.chat.id, text="Kechirasiz, bu testga hech kim qatnashmagani sabab natijalar mavjud emas.")
            
            return True

        except Exception as e:
            await bot.send_message(LOGS_CHANNEL, f"Error in generate_test_report(): {e}")
            return False