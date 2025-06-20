from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from database_setup import SessionLocal, User, EBike, PracticeTest, RealTest, ParkingSpot, PracticeAttempt, PracticeQuestion, RealTestAttempt, PracticeTest, ParkingReservation
import forms
from datetime import datetime
from flask import Flask
from flask.cli import with_appcontext
from database_setup import SessionLocal, PracticeTest, PracticeQuestion, Area
import click
import random
from collections import defaultdict
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
import os
import pandas as pd
from sqlalchemy.orm import joinedload
from flask import Flask, render_template, request, redirect, url_for, flash, session as flask_session
from flask_login import login_required, current_user
import random
from flask import abort



# Set up Flask app and login manager
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key12345asdfg'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if user is not authenticated

# Session management function which retrieves the user from the database
@login_manager.user_loader
def load_user(user_id):
    session = SessionLocal()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

# Welcome page route
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        session = SessionLocal()
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed_password,
            role=form.role.data,
            department=form.department.data if form.role.data == 'teacher' else None,
            year=int(form.year.data) if form.role.data == 'student' and form.year.data else None,
            house=form.house.data if form.role.data == 'student' else None
        )
        session.add(new_user)
        try:
            session.commit()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            session.rollback()
            flash('Username already exists. Please choose a different one.', 'danger')
        finally:
            session.close()
    return render_template('register.html', form=form)


# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        session = SessionLocal()
        user = session.query(User).filter_by(username=form.username.data).first()
        session.close()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

# Route for logging out
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    session = SessionLocal()
    ebike_count = session.query(EBike).filter_by(owner_id=current_user.id).count()
    completed_practice_tests = session.query(PracticeAttempt).filter(
        PracticeAttempt.user_id == current_user.id,
        PracticeAttempt.score >= 80
    ).count()
    total_tests = session.query(RealTest).filter_by(user_id=current_user.id).count()
    available_parking_spots = session.query(ParkingSpot).filter_by(is_available=True).count()
    practice_tests = session.query(PracticeTest).filter_by(user_id=current_user.id).all()
    session.close()
    return render_template(
        'dashboard.html',
        ebike_count=ebike_count,
        completed_practice_tests=completed_practice_tests,
        available_parking_spots=available_parking_spots,
        total_tests=total_tests,
        practice_tests=practice_tests
    )

@app.route('/ebikes', methods=['GET', 'POST'])
@login_required
def ebike_management():
    session = SessionLocal()
    form = forms.EbikeRegistrationForm()
    ebikes = session.query(EBike).filter_by(owner_id=current_user.id).all()

    # Check if the user has passed the real test
    passed_test = session.query(RealTestAttempt).filter(
        RealTestAttempt.user_id == current_user.id,
        RealTestAttempt.passed == True
    ).count() > 0

    # Handle e-bike registration
    if form.validate_on_submit():
        new_ebike = EBike(
            owner_id=current_user.id,
            model=form.model.data,
            serial_number=form.serial_number.data,
            colour=form.colour.data
        )
        try:
            session.add(new_ebike)
            session.commit()
            flash('E-bike registered successfully!', 'success')
        except IntegrityError:
            session.rollback()
            flash('This serial number is already registered. Please use a unique serial number.', 'danger')
        return redirect(url_for('ebike_management'))

    # Handle e-bike deletion
    if request.method == 'POST' and 'delete_ebike_id' in request.form:
        ebike_id = int(request.form.get('delete_ebike_id'))
        ebike_to_delete = session.query(EBike).filter_by(id=ebike_id, owner_id=current_user.id).first()
        if ebike_to_delete:
            session.delete(ebike_to_delete)
            session.commit()
            flash('E-bike deleted successfully!', 'success')
        return redirect(url_for('ebike_management'))
    
    session.close()
    return render_template('ebike_management.html', ebikes=ebikes, form=form, passed_test=passed_test)


@app.route('/reserve_spot', methods=['POST'])
@login_required
def reserve_spot():
    session = SessionLocal()
    spot_id = request.form.get('spot_id')
    selected_date_str = request.form.get('selected_date')
    reservation_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

    if reservation_date < date.today():
        flash("Cannot book spots for past dates.", "danger")
        session.close()
        return redirect(f'/parking_spots?date={selected_date_str}')

    # Check if spot is already reserved for that date
    existing_reservation = session.query(ParkingReservation).filter_by(
        spot_id=spot_id,
        reservation_date=reservation_date
    ).first()

    if existing_reservation:
        flash("This spot is already booked for that date.", "danger")
        session.close()
        return redirect(f'/parking_spots?date={selected_date_str}')

    # Prevent multiple bookings by same student for same date
    if current_user.role == 'student':
        user_reservation = session.query(ParkingReservation).filter_by(
            user_id=current_user.id,
            reservation_date=reservation_date
        ).first()
        if user_reservation:
            flash("You already have a spot booked for this date.", "warning")
            session.close()
            return redirect(f'/parking_spots?date={selected_date_str}')

    # Book the spot
    new_reservation = ParkingReservation(
        spot_id=spot_id,
        user_id=current_user.id,
        reservation_date=reservation_date
    )
    session.add(new_reservation)
    session.commit()
    session.close()
    flash("Spot reserved successfully!", "success")
    return redirect(f'/parking_spots?date={selected_date_str}')


