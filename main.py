from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request
from datetime import datetime
from datetime import timedelta
from flask import request, redirect, url_for, render_template

# Set up Flask app and login manager
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key12345asdfg' 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect to login page if user is not authenticated

# Route for the welcome page, sends you to that when you load the app
@app.route('/')
def welcome():
    return render_template('welcome.html')

# Session management function which retrieves the user from the database
@login_manager.user_loader
def load_user(user_id):
    session = SessionLocal()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

# Route for registering a new user, sending you to the register page
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit(): # Handles the process of registering a new user 
        session = SessionLocal()  # including form validation, password hashing, database interaction, and error handling
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

# Route for logging in an existing user, handling the login process
# including form validation, password checking, and session management
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



if __name__ == '__main__':
    app.run(debug=True)
