from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Date, Enum
import enum

DATABASE_URL = 'sqlite:///persistent_database.db'

engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(150), nullable=True)
    password = Column(String(150), nullable=False)
    
    # Relationships
    ebikes = relationship('EBike', back_populates='owner', cascade="all, delete-orphan")
    practice_tests = relationship('PracticeTest', back_populates='user', cascade="all, delete-orphan")
    real_tests = relationship('RealTest', back_populates='user', cascade="all, delete-orphan")
    practice_attempts = relationship("PracticeAttempt", back_populates="user", cascade="all, delete-orphan")
    parking_spot = relationship("ParkingSpot", back_populates="reserved_user", uselist=False)
    role = Column(String(10))  # 'student' or 'teacher'
    department = Column(String(150))  # for teachers
    year = Column(Integer)  # for students
    house = Column(String(50))  # for students

class EBike(Base):
    __tablename__ = 'ebikes'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    model = Column(String(100), nullable=False)
    serial_number = Column(String(100), unique=True, nullable=False)
    colour = Column(String(50), nullable=False)  # New field for e-bike colour
    is_approved = Column(Boolean, default=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    owner = relationship('User', back_populates='ebikes')

class PracticeTest(Base):
    __tablename__ = 'practice_tests'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))  # <-- This line fixes the problem

    user = relationship('User', back_populates='practice_tests')  # <-- Define this side of the relationship
    questions = relationship('PracticeQuestion', back_populates='test', cascade="all, delete-orphan")


class PracticeQuestion(Base):
    __tablename__ = 'practice_questions'
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('practice_tests.id'), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # Store options as a comma-separated string
    correct_answer = Column(String(100), nullable=False)

    test = relationship('PracticeTest', back_populates='questions')

class PracticeAttempt(Base):
    __tablename__ = 'practice_attempts'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('practice_tests.id'), nullable=False)
    score = Column(Integer, nullable=False)
    attempt_date = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='practice_attempts')


class RealTest(Base):
    __tablename__ = 'real_tests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    questions = relationship("RealTestQuestion", back_populates="test", cascade="all, delete-orphan")
    user = relationship("User", back_populates="real_tests")

class RealTestQuestion(Base):
    __tablename__ = 'real_test_questions'
    
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey('real_tests.id'), nullable=False)
    question_text = Column(String(255), nullable=False)
    correct_answer = Column(String(1), nullable=False)
    option_a = Column(String(100), nullable=False)
    option_b = Column(String(100), nullable=False)
    option_c = Column(String(100), nullable=False)
    option_d = Column(String(100), nullable=False)
    
    test = relationship("RealTest", back_populates="questions")


class Area(enum.Enum):
    OLD_SCHOOL = "Old School"
    SIDE_GATE = "Side Gate"

class ParkingSpot(Base):
    __tablename__ = 'parking_spots'
    
    id = Column(Integer, primary_key=True)
    number = Column(String(10), nullable=False, unique=True)
    area = Column(Enum(Area), nullable=False)
    is_available = Column(Boolean, default=True)
    reserved_for = Column(Integer, ForeignKey('users.id'))
    reservation_date = Column(Date)  # Date of reservation
    
    reserved_user = relationship("User", back_populates="parking_spot")

class RealTestAttempt(Base):
    __tablename__ = 'real_test_attempts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('real_tests.id'), nullable=False)
    passed = Column(Boolean, nullable=False, default=False)
    attempt_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="real_test_attempts")
    test = relationship("RealTest", back_populates="attempts")

# Update User and RealTest relationships
User.real_test_attempts = relationship("RealTestAttempt", back_populates="user", cascade="all, delete-orphan")
RealTest.attempts = relationship("RealTestAttempt", back_populates="test", cascade="all, delete-orphan")

Base.metadata.create_all(bind=engine)