@app.route('/release_spot', methods=['POST'])
@login_required
def release_spot():
    session = SessionLocal()
    spot_id = request.form.get('spot_id')
    selected_date_str = request.form.get('selected_date')
    reservation_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()

    reservation = session.query(ParkingReservation).filter_by(
        spot_id=spot_id,
        reservation_date=reservation_date
    ).first()

    if not reservation:
        flash("Invalid spot or not reserved on this date.", "danger")
        session.close()
        return redirect(f'/parking_spots?date={selected_date_str}')

    if current_user.role == 'teacher' or reservation.user_id == current_user.id:
        session.delete(reservation)
        session.commit()
        flash("Spot released.", "info")
    else:
        flash("You don't have permission to release this spot.", "danger")

    session.close()
    return redirect(f'/parking_spots?date={selected_date_str}')


@app.route("/parking_spots", methods=["GET"])
@login_required
def parking_spots():
    session = SessionLocal()

    # Parse selected date or use today
    selected_date_str = request.args.get("date")
    selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date() if selected_date_str else date.today()

    # Get all spots
    all_spots = session.query(ParkingSpot).all()

    # Get reservations for the selected date
    reservations = session.query(ParkingReservation)\
        .filter(ParkingReservation.reservation_date == selected_date)\
        .all()

    # Build a mapping of spot_id -> reservation
    reservation_map = {r.spot_id: r for r in reservations}

    # Build a dictionary of spot number → (spot, reservation)
    spots_by_number = {
        spot.number: {
            "spot": spot,
            "reservation": reservation_map.get(spot.id)
        }
        for spot in all_spots
    }

    # Load layout grid from Excel file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(base_dir, "Map.xlsx")
    layout_df = pd.read_excel(map_path, header=None).iloc[0:30, 0:42].fillna("").astype(str)
    layout_grid = layout_df.values.tolist()

    session.close()

    return render_template(
        "parking_spots.html",
        layout_grid=layout_grid,
        spots_by_number=spots_by_number,
        selected_date=selected_date,
        timedelta=timedelta,
        current_date=date.today(),
        current_user=current_user
    )




@app.route('/seed_parking_spots')
def seed_parking_spots():
    session = SessionLocal()
    for i in range(1, 97):
        spot = ParkingSpot(number=f"OS-{i}", area=Area.OLD_SCHOOL)
        session.add(spot)
    for i in range(1, 31):
        spot = ParkingSpot(number=f"SG-{i}", area=Area.SIDE_GATE)
        session.add(spot)
    session.commit()
    session.close()
    return "Seeded parking spots!"

@app.route('/real_tests')
@login_required
def real_tests():
    return render_template('real_tests.html')

# Route for user profile
@app.route('/profile')
@login_required
def user_profile():
    return render_template('user_profile.html')

@app.route('/practice', methods=['GET'])
@login_required
def practice_selection():
    session = SessionLocal()
    user = session.query(User).filter_by(id=current_user.id).first()
    tests = session.query(PracticeTest).all()

    attempts = {attempt.test_id: attempt for attempt in user.practice_attempts}
    session.close()
    return render_template('practice_selection.html', tests=tests, attempts=attempts)

@app.route('/practice/<int:test_id>', methods=['GET', 'POST'])
@login_required
def practice_quiz(test_id):
    session = SessionLocal()
    test = session.query(PracticeTest).filter_by(id=test_id).first()

    if not test:
        flash("Quiz not found.", "danger")
        session.close()
        return redirect(url_for('practice_selection'))

    if request.method == 'POST':
        questions = session.query(PracticeQuestion).filter_by(test_id=test_id).all()
        question_dict = {q.id: q for q in questions}
        score = 0
        feedback = {}

        for question_id_str, user_answer in request.form.items():
            if question_id_str == 'submit':
                continue
            question_id = int(question_id_str)
            question = question_dict.get(question_id)
            if not question:
                continue
            correct = user_answer == question.correct_answer
            if correct:
                score += 1
            option_labels = ['A', 'B', 'C', 'D']
            parsed_options = question.options.split(',')

                        # Map label to option (A: "Go", B: "Slow down", etc.)
            options_map = {label: text for label, text in zip(option_labels, parsed_options)}

            # Reverse map to find labels from answers
            reverse_options = {text.strip(): label for label, text in options_map.items()}

            feedback[question.id] = {
                'question_text': question.question,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'user_label': reverse_options.get(user_answer.strip(), None),
                'correct_label': reverse_options.get(question.correct_answer.strip(), None),
                'is_correct': correct,
                'options': options_map
            }
        
        attempt = PracticeAttempt(user_id=current_user.id, test_id=test_id, score=score)
        session.add(attempt)
        session.commit()
        session.close()

        flask_session['practice_feedback'] = feedback
        flask_session['practice_score'] = score
        return redirect(url_for('practice_results', test_id=test_id))

    all_questions = test.questions
    questions = random.sample(all_questions, min(20, len(all_questions)))

    # Add parsed options to each question
    for q in questions:
        q.parsed_options = q.options.split(",")

    session.close()
    return render_template('practice_quiz.html', test=test, questions=questions)

@app.route('/practice/<int:test_id>/results')
@login_required
def practice_results(test_id):
    feedback = flask_session.pop('practice_feedback', None)
    score = flask_session.pop('practice_score', None)
    if not feedback or score is None:
        flash("No quiz results to display.", "warning")
        return redirect(url_for('practice_selection'))

    return render_template('practice_results.html', test_id=test_id, feedback=feedback, score=score)


@app.cli.command("populate-practice-questions")
@with_appcontext
def populate_practice_questions():
    session = SessionLocal()

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
        test = PracticeTest(name=quiz_name, user_id=1)
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

    session.close()
    print("Practice tests with 20 unique questions each populated successfully.")



if __name__ == '__main__':
    app.run(debug=True)



