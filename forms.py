from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, DateField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from wtforms import SelectField, BooleanField

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


# Form for task creation and editing
class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    category = SelectField(
        'Category',
        choices=[('Study', 'Study'), ('Exam', 'Exam'), ('Sport', 'Sport'), 
                 ('Social', 'Social'), ('Other', 'Other')],
        validators=[DataRequired()])
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Add Task')
    important = BooleanField('Important') 

class ProfileUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=150)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit_profile = SubmitField('Update Profile')

class PasswordUpdateForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit_password = SubmitField('Update Password')

