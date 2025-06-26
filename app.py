from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from database_setup import SessionLocal, User, EBike, PracticeTest, RealTest, ParkingSpot, PracticeAttempt, PracticeQuestion, RealTestAttempt, PracticeTest, ParkingReservation, RealTestQuestion
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
from database_setup import Base, engine, seed_data  # Import seed_data here



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

    # Restrict students who don't have a license
    if current_user.role == 'student':
        has_license = current_user.has_license  # already loaded by Flask-Login
        if not has_license:
            flash("You must pass the test and be approved by a teacher before registering an e-bike.", "warning")
            session.close()
            return redirect(url_for('dashboard'))

    form = forms.EbikeRegistrationForm()
    ebikes = session.query(EBike).filter_by(owner_id=current_user.id).all()

    # Check if the user has passed the real test (optional: you may remove this if not needed anymore)
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

    # Restrict unlicensed students
    if current_user.role == 'student' and not current_user.has_license:
        flash("You must be licensed by a teacher before reserving a parking spot.", "warning")
        session.close()
        return redirect(f'/parking_spots?date={selected_date_str}')

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

@app.route('/real-test', methods=['GET', 'POST'])
@login_required
def real_test():
    session = SessionLocal()

    if request.method == 'POST':
        submitted_answers = request.form
        test_id = submitted_answers.get('test_id')
        score = 0
        questions = session.query(RealTestQuestion).filter_by(test_id=test_id).all()
        feedback = []

        for question in questions:
            user_answer = submitted_answers.get(str(question.id))
            correct = user_answer == question.correct_answer
            if correct:
                score += 1
            feedback.append({
                'question': question.question_text,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'options': {
                    'A': question.option_a,
                    'B': question.option_b,
                    'C': question.option_c,
                    'D': question.option_d
                }
            })

        passed = score >= 18
        test_attempt = RealTestAttempt(
            user_id=current_user.id,
            test_id=test_id,
            passed=passed
        )
        session.add(test_attempt)
        session.commit()
        session.close()

        return render_template('real_test_results.html', score=score, passed=passed, feedback=feedback)

    # Create a new RealTest
    real_test = RealTest(user_id=current_user.id, name="Official eBike Safety Test")
    session.add(real_test)
    session.commit()

    # Sample 20 random practice questions
    practice_questions = session.query(PracticeQuestion).all()
    selected = []
    option_labels = ['A', 'B', 'C', 'D']

    for pq in random.sample(practice_questions, len(practice_questions)):
        if len(selected) >= 20:
            break

        options = [opt.strip() for opt in pq.options.split(",")]
        correct_answer = pq.correct_answer.strip()

        if correct_answer not in options:
            print(f"Skipping question: '{pq.question}' because correct answer '{correct_answer}' not in options: {options}")
            continue

        random.shuffle(options)
        try:
            correct_label = option_labels[options.index(correct_answer)]
        except ValueError:
            continue  # fallback if still problematic

        rtq = RealTestQuestion(
            test_id=real_test.id,
            question_text=pq.question,
            correct_answer=correct_label,
            option_a=options[0],
            option_b=options[1],
            option_c=options[2],
            option_d=options[3],
        )
        session.add(rtq)
        selected.append(rtq)

    session.commit()
    questions = session.query(RealTestQuestion).filter_by(test_id=real_test.id).all()
    session.close()
    return render_template('real_test.html', questions=questions, test_id=real_test.id, getattr=getattr)



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

@app.route('/approve_licenses', methods=['GET', 'POST'])
@login_required
def approve_licenses():
    if current_user.role != 'teacher':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard'))

    session = SessionLocal()
    # Get students who passed but aren't licensed
    passed_students = session.query(User).join(RealTestAttempt).filter(
        User.role == 'student',
        RealTestAttempt.passed == True,
        User.has_license == False
    ).distinct().all()

    if request.method == 'POST':
        approved_ids = request.form.getlist('approve')
        for student_id in approved_ids:
            student = session.query(User).get(int(student_id))
            if student:
                student.has_license = True
        session.commit()
        flash("Licenses approved!", "success")
        session.close()
        return redirect(url_for('approve_licenses'))

    session.close()
    return render_template('approve_licenses.html', students=passed_students)

@app.route('/license')
@login_required
def license_page():
    session = SessionLocal()

    # If user has passed the real test and has a license
    if current_user.has_license:
        session.close()
        return render_template('license_status.html')  # Optional: show 'Licensed!' message or renewal date

    # If user has passed test but not approved
    passed_test = session.query(RealTestAttempt).filter_by(user_id=current_user.id, passed=True).first()
    session.close()

    if passed_test:
        return render_template('license_status.html', awaiting_approval=True)

    # Redirect to real test if they haven't passed
    return redirect(url_for('real_test'))



@app.route('/practice/<int:test_id>/results')
@login_required
def practice_results(test_id):
    feedback = flask_session.pop('practice_feedback', None)
    score = flask_session.pop('practice_score', None)
    if not feedback or score is None:
        flash("No quiz results to display.", "warning")
        return redirect(url_for('practice_selection'))

    return render_template('practice_results.html', test_id=test_id, feedback=feedback, score=score)

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)  # Ensure tables exist
    seed_data()                             # Seed DB only if empty
    app.run(debug=True)



