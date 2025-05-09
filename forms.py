from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, RadioField, TextAreaField, DateField, IntegerField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, NumberRange
from flask_wtf import FlaskForm
from wtforms.fields import DateTimeField
from datetime import datetime


# Form for user login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Form for user registration
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

# Form for profile updates
class ProfileUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit_profile = SubmitField('Update Profile')

# Form for password updates
class PasswordUpdateForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit_password = SubmitField('Update Password')

class EbikeRegistrationForm(FlaskForm):
    model = StringField('E-Bike Model', validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[DataRequired()])
    submit = SubmitField('Register E-Bike')
    registration_date = DateTimeField('Registration Date', default=datetime.utcnow, format='%Y-%m-%d %H:%M:%S')
    
class PracticeQuizForm(FlaskForm):
    question = RadioField('Select the correct answer:', choices=[], validators=[DataRequired()])
    submit = SubmitField('Submit')
