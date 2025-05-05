from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from database_setup import SessionLocal, User, Task
import forms
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

# Route for the user dashboard, displaying tasks categorized by their status
@app.route('/dashboard')
@login_required
def dashboard():
    session = SessionLocal()
    try:
        # Get all tasks for the current user
        tasks = session.query(Task).filter_by(user_id=current_user.id).all()

        # Filter tasks into categories
        important_tasks = [task for task in tasks if task.important and not task.is_complete]
        tasks_due_today = [
            task for task in tasks
            if task.due_date and task.due_date == datetime.utcnow().date()
        ]
        upcoming_tasks = [
            task for task in tasks
            if task.due_date and task.due_date > datetime.utcnow().date() and not task.is_complete
        ]
        completed_tasks = [task for task in tasks if task.is_complete]

        # Calculate days_until_due for upcoming tasks
        today = datetime.utcnow().date()
        for task in upcoming_tasks:
            task.days_until_due = (task.due_date - today).days

    finally:
        session.close()  # Ensure session is closed even if an error occurs

    # Pass the filtered tasks to the template
    return render_template(
        'dashboard.html',
        important_tasks=important_tasks,
        tasks_due_today=tasks_due_today,
        upcoming_tasks=upcoming_tasks,
        completed_tasks=completed_tasks
    )

