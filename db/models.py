from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
from aiogram.dispatcher.filters.state import State, StatesGroup

# Database setup
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()

# Define models
# Role class definition
class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(20), nullable=False)

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    fullname = Column(String(100))
    region = Column(String(100))
    district = Column(String(100))
    school = Column(String(100))
    roleID = Column(Integer, ForeignKey('role.id'))
    role = relationship("Role")
    joined_at = Column(DateTime)

class Subject(Base):
    __tablename__ = 'subject'
    subjectID = Column(Integer, primary_key=True)
    name = Column(String(100))

class Test(Base):
    __tablename__ = 'test'
    testID = Column(Integer, primary_key=True)
    ownerID = Column(Integer, ForeignKey('user.id'))
    subjectID = Column(Integer, ForeignKey('subject.subjectID'))
    created_at = Column(DateTime)
    owner = relationship("User")
    subject = relationship("Subject")

class Question(Base):
    __tablename__ = 'question'
    questionID = Column(Integer, primary_key=True)
    testID = Column(Integer, ForeignKey('test.testID'))
    answer = Column(String(100))
    created_at = Column(DateTime)
    test = relationship("Test")

class Participation(Base):
    __tablename__ = 'participation'
    participationID = Column(Integer, primary_key=True)
    userID = Column(Integer, ForeignKey('user.id'))
    testID = Column(Integer, ForeignKey('test.testID'))
    score = Column(Integer)
    submittedAt = Column(DateTime)
    user = relationship("User")
    test = relationship("Test")

# Create tables
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# State Management
class TeacherState(StatesGroup):
    subject = State()
    num_questions = State()
    question_creation = State()