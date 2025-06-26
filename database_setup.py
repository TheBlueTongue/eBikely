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
    reservations = relationship("ParkingReservation", back_populates="user")
    incident_reports = relationship('IncidentReport', back_populates='user')
    has_license = Column(Boolean, default=False)
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
    reservations = relationship("ParkingReservation", back_populates="spot")


class ParkingReservation(Base):
    __tablename__ = 'parking_reservations'

    id = Column(Integer, primary_key=True)
    spot_id = Column(Integer, ForeignKey('parking_spots.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    reservation_date = Column(Date, nullable=False)

    user = relationship("User", back_populates="reservations")
    spot = relationship("ParkingSpot", back_populates="reservations")

class RealTestAttempt(Base):
    __tablename__ = 'real_test_attempts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    test_id = Column(Integer, ForeignKey('real_tests.id'), nullable=False)
    passed = Column(Boolean, nullable=False, default=False)
    attempt_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="real_test_attempts")
    test = relationship("RealTest", back_populates="attempts")

class IncidentReport(Base):
    __tablename__ = 'incident_reports'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(Text)
    date_reported = Column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='incident_reports')

def seed_data():
    session = SessionLocal()

    # --- Seed Parking Spots ---
    if not session.query(ParkingSpot).first():
        for i in range(1, 97):
            session.add(ParkingSpot(number=f"OS-{i}", area=Area.OLD_SCHOOL))
        for i in range(1, 31):
            session.add(ParkingSpot(number=f"SG-{i}", area=Area.SIDE_GATE))
        print("✅ Seeded parking spots.")

    # --- Seed Practice Tests & Questions ---
    if not session.query(PracticeTest).first():
        quiz_data = {
            "Practice Test 1": [
                # Original 5
                {"question": "What should you always wear when riding an e-bike?", "options": ["Helmet", "Scarf", "Sunglasses", "Backpack"], "correct": "Helmet"},
                {"question": "Is it legal to ride an e-bike without a helmet in Australia?", "options": ["Yes", "Only in parks", "No", "Only on private property"], "correct": "No"},
                {"question": "What is the maximum speed allowed for e-bikes in Australia?", "options": ["25 km/h", "40 km/h", "15 km/h", "35 km/h"], "correct": "25 km/h"},
                {"question": "How should you position yourself on the road when riding an e-bike?", "options": ["To the far left", "In the middle of the lane", "On the footpath", "Against traffic"], "correct": "To the far left"},
                {"question": "What should you do before riding your e-bike for the first time?", "options": ["Check brakes and battery", "Start pedaling", "Put on gloves", "Adjust mirrors"], "correct": "Check brakes and battery"},
                # +15 new
                {"question": "Which part of the e-bike provides electric assistance?", "options": ["Motor", "Frame", "Handlebar", "Tire"], "correct": "Motor"},
                {"question": "What is the safest way to cross a busy intersection?", "options": ["Walk bike across", "Speed through", "Ignore signals", "Use pedestrian crossing"], "correct": "Walk bike across"},
                {"question": "Where should you not ride an e-bike?", "options": ["On highways", "On shared paths", "On bike lanes", "On quiet streets"], "correct": "On highways"},
                {"question": "What is one way to extend e-bike battery life?", "options": ["Pedal assist", "Ride at top speed", "Turn lights on all day", "Avoid charging fully"], "correct": "Pedal assist"},
                {"question": "How often should you check your e-bike’s chain?", "options": ["Weekly", "Yearly", "Every ride", "Never"], "correct": "Weekly"},
                {"question": "Which component helps absorb bumps?", "options": ["Suspension", "Battery", "Bell", "Stand"], "correct": "Suspension"},
                {"question": "What’s the legal motor watt limit for Australian e-bikes?", "options": ["250W", "500W", "750W", "1000W"], "correct": "250W"},
                {"question": "Can you ride an e-bike under the influence of alcohol?", "options": ["No", "Yes", "Only under 0.05", "Only on weekends"], "correct": "No"},
                {"question": "Which tool helps prevent theft?", "options": ["Bike lock", "Phone", "Water bottle", "Helmet"], "correct": "Bike lock"},
                {"question": "What’s one thing you should avoid doing while riding?", "options": ["Using a phone", "Looking ahead", "Using hand signals", "Pedaling"], "correct": "Using a phone"},
                {"question": "What should you do in wet conditions?", "options": ["Slow down", "Ride faster", "Ignore puddles", "Wear sandals"], "correct": "Slow down"},
                {"question": "What does a blinking red taillight mean?", "options": ["Caution", "Stopped", "No power", "Visibility"], "correct": "Visibility"},
                {"question": "How far in advance should you signal a turn?", "options": ["At least 30m", "After turning", "Only in groups", "No need to"], "correct": "At least 30m"},
                {"question": "How can you improve visibility at night?", "options": ["Wear reflective gear", "Ride silently", "Turn off lights", "Go faster"], "correct": "Wear reflective gear"},
                {"question": "What’s the best way to park your e-bike at school?", "options": ["In the designated spot", "Against any fence", "Behind a car", "Near the canteen"], "correct": "In the designated spot"},
            ],
            "Practice Test 2": [
                # Original 5
                {"question": "What does the red traffic light signify?", "options": ["Go", "Slow down", "Stop", "Yield"], "correct": "Stop"},
                {"question": "Can you ride on footpaths in Australia with an e-bike?", "options": ["Always", "Only under 12 or with an adult", "Never", "Only in rural areas"], "correct": "Only under 12 or with an adult"},
                {"question": "What should you do when approaching a pedestrian crossing?", "options": ["Speed up", "Sound the horn", "Stop for pedestrians", "Weave around them"], "correct": "Stop for pedestrians"},
                {"question": "How should you signal a turn on an e-bike?", "options": ["Shout", "Use hand signals", "Use blinkers", "Tap your helmet"], "correct": "Use hand signals"},
                {"question": "What does a yellow bike lane sign mean?", "options": ["Bike lane ends", "Shared path ahead", "Bike lane", "No bikes allowed"], "correct": "Bike lane"},
                # +15 new
                {"question": "Why should you wear gloves while riding?", "options": ["Grip and protection", "Fashion", "Sunblock", "No reason"], "correct": "Grip and protection"},
                {"question": "What’s the benefit of using pedal assist?", "options": ["Less effort", "More noise", "Faster battery drain", "None"], "correct": "Less effort"},
                {"question": "When should you charge your e-bike?", "options": ["Before battery is empty", "After flat", "During rides", "Never"], "correct": "Before battery is empty"},
                {"question": "What should you do when turning right at a roundabout?", "options": ["Signal and give way", "Go straight", "Ride against traffic", "Stop in the middle"], "correct": "Signal and give way"},
                {"question": "What is a safe way to carry a backpack?", "options": ["On your back", "Hanging from handlebars", "On pedals", "Dragging behind"], "correct": "On your back"},
                {"question": "Why should your lights be checked regularly?", "options": ["Visibility and safety", "To look cool", "To avoid speeding", "They add weight"], "correct": "Visibility and safety"},
                {"question": "How do you avoid slipping in wet conditions?", "options": ["Brake earlier", "Speed up", "Lean heavily", "Avoid pedaling"], "correct": "Brake earlier"},
                {"question": "When is it okay to block a driveway?", "options": ["Never", "If you're fast", "If no one is home", "Only for a moment"], "correct": "Never"},
                {"question": "What part of the day is most dangerous for visibility?", "options": ["Dusk/dawn", "Midday", "Night", "Morning"], "correct": "Dusk/dawn"},
                {"question": "Should you use both brakes?", "options": ["Yes", "Only front", "Only rear", "Not needed"], "correct": "Yes"},
                {"question": "What should you check before every ride?", "options": ["Tires, brakes, battery", "Phone", "Shoelaces", "Social media"], "correct": "Tires, brakes, battery"},
                {"question": "Can you wear headphones while riding?", "options": ["Not recommended", "Yes", "Only one ear", "Only on weekends"], "correct": "Not recommended"},
                {"question": "Where should you mount your phone?", "options": ["On a holder", "On the front wheel", "On your back", "On the battery"], "correct": "On a holder"},
                {"question": "What do reflectors do?", "options": ["Help others see you", "Decorate", "Slow you down", "Change colours"], "correct": "Help others see you"},
                {"question": "What does a bike bell help with?", "options": ["Alerting others", "Playing tunes", "Measuring speed", "Balancing"], "correct": "Alerting others"},
            ],
            "Practice Test 3": [
                # Original 5
                {"question": "What is the recommended tire pressure for an e-bike?", "options": ["As per manufacturer guidelines", "30 PSI", "50 PSI", "Any pressure"], "correct": "As per manufacturer guidelines"},
                {"question": "How do you check the brakes on your e-bike?", "options": ["Squeeze levers and check resistance", "Kick the tire", "Look at the pads only", "Ride fast and stop suddenly"], "correct": "Squeeze levers and check resistance"},
                {"question": "What should you do if your e-bike’s battery dies during a ride?", "options": ["Pedal manually", "Call a tow truck", "Leave it and walk home", "Push it to a shop"], "correct": "Pedal manually"},
                {"question": "How often should you clean your e-bike?", "options": ["Every week", "Only when muddy", "Every ride", "Regularly depending on use"], "correct": "Regularly depending on use"},
                {"question": "What should you do if you experience a flat tire?", "options": ["Replace or patch it", "Pump more air", "Keep riding", "Ignore it"], "correct": "Replace or patch it"},
                # +15 new
                {"question": "What is the first thing to check in a crash?", "options": ["Yourself for injuries", "Your phone", "Your helmet style", "Weather"], "correct": "Yourself for injuries"},
                {"question": "Can you take passengers on an e-bike?", "options": ["Only with proper seat", "Always", "Never", "Only kids"], "correct": "Only with proper seat"},
                {"question": "Why should you not overload your e-bike?", "options": ["Affects balance and brakes", "Battery grows", "Chain gets longer", "Tyres explode"], "correct": "Affects balance and brakes"},
                {"question": "Why are mirrors useful on e-bikes?", "options": ["Check traffic behind", "Style", "Aerodynamics", "None"], "correct": "Check traffic behind"},
                {"question": "How do you protect your e-bike from rain?", "options": ["Cover it", "Ride faster", "Tilt it", "Use hairdryer"], "correct": "Cover it"},
                {"question": "What is regenerative braking?", "options": ["Charging via braking", "Fast stopping", "Extra braking pad", "None of these"], "correct": "Charging via braking"},
                {"question": "What is chain skipping a sign of?", "options": ["Worn drivetrain", "Too much speed", "Air in tires", "Overcharging"], "correct": "Worn drivetrain"},
                {"question": "What does a clicking noise in pedaling suggest?", "options": ["Loose part", "Battery charged", "Chain tight", "Normal"], "correct": "Loose part"},
                {"question": "Where is the best place to store your e-bike?", "options": ["Dry, sheltered place", "On the street", "In the rain", "Next to heater"], "correct": "Dry, sheltered place"},
                {"question": "How can you increase your e-bike's range?", "options": ["Use eco mode", "Full throttle", "Skip braking", "Ride uphill"], "correct": "Use eco mode"},
                {"question": "Should you ride with one hand?", "options": ["Only when signaling", "Always", "To wave", "No reason"], "correct": "Only when signaling"},
                {"question": "What should your e-bike have to ride at night?", "options": ["Lights and reflectors", "Flashing helmet", "Phone torch", "Glow paint"], "correct": "Lights and reflectors"},
                {"question": "What’s the best way to dry your e-bike after rain?", "options": ["Wipe it down", "Leave in sun all day", "Use dryer", "Nothing"], "correct": "Wipe it down"},
                {"question": "Should you lubricate the chain?", "options": ["Yes, regularly", "Never", "Only in summer", "Only after flat tires"], "correct": "Yes, regularly"},
                {"question": "What could loose handlebars mean?", "options": ["Dangerous handling", "Faster turning", "Cool style", "Low battery"], "correct": "Dangerous handling"},
            ],
        }

        for quiz_name, question_list in quiz_data.items():
            test = PracticeTest(name=quiz_name, user_id=1)  # user_id=1 for initial seed
            session.add(test)
            session.commit()

            for q_data in question_list:
                question = PracticeQuestion(
                    test_id=test.id,
                    question=q_data["question"],
                    options=",".join(q_data["options"]),
                    correct_answer=q_data["correct"]
                )
                session.add(question)
            session.commit()
        print("✅ Seeded practice tests with 20 questions each.")

    session.close()

# Update User and RealTest relationships
User.real_test_attempts = relationship("RealTestAttempt", back_populates="user", cascade="all, delete-orphan")
RealTest.attempts = relationship("RealTestAttempt", back_populates="test", cascade="all, delete-orphan")

Base.metadata.create_all(bind=engine)