# Route for the user profile page, allowing profile and password updates
@app.route('/user_profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    profile_form = forms.ProfileUpdateForm()
    password_form = forms.PasswordUpdateForm()
    session = SessionLocal()
    
    try:
        # Get the current user from the database session
        user = session.query(User).get(current_user.id)
        
        if request.method == 'POST':
            if 'submit_profile' in request.form and profile_form.validate():
                # Check if username is already taken
                existing_user = session.query(User).filter(
                    User.username == profile_form.username.data,
                    User.id != current_user.id
                ).first()
                
                if existing_user:
                    flash('Username already taken.', 'danger')
                else:
                    # Update the user object in the session
                    user.username = profile_form.username.data
                    user.email = profile_form.email.data
                    session.commit()
                    flash('Profile updated successfully!', 'success')
                    
            elif 'submit_password' in request.form and password_form.validate():
                if check_password_hash(user.password, password_form.current_password.data):
                    # Update the password in the session
                    user.password = generate_password_hash(
                        password_form.new_password.data,
                        method='pbkdf2:sha256'
                    )
                    session.commit()
                    flash('Password updated successfully!', 'success')
                else:
                    flash('Current password is incorrect.', 'danger')

        # Get user statistics
        tasks = session.query(Task).filter_by(user_id=user.id).all()
        first_task = session.query(Task).filter_by(user_id=user.id).order_by(Task.created_at.asc()).first()
        
        stats = {
            "total_tasks": len(tasks),
            "completed_tasks": len([task for task in tasks if task.is_complete]),
            "first_task_date": first_task.created_at if first_task else None,
        }

        # Pre-populate the profile form with current user data
        if not profile_form.username.data:
            profile_form.username.data = user.username
            profile_form.email.data = user.email

    finally:
        session.close()

    return render_template('user_profile.html', 
                         profile_form=profile_form,
                         password_form=password_form,
                         stats=stats)

# Route for displaying tasks due today
@app.route('/todays_tasks')
@login_required
def todays_tasks():
    session = SessionLocal()
    today = datetime.now().date()
    tasks_due_today = session.query(Task).filter_by(user_id=current_user.id).filter(Task.due_date == today).all()
    session.close()
    
    return render_template('todays_tasks.html', tasks=tasks_due_today)

# Route for displaying the list of tasks and adding a new task
@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    form = forms.TaskForm()
    session = SessionLocal()

    # Check if a new task is being submitted
    if form.validate_on_submit():
        new_task = Task(
            title=form.title.data,
            category=form.category.data,
            due_date=form.due_date.data,
            user_id=current_user.id
        )
        session.add(new_task)
        session.commit()
        
        return redirect(url_for('tasks'))

    # Get sorting parameters from the request arguments, defaulting to 'due_date' and 'asc'
    sort_by = request.args.get('sort_by', 'due_date')
    order = request.args.get('order', 'asc')

    # Determine the column to sort by based on the `sort_by` parameter
    if sort_by == 'title':
        order_column = Task.title
    elif sort_by == 'category':
        order_column = Task.category
    else:
        order_column = Task.due_date  # Default to sorting by due date

    # Apply ordering based on the `order` parameter
    if order == 'desc':
        order_column = order_column.desc()

    # Query the tasks with sorting applied
    user_tasks = session.query(Task).filter_by(user_id=current_user.id).order_by(order_column).all()

    # Calculate days until due for each task
    current_date = datetime.now().date()
    tasks_with_days_until_due = [
        {
            'task': task,
            'days_until_due': (task.due_date - current_date).days if task.due_date else None
        }
        for task in user_tasks
    ]

    # Close the session
    session.close()

    # Render the template with tasks, current sorting parameters, and days until due
    return render_template(
        'tasks.html',
        form=form,
        tasks=tasks_with_days_until_due,
        sort_by=sort_by,
        order=order)

# Route for editing an existing task
@app.route('/tasks/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    session = SessionLocal()
    try:
        task = session.query(Task).get(task_id)
        
        # If the task doesn't exist or belongs to another user, redirect
        if not task or task.user_id != current_user.id:
            flash("Task not found or access denied!", "danger")
            return redirect(url_for('dashboard'))

        # Populate the form with the task data
        form = forms.TaskForm(obj=task)
        
        if form.validate_on_submit():
            # Update task fields with the new data from the form
            task.title = form.title.data
            task.category = form.category.data
            task.due_date = form.due_date.data
            task.description = form.description.data  # Ensure description is updated
            task.important = form.important.data  # Update important field
            
            session.commit()
            
            # Redirect to the task detail page with a success message
            flash("Task successfully updated!", "success")
            return redirect(url_for('task_detail', task_id=task.id))
        
    finally:
        session.close()
    
    # Render the edit task page with the form
    return render_template('edit_task.html', form=form, task=task)

# Route for deleting a task
@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    session = SessionLocal()
    task = session.query(Task).get(task_id)
    if task and task.user_id == current_user.id:
        session.delete(task)
        session.commit()
        
    session.close()
    return redirect(url_for('tasks'))

# Route for adding a new task
@app.route('/tasks/add', methods=['GET', 'POST'])
@login_required
def add_task():
    form = forms.TaskForm()
    if form.validate_on_submit():
        session = SessionLocal()
        try:
            # Create a new task using the form data
            new_task = Task(
                title=form.title.data,
                category=form.category.data,
                description=form.description.data,
                due_date=form.due_date.data,
                important=form.important.data,  # Include the important field
                user_id=current_user.id
            )
            session.add(new_task)
            session.commit()

            # Redirect to the newly created task's detail page
            flash("Task successfully created!", "success")
            return redirect(url_for('task_detail', task_id=new_task.id))
        
        finally:
            session.close()
    
    # Render the add task page with the form
    return render_template('add_task.html', form=form)

# Route for toggling task completion status
@app.route('/toggle_task_completion/<int:task_id>', methods=['POST'])
@login_required
def toggle_task_completion(task_id):
    session = SessionLocal()
    task = session.query(Task).get(task_id)
    if task and task.user_id == current_user.id:
        task.is_complete = not task.is_complete
        session.commit()
    
    session.close()
    
    # Get the return page and scroll position
    return_to = request.form.get('return_to', 'tasks')
    scroll_position = request.form.get('scroll_position', '0')
    
    # Return to the appropriate page with scroll position
    if return_to == 'todays_tasks':
        return redirect(url_for('todays_tasks', scroll=scroll_position))
    else:
        sort_by = request.form.get('sort_by', 'title')
        order = request.form.get('order', 'asc')
        return redirect(url_for('tasks', sort_by=sort_by, order=order, scroll=scroll_position))

# Route for displaying task details
@app.route('/task/<int:task_id>')
@login_required
def task_detail(task_id):
    session = SessionLocal()
    task = session.query(Task).filter_by(id=task_id, user_id=current_user.id).first()
    session.close()
    
    if task is None:
        flash('Task not found.', 'danger')
        return redirect(url_for('tasks'))
    
    return render_template('task_detail.html', task=task)

if __name__ == '__main__':
    app.run(debug=True)

