# Basic HRMS (Human Resource Management System)

This project simulates a Basic HRMS (Human Resource Management System) with functionalities such as employee management, attendance tracking, and basic reporting. The tasks are designed to cover various aspects of development.

## Project Overview: HRMS Flask App

## Tasks:

### Set up the Flask App:

- Initialize a Flask application.
- Create necessary directories and files (templates, static, app.py, etc.).
- Implement a basic route for the home page ("/") with a welcome message.

### Employee Management:

- Create a database model for employees with attributes like name, designation, department, date of joining, etc.
- Create an API endpoint to add a new employee with basic information (name, address, email etc.)
- Create an API endpoint to retrieve the list of all employees.
- Implement a route to display the list of employees on the home page.

### Attendance Tracking:

- Add fields for attendance in the employee model.
- Create an API endpoint to mark attendance for a specific employee on a given date. (In time/Out Time)
- Create an API endpoint to retrieve attendance details for a specific employee.
- Display attendance details on the employee details page.

### Basic Reporting:

- Implement a route to show a simple report that displays the count of employees in each department.
- Use charts or tables to present the report.

### Documentation:

- Include docstrings for all functions and classes.
- Write a brief README.md file explaining the project structure, how to run the app locally, and any additional information.
- Include a README.md file with instructions on setting up and running the app.
- Ensure proper usage of docstrings, comments, and coding best practices.

## Requirements:

- Flask/Django Knowledge: How well the Flask app is structured and how effectively Flask features are used.
- API Development: Proper implementation of API endpoints and adherence to RESTful principles.
- Database Queries: Correct implementation of database queries using an ORM (e.g., SQLAlchemy, DjangoORM).
- Docstring Usage: Proper documentation of functions and classes using docstrings.
- Python Knowledge: Code readability, adherence to PEP 8, and effective use of Python features.

## Bonus - Complexities:

- Time and Space complexities dont add professional styles use standard css properties and all pages are fully responsiveness mediaqueries in all screens and all full working functionality

## Project Structure:

```
hrms-assignment/
├── app.py                 # Main Flask application with routes and API endpoints
├── models.py              # Database models (Employee, Attendance)
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .env.example          # Environment variables example
├── instance/             # Database storage
│   └── hrms.db          # SQLite database file
├── logs/                # Application logs
│   ├── hrms.log         # Main log file
│   ├── hrms.log.1       # Rotated log files
│   └── hrms.log.5
├── static/               # Static files
│   ├── css/
│   │   └── style.css     # Custom CSS styles
│   ├── js/
│   │   └── script.js     # JavaScript functionality
│   └── images/           # Image assets
├── templates/            # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Home page with employee list
│   ├── employee_details.html  # Employee details page
│   ├── reports.html      # Department reports page
│   └── error.html        # Error page template
└── tests/               # Test files
    ├── __init__.py
    └── test_app.py      # Application tests
```

## How It Works:

### 1. Application Setup
- The Flask application is initialized in `app.py` with database configuration
- SQLAlchemy is used for ORM to interact with SQLite database
- The application creates necessary database tables on first run

### 2. Employee Management
- **Home Page (`/`)**: Displays list of all employees with options to add new employees
- **Add Employee**: Modal form to add new employee with details (name, email, department, etc.)
- **Employee Details (`/employee/<id>`)**: Shows individual employee information and attendance records
- **API Endpoints**: RESTful APIs for CRUD operations on employees

### 3. Attendance Tracking
- **Mark Attendance**: For each employee, attendance can be marked with date, in-time, and out-time
- **Attendance History**: View all attendance records for a specific employee
- **Unique Records**: System prevents duplicate attendance entries for same employee on same date

### 4. Reporting System
- **Department Reports (`/reports`)**: Shows employee count by department
- **Visual Charts**: Interactive pie chart using Chart.js for department distribution
- **Summary Cards**: Display total employees, departments, and average employees per department
- **Detailed Tables**: Show department-wise breakdown with percentages

### 5. User Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern UI**: Clean interface with Font Awesome icons
- **Interactive Elements**: Modals, hover effects, and smooth transitions
- **Navigation**: Easy access to all sections from any page

