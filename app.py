from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from database_setup import SessionLocal, User, EBike, PracticeTest, RealTest, ParkingSpot, PracticeAttempt, PracticeQuestion, RealTestAttempt, PracticeTest
import forms
from datetime import datetime
from forms import PracticeQuizForm
from flask import Flask
from flask.cli import with_appcontext
from database_setup import SessionLocal, PracticeTest, PracticeQuestion
import click
import random



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

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        session = SessionLocal()
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(
            username=form.username.data,
            email=form.email.data, 
            password=hashed_password
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


@app.route('/parking_spots')
@login_required
def parking_spots():
    session = SessionLocal()
    spots = session.query(ParkingSpot).all()
    session.close()
    return render_template('parking_spots.html', spots=spots)

@app.route('/real_tests')
@login_required
def real_tests():
    return render_template('real_tests.html')

# Route for user profile
@app.route('/profile')
@login_required
def user_profile():
    return render_template('user_profile.html')

# Practice Quiz Selection Page
@app.route('/practice', methods=['GET'])
@login_required
def practice_selection():
    session = SessionLocal()
    # Fetch all practice tests
    tests = session.query(PracticeTest).all()
    attempts = {attempt.test_id: attempt for attempt in current_user.practice_attempts}
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

    # Get 20 random questions for this test
    questions = random.sample(test.questions, min(20, len(test.questions)))
    form = PracticeQuizForm()
    form.question.choices = []  # Clear existing choices

    # Populate form choices if GET request
    if request.method == 'GET':
        for question in questions:
            form.question.choices.append((question.id, f"{question.question_text}\nA. {question.option_a}  B. {question.option_b}  C. {question.option_c}  D. {question.option_d}"))
        session.close()
        return render_template('practice_quiz.html', form=form, test=test)

    # Handle form submission
    if form.validate_on_submit():
        score = 0
        for question in questions:
            selected_answer = request.form.get(str(question.id))
            if selected_answer == question.correct_answer:
                score += 1
        
        # Record the attempt
        attempt = PracticeAttempt(user_id=current_user.id, test_id=test_id, score=score)
        session.add(attempt)
        session.commit()
        session.close()

        flash(f"You scored {score}/{len(questions)}", "success")
        return redirect(url_for('practice_selection'))
    
    flash("Please answer all questions.", "danger")
    session.close()
    return render_template('practice_quiz.html', form=form, test=test)


# CLI command to populate practice quizzes
@app.cli.command("populate-practice-questions")
@with_appcontext
def populate_practice_questions():
    session = SessionLocal()
    quiz_names = ["Basic E-Bike Safety", "Traffic Rules and Signs", "E-Bike Maintenance", "Emergency Handling", "Advanced E-Bike Knowledge"]
    for quiz_name in quiz_names:
        test = PracticeTest(name=quiz_name, user_id=1)  # Assuming user_id 1 exists
        session.add(test)
        session.commit()
        for _ in range(30):  # 30 questions per test for variety
            question = PracticeQuestion(
                test_id=test.id,
                question_text="Sample question for {}?".format(quiz_name),
                option_a="Option A",
                option_b="Option B",
                option_c="Option C",
                option_d="Option D",
                correct_answer="A"
            )
            session.add(question)
        session.commit()
    session.close()
    print("Practice tests and questions populated successfully.")

if __name__ == '__main__':
    app.run(debug=True)

