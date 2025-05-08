from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from database_setup import SessionLocal, User, EBike, PracticeTest, RealTest, ParkingSpot
import forms
from datetime import datetime

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

# Route for the dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    session = SessionLocal()
    ebike_count = session.query(EBike).filter_by(owner_id=current_user.id).count()
    completed_practice_tests = session.query(PracticeTest).filter_by(user_id=current_user.id, passed=True).count()
    total_tests = session.query(RealTest).filter_by(user_id=current_user.id).count()
    available_parking_spots = session.query(ParkingSpot).filter_by(is_occupied=False).count()
    session.close()
    return render_template(
        'dashboard.html',
        ebike_count=ebike_count,
        completed_practice_tests=completed_practice_tests,
        available_parking_spots=available_parking_spots,
        total_tests=total_tests
    )

# Route for e-bike management
@app.route('/ebikes', methods=['GET', 'POST'])
@login_required
def ebike_management():
    session = SessionLocal()
    ebikes = session.query(EBike).filter_by(owner_id=current_user.id).all()

    if not ebikes:  # If no e-bike is registered
        if request.method == 'POST':  # Handle the form submission for new e-bike registration
            # Assuming a form for registering an e-bike exists
            form = forms.EbikeRegistrationForm()
            if form.validate_on_submit():
                new_ebike = EBike(
                    owner_id=current_user.id,
                    model=form.model.data,
                    serial_number=form.serial_number.data,
                    # Remove registration_date as it's automatically handled by the database
)

                session.add(new_ebike)
                session.commit()
                flash('E-bike registered successfully!', 'success')
                return redirect(url_for('ebike_management'))
            return render_template('ebike_management.html', form=form)
        else:
            # If the user hasn't registered an e-bike, show the registration form
            form = forms.EbikeRegistrationForm()
            return render_template('ebike_management.html', form=form)
    
    session.close()
    return render_template('ebike_management.html', ebikes=ebikes)



# Route for parking overview
@app.route('/parking-spots')
@login_required
def parking_spots():
    session = SessionLocal()
    parking_spots = session.query(ParkingSpot).all()
    session.close()
    return render_template('parking_overview.html', parking_spots=parking_spots)

# Route for practice tests
@app.route('/practice-tests', methods=['GET', 'POST'])
@login_required
def practice_tests():
    form = forms.PracticeTestForm()
    if form.validate_on_submit():
        session = SessionLocal()
        practice_test = PracticeTest(
            user_id=current_user.id,
            score=form.score.data,
            passed=form.passed.data
        )
        session.add(practice_test)
        session.commit()
        session.close()
        flash('Practice test submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('practice_test.html', form=form)

# Route for real tests
@app.route('/real-tests', methods=['GET', 'POST'])
@login_required
def real_tests():
    form = forms.RealTestForm()
    if form.validate_on_submit():
        session = SessionLocal()
        real_test = RealTest(
            user_id=current_user.id,
            date=datetime.now(),
            score=form.score.data,
            passed=form.passed.data
        )
        session.add(real_test)
        session.commit()
        session.close()
        flash('Real test recorded successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('real_test.html', form=form)

# Route for user profile
@app.route('/profile')
@login_required
def user_profile():
    return render_template('user_profile.html')

if __name__ == '__main__':
    app.run(debug=True)

