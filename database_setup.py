from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from flask_login import UserMixin
from datetime import datetime

# Define a consistent path for the SQLite database file
DATABASE_URL = 'sqlite:///persistent_database.db'

# Set up the engine and base
engine = create_engine(DATABASE_URL)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    email = Column(String(150), nullable=True)  
    password = Column(String(150), nullable=False)
    ebikes = relationship('EBike', back_populates='owner')
    practice_tests = relationship('PracticeTest', back_populates='user')
    real_tests = relationship('RealTest', back_populates='user')

class EBike(Base):
    __tablename__ = 'ebikes'

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    model = Column(String(100), nullable=False)
    is_approved = Column(Boolean, default=False)
    serial_number = Column(String(100), unique=True, nullable=False)  # serial_number added here
    registration_date = Column(DateTime, default=datetime.utcnow) 
    owner = relationship('User', back_populates='ebikes')

class ParkingSpot(Base):
    __tablename__ = 'parking_spots'

    id = Column(Integer, primary_key=True)
    spot_number = Column(String(10), unique=True, nullable=False)
    is_occupied = Column(Boolean, default=False)
    occupant_id = Column(Integer, ForeignKey('users.id'), nullable=True)

class PracticeTest(Base):
    __tablename__ = 'practice_tests'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    score = Column(Integer, nullable=False)
    date_taken = Column(DateTime, default=datetime.utcnow)
    passed = Column(Boolean, nullable=False)
    user = relationship('User', back_populates='practice_tests')

class RealTest(Base):
    __tablename__ = 'real_tests'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    score = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    user = relationship('User', back_populates='real_tests')

# Create tables if they don't already exist
Base.metadata.create_all(bind=engine)