### 6. Database Schema
- **Employees Table**: Stores employee information (id, name, email, department, etc.)
- **Attendance Table**: Stores attendance records (employee_id, date, in_time, out_time)
- **Relationships**: One-to-many relationship between employees and attendance records

### 7. API Endpoints
- `GET /api/v1/employees` - Get all employees
- `POST /api/v1/employees` - Add new employee
- `POST /api/attendance/<employee_id>` - Mark attendance
- `GET /api/attendance/<employee_id>` - Get employee attendance
- `POST /api/add-employee-simple` - Simple add employee endpoint

### 8. Error Handling
- Custom error pages for better user experience
- Form validation for data integrity
- Database error handling with user-friendly messages

## How to Run:

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd hrms-assignment

# Or download and extract the project folder
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables (Optional)
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env file with your settings (optional for development)
```

### Step 5: Run the Application
```bash
python app.py
```

### Step 6: Access the Application
- Open your web browser and go to: `http://localhost:5000`
- The application will start automatically and create the database if it doesn't exist

### Troubleshooting:
- **Port 5000 already in use**: The app will automatically try alternative ports (5001, 5002, etc.)
- **Database errors**: Delete the `instance/hrms.db` file and restart the application
- **Dependencies issues**: Make sure you're using the virtual environment and run `pip install -r requirements.txt` again

## How to Check API Endpoints in Browser:

### 1. GET Endpoints (Easy to Test in Browser)
You can directly open these URLs in your browser:

#### Get All Employees
```
http://localhost:5000/api/v1/employees
```
- Returns a JSON array of all employees
- Shows employee details like name, email, department, etc.

#### Get Employee Attendance
```
http://localhost:5000/api/attendance/1
```
- Replace `1` with actual employee ID
- Returns attendance records for that specific employee

#### Alternative Simple Add Employee (POST only)
```
http://localhost:5000/api/add-employee-simple
```
- Simple endpoint to add employee without complex validation
- Only accepts POST requests

### 2. POST Endpoints (Need Browser Extensions or Tools)
POST endpoints require special tools since browsers can't easily send POST requests with JSON data:

#### Option A: Browser Extensions
- Install **Postman** (Chrome Extension) or **REST Client** extensions
- Set method to POST
- Set URL to `http://localhost:5000/api/v1/employees` or `http://localhost:5000/api/attendance/1`
- Add JSON data in request body

#### Option B: Using Browser Developer Console
1. Open your browser (F12 or Ctrl+Shift+I)
2. Go to Console tab
3. Use JavaScript fetch() to test POST requests:

```javascript
// Add new employee
fetch('http://localhost:5000/api/v1/employees', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        name: 'Test Employee',
        email: 'test@example.com',
        department: 'IT',
        designation: 'Developer'
    })
})
.then(response => response.json())
.then(data => console.log(data));

// Mark attendance (replace 1 with employee ID)
fetch('http://localhost:5000/api/attendance/1', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        date: '2024-01-25',
        in_time: '09:00',
        out_time: '18:00'
    })
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Option C: Using curl Command
```bash
# Add new employee
curl -X POST http://localhost:5000/api/v1/employees \
-H "Content-Type: application/json" \
-d '{"name":"Test Employee","email":"test@example.com","department":"IT"}'

# Mark attendance
curl -X POST http://localhost:5000/api/attendance/1 \
-H "Content-Type: application/json" \
-d '{"date":"2024-01-25","in_time":"09:00","out_time":"18:00"}'
```

### 3. Expected Responses

#### Successful Employee Addition
```json
{
    "message": "Employee added successfully",
    "employee_id": 5
}
```

#### Successful Attendance Marking
```json
{
    "message": "Attendance marked successfully"
}
```

#### Error Responses
```json
{
    "error": "Email already exists"
}
```

### 4. Testing Tips
- **Start the application first**: Make sure `python app.py` is running
- **Check port**: If using alternative ports, update URLs accordingly (e.g., `http://localhost:5001`)
- **Verify data**: After POST requests, refresh the GET endpoints to see new data
- **Browser refresh**: Use Ctrl+F5 to hard refresh and avoid cached responses
