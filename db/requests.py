from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message
from models import User, Subject, Test, Question, Participation, async_session, TeacherState


# Functions
async def register_user(message: Message, userID, fullname, region, district, school, roleID, joined_at):
    async with async_session() as session:
        try:
            new_user = User(id=userID, fullname=fullname, region=region, district=district, school=school,
                            roleID=roleID, joined_at=joined_at)
            session.add(new_user)
            await session.commit()
            await message.answer("✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz!")
        except SQLAlchemyError as err:
            await session.rollback()
            print("Error registering user:", err)
            await message.answer("🚫 Ro'yxatdan o'tish amalga oshmadi. Yana harakat qilib ko'ring.")


async def user_is_registered(userID):
    async with async_session() as session:
        user_role = await session.get(User, userID)
        user_exists = user_role is not None
        print("Foydalanuvchi bazada mavjud emas." if not user_exists else "Foydalanuvchi bazada mavjud.")
        return user_role.roleID if user_role else None


async def get_user_data(userID):
    async with async_session() as session:
        user_data = await session.get(User, userID)
        return (user_data.fullname, user_data.region, user_data.district, user_data.school,
                user_data.roleID) if user_data else None


async def get_subjects():
    async with async_session() as session:
        result = await session.execute(select(Subject))
        subjects = result.scalars().all()
        return subjects


async def get_subject_id(subject_name):
    async with async_session() as session:
        result = await session.execute(select(Subject).where(Subject.name == subject_name))
        subject_data = result.scalar_one_or_none()
        return subject_data.subjectID if subject_data else None


async def validate_teacher(userID):
    async with async_session() as session:
        result = await session.get(User, userID)
        return result.roleID == 1 if result else False


async def create_test_on_db(ownerID, subjectID, created_at):
    async with async_session() as session:
        try:
            new_test = Test(ownerID=ownerID, subjectID=subjectID, created_at=created_at)
            session.add(new_test)
            await session.commit()
            return new_test.testID
        except SQLAlchemyError as err:
            await session.rollback()
            print("Test yaratish jarayonida muammo yuzaga keldi:", err)
            return None


async def create_questions(testID, answers):
    async with async_session() as session:
        try:
            for answer in answers:
                created_at = datetime.now()
                new_question = Question(testID=testID, answer=answer, created_at=created_at)
                session.add(new_question)
            await session.commit()
            return True
        except SQLAlchemyError as err:
            await session.rollback()
            print("Savol yaratish jarayonida muammo yuzaga keldi:", err)
            return False


# STUDENT related tasks
async def validate_test_request(testID):
    async with async_session() as session:
        questions = await session.execute(select(Question).where(Question.testID == testID))
        questions = questions.scalars().all()
        if not questions:
            return False
        else:
            num_questions = len(questions)
            return questions, num_questions


async def check_participation_status(userID, testID):
    async with async_session() as session:
        res = await session.execute(
            select(Participation).where(Participation.userID == userID, Participation.testID == testID))
        return res.scalar_one_or_none() is not None


async def save_participation(userID, testID, score, submitted_at):
    async with async_session() as session:
        try:
            new_participation = Participation(userID=userID, testID=testID, score=score, submittedAt=submitted_at)
            session.add(new_participation)
            await session.commit()
            return True
        except SQLAlchemyError as err:
            await session.rollback()
            print("Qatnashuvni ro'yxatga olishda muammo yuzaga keldi:", err)
            return False

        # Initialize bot


API_TOKEN = 'YOUR_BOT_API_TOKEN'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# Example handler
@dp.message_handler(commands='start', state='*')
async def start_handler(message: types.Message, state: FSMContext):
    await TeacherState.subject.set()
    await message.reply("Please enter the subject:")


@dp.message_handler(state=TeacherState.subject)
async def process_subject(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['subject'] = message.text
    await message.reply(f"Subject set to: {message.text}")
    # Transition to the next state if needed
    # await TeacherState.next()


# Initialize database
import asyncio

asyncio.run(init_models())

if __name__ == '__main__':
    from aiogram.utils import executor

    executor.start_polling(dp, skip_updates=True)
