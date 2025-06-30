



# eBike Safety Management System

A comprehensive web application for managing eBike safety, testing, and licensing in educational institutions. Built with Flask, SQLAlchemy, HTML, CSS, and JavaScript, this system provides a complete solution for eBike registration, safety testing, incident reporting, and parking management.

This eBike Safety Management System was created for Year 12 Software Development assessment, demonstrating advanced web application development skills and database management.

## Features

### Student Features
- **Practice Tests**: Take unlimited practice safety tests with randomized questions
- **Real Safety Tests**: Official licensing tests with pass/fail results
- **eBike Registration**: Register and manage personal eBikes after obtaining license
- **Parking Reservations**: Reserve parking spots using an interactive grid system
- **Incident Reporting**: Report safety incidents or unsafe behavior
- **License Status Tracking**: Monitor test progress and license approval status
- **Personal Dashboard**: View statistics, progress, and quick actions

### Teacher/Admin Features
- **License Management**: Approve student licenses after test completion
- **Incident Management**: Review, investigate, and resolve incident reports
- **System Analytics**: View comprehensive statistics and user activity
- **Practice Test Oversight**: Monitor student performance and test statistics
- **eBike Registration Oversight**: Review all student eBike registrations
- **Database Management**: Migrate and seed database with test questions

### System Features
- **Role-Based Access Control**: Separate interfaces for students and teachers
- **Responsive Design**: Modern, mobile-friendly interface
- **Real-time Updates**: Dynamic content and instant feedback
- **Data Security**: Secure authentication and session management
- **Excel Integration**: Parking layout configuration via Excel files
- **Comprehensive Testing**: 60+ safety questions across 3 practice tests

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Forms**: Flask-WTF with WTForms validation
- **Authentication**: Flask-Login with password hashing
- **Data Processing**: Pandas for Excel file handling
- **Security**: CSRF protection, secure session management

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Instructions

1. **Clone or download the repository**
   ```bash
   git clone [your-repository-url]
   cd "major project"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   - Open your web browser
   - Navigate to `http://localhost:5000`
   - Register a new account or use existing credentials

### First Time Setup
- The application will automatically create the database and seed it with initial data
- Register as either a student or teacher to access role-specific features
- Teachers can access the database migration tool at `/admin/migrate_database` if needed

## Usage

### For Students
1. **Register an account** with role "Student"
2. **Take practice tests** to prepare for the official test
3. **Take the real safety test** when ready (requires 18/20 to pass)
4. **Wait for teacher approval** of your license
5. **Register your eBike** once licensed
6. **Reserve parking spots** using the interactive map
7. **Report incidents** if necessary

### For Teachers
1. **Register an account** with role "Teacher"
2. **Approve student licenses** after they pass the real test
3. **Manage incident reports** - review, investigate, and resolve
4. **Monitor system statistics** via the admin dashboard
5. **Oversee eBike registrations** and student progress
6. **Create incident reports** for administrative purposes

## Project Structure

```
major project/
├── app.py                 # Main Flask application
├── database_setup.py      # Database models and seeding
├── forms.py              # WTForms form definitions
├── requirements.txt      # Python dependencies
├── Map.xlsx             # Parking layout configuration
├── static/
│   ├── styles.css       # Custom CSS styling
│   └── images/          # Application images
└── templates/           # Jinja2 HTML templates
    ├── base.html        # Base template
    ├── dashboard.html   # Student dashboard
    ├── admin_*.html     # Admin templates
    └── ...              # Other page templates
```
## Database Schema

The application uses SQLAlchemy ORM with the following main models:

- **User**: Student and teacher accounts with role-based permissions
- **EBike**: eBike registration details linked to users
- **PracticeTest/PracticeQuestion**: Practice test content and structure
- **RealTest/RealTestQuestion**: Official licensing test content
- **PracticeAttempt/RealTestAttempt**: Test attempt records and scores
- **ParkingSpot/ParkingReservation**: Parking management system
- **IncidentReport**: Safety incident tracking and management

## Key Features Explained

### Safety Testing System
- **Practice Tests**: 3 comprehensive tests with 20 questions each
- **Randomized Questions**: Questions and answer options are shuffled for each attempt
- **Progress Tracking**: Students can see their best scores and completion rates
- **Real Test**: Official test using randomized questions from practice pool
- **Pass Threshold**: 18/20 (90%) required to pass the real test

### Parking Management
- **Interactive Grid**: Visual parking layout loaded from Excel file
- **Real-time Availability**: Shows current reservations and available spots
- **Date-based Reservations**: Students can book spots for future dates
- **Conflict Prevention**: Prevents double-booking and past-date reservations

### Incident Reporting
- **Comprehensive Forms**: Detailed incident reporting with severity levels
- **Admin Workflow**: Teachers can review, investigate, and resolve incidents
- **Status Tracking**: Open, Under Investigation, Resolved, Dismissed statuses
- **User History**: Students can view incidents they've been involved in

## Contributing

This is a student project created for HSC Software Development assessment. However, suggestions and feedback are welcome!

For bugs, feature suggestions, or improvements:
1. Review the code structure and documentation
2. Test the application thoroughly
3. Provide detailed feedback on functionality and user experience

## Future Enhancements

Potential improvements for the system:
- Email notifications for license approvals and incident updates
- Mobile app companion for quick parking spot checks
- Advanced analytics dashboard with charts and graphs
- Integration with school management systems
- Multi-language support for diverse student populations

## Assessment Context

This project demonstrates:
- **Advanced Web Development**: Complex Flask application with multiple routes and features
- **Database Design**: Normalized relational database with proper relationships
- **User Interface Design**: Responsive, modern web interface with excellent UX
- **Security Implementation**: Authentication, authorization, and data protection
- **Code Quality**: Clean, well-documented, and maintainable codebase
- **Testing and Validation**: Comprehensive form validation and error handling

## License

This project is created for educational purposes as part of HSC Software Development assessment.

For educational use and reference only.

