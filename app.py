"""
HRMS (Human Resource Management System) Flask Application

This application provides employee management, attendance tracking, and reporting
functionalities for HR departments.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import os
import re
import html
import logging
from logging.handlers import RotatingFileHandler
import uuid
from functools import wraps

# Initialize Flask application
app = Flask(__name__, static_folder='static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hrms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 120,
    'pool_pre_ping': True
}
app.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'application/json', 'text/javascript']
app.config['COMPRESS_LEVEL'] = 6
app.config['COMPRESS_MIN_SIZE'] = 500

# Configure logging
class SafeRotatingFileHandler(RotatingFileHandler):
    def doRollover(self):
        try:
            super().doRollover()
        except PermissionError:
            return()

is_debug_mode = (
    os.environ.get('FLASK_DEBUG') == '1'
    or os.environ.get('FLASK_ENV') == 'development'
    or __name__ == '__main__'
)

if not is_debug_mode:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    try:
        file_handler = SafeRotatingFileHandler('logs/hrms.log', maxBytes=10240, backupCount=5, delay=True)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not set up file logging: {e}")
        print("Using console logging instead")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s'
        )
else:
    # In debug mode, log to console only to avoid file permission issues
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s'
    )

# Only log startup in non-debug mode to avoid file permission errors
if not is_debug_mode:
    app.logger.info('HRMS startup')

import uuid
from functools import wraps

# Request tracking middleware
@app.before_request
def before_request():
    """Generate unique request ID for tracking"""
    g.request_id = str(uuid.uuid4())
    g.start_time = datetime.utcnow()

@app.after_request
def request_headers(response):
    """Add request tracking and CORS headers"""
    # Request tracking
    if hasattr(g, 'start_time'):
        duration = (datetime.utcnow() - g.start_time).total_seconds()
        response.headers['X-Request-ID'] = getattr(g, 'request_id', 'unknown')
        response.headers['X-Response-Time'] = f"{duration:.3f}s"
        app.logger.info(f'Request {getattr(g, "request_id", "unknown")} completed in {duration:.3f}s')
    
    # CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    
    # Add caching headers for API responses
    if request.endpoint and request.endpoint.startswith('api_'):
        response.cache_control.no_cache = True
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    else:
        # Cache static content for 1 hour
        response.headers['Cache-Control'] = 'public, max-age=3600'
    
    return response

# Initialize database and migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)
csrf = CSRFProtect(app)
compress = Compress(app)

# Initialize rate limiter (commented out for now to fix startup)
# limiter = Limiter(
#     app,
#     key_func=get_remote_address,
#     default_limits=["200 per day", "50 per hour"]
# )

# Define models here to avoid circular import
class Employee(db.Model):
    """Employee model representing employee information in the HRMS."""
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20), index=True)
    designation = db.Column(db.String(100), index=True)
    department = db.Column(db.String(100), index=True)
    date_of_joining = db.Column(db.Date, default=date.today, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    attendance = db.relationship('Attendance', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_employee_name_dept', 'name', 'department'),
        db.Index('idx_employee_email_dept', 'email', 'department'),
    )
    
    def __repr__(self):
        return f'<Employee {self.name}>'

class Attendance(db.Model):
    """Attendance model tracking employee check-in and check-out times."""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    in_time = db.Column(db.Time, index=True)
    out_time = db.Column(db.Time, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date', name='unique_employee_date'),
        db.CheckConstraint('out_time > in_time', name='check_time_order'),
        db.Index('idx_attendance_employee_date', 'employee_id', 'date'),
        db.Index('idx_attendance_date_range', 'date', 'in_time', 'out_time'),
    )
    
    def __repr__(self):
        return f'<Attendance Employee:{self.employee_id} Date:{self.date}>'
    
    @property
    def working_hours(self):
        """Calculate total working hours for the day."""
        if self.in_time and self.out_time:
            in_datetime = datetime.combine(date.today(), self.in_time)
            out_datetime = datetime.combine(date.today(), self.out_time)
            diff = out_datetime - in_datetime
            return diff.total_seconds() / 3600
        return None

@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        JSON response with health status
    """
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'database': 'connected'
        }), 200
    except Exception as e:
        app.logger.error(f'Health check failed: {str(e)}')
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 503

@app.route('/metrics')
def metrics():
    """
    Basic metrics endpoint for monitoring.
    
    Returns:
        JSON response with application metrics
    """
    try:
        employee_count = Employee.query.count()
        attendance_count = Attendance.query.count()
        
        return jsonify({
            'employees': employee_count,
            'attendance_records': attendance_count,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        app.logger.error(f'Metrics endpoint failed: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/')
def home():
    """
    Home page route that displays welcome message and employee list.
    
    Returns:
        Rendered HTML template for home page
    """
    try:
        # Optimize query with only needed fields and limit
        employees = Employee.query.options(
            db.load_only(Employee.id, Employee.name, Employee.email, 
                      Employee.department, Employee.designation, Employee.date_of_joining)
        ).order_by(Employee.created_at.asc()).limit(100).all()
        
        return render_template('index.html', employees=employees)
    except Exception as e:
        app.logger.error(f'Error loading home page: {str(e)}')
        return render_template('error.html', error='Failed to load data'), 500

# API versioning
API_VERSION = 'v1'

@app.route(f'/api/{API_VERSION}/employees', methods=['GET'])
def get_employees():
    """
    API endpoint to retrieve all employees.
    
    Returns:
        JSON response with list of employees
    """
    try:
        # Add pagination support
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = Employee.query
        if search:
            query = query.filter(
                Employee.name.contains(search) |
                Employee.email.contains(search) |
                Employee.department.contains(search)
            )
        
        # Paginate results
        employees_pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        employees = [{
            'id': emp.id,
            'name': emp.name,
            'email': emp.email,
            'designation': emp.designation,
            'department': emp.department,
            'date_of_joining': emp.date_of_joining.strftime('%Y-%m-%d') if emp.date_of_joining else None,
            'created_at': emp.created_at.isoformat() if emp.created_at else None
        } for emp in employees_pagination.items]
        
        return jsonify({
            'employees': employees,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': employees_pagination.total,
                'pages': employees_pagination.pages,
                'has_next': employees_pagination.has_next,
                'has_prev': employees_pagination.has_prev
            },
            'api_version': API_VERSION
        })
        
    except Exception as e:
        app.logger.error(f'Error retrieving employees: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

def sanitize_input(data: Any) -> Any:
    """
    Sanitize input data to prevent XSS attacks.
    
    Args:
        data: Input data to sanitize (str, dict, or list)
        
    Returns:
        Sanitized data with HTML entities escaped
    """
    if isinstance(data, str):
        return html.escape(data.strip())
    elif isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

@app.route('/api/add-employee-simple', methods=['POST'])
@csrf.exempt  # Disable CSRF protection for this endpoint
def add_employee_simple():
    """Simple endpoint to add employee without complex validation"""
    try:
        print("DEBUG: Simple endpoint called")
        data = request.get_json()
        print("DEBUG: Received data:", data)
        
        if not data:
            print("DEBUG: No data received")
            return jsonify({'error': 'No data received'}), 400
            
        # Create employee with minimal validation
        employee = Employee(
            name=data.get('name', 'Unknown'),
            email=data.get('email', 'unknown@example.com'),
            address=data.get('address', ''),
            phone=data.get('phone', ''),
            designation=data.get('designation', ''),
            department=data.get('department', ''),
            date_of_joining=date.today()
        )
        
        db.session.add(employee)
        db.session.commit()
        
        print("DEBUG: Employee created successfully")
        return jsonify({
            'message': 'Employee added successfully',
            'employee_id': employee.id
        }), 201
        
    except Exception as e:
        print("DEBUG: Error:", str(e))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route(f'/api/{API_VERSION}/employees', methods=['POST'])
def add_employee() -> Dict[str, Any]:
    """
    API endpoint to add a new employee.
    
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        if not data.get('name') or not data.get('name').strip():
            return jsonify({'error': 'Name is required and cannot be empty'}), 400
            
        if len(data.get('name', '').strip()) > 100:
            return jsonify({'error': 'Name cannot exceed 100 characters'}), 400
            
        if not data.get('email') or not data.get('email').strip():
            return jsonify({'error': 'Email is required and cannot be empty'}), 400
            
        if len(data.get('email', '').strip()) > 120:
            return jsonify({'error': 'Email cannot exceed 120 characters'}), 400
            
        # Validate address length
        if data.get('address') and len(data.get('address', '').strip()) > 500:
            return jsonify({'error': 'Address cannot exceed 500 characters'}), 400
            
        # Validate phone length
        if data.get('phone') and len(data.get('phone', '').strip()) > 20:
            return jsonify({'error': 'Phone cannot exceed 20 characters'}), 400
            
        # Validate designation length
        if data.get('designation') and len(data.get('designation', '').strip()) > 100:
            return jsonify({'error': 'Designation cannot exceed 100 characters'}), 400
            
        # Validate department length
        if data.get('department') and len(data.get('department', '').strip()) > 100:
            return jsonify({'error': 'Department cannot exceed 100 characters'}), 400
            
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email'].strip()):
            return jsonify({'error': 'Invalid email format'}), 400
            
        # Validate phone number if provided
        if data.get('phone') and data['phone'].strip():
            phone_pattern = r'^[\d\s\-\+\(\)]+$'
            if not re.match(phone_pattern, data['phone'].strip()):
                return jsonify({'error': 'Invalid phone number format'}), 400
        
        # Check for duplicate email
        existing_employee = Employee.query.filter_by(email=data['email'].strip()).first()
        if existing_employee:
            return jsonify({'error': 'Email already exists'}), 409
        
        # Create new employee
        try:
            # Sanitize input data
            sanitized_data = sanitize_input(data)
            
            employee = Employee(
                name=sanitized_data['name'],
                email=sanitized_data['email'],
                address=sanitized_data.get('address', ''),
                phone=sanitized_data.get('phone', ''),
                designation=sanitized_data.get('designation', ''),
                department=sanitized_data.get('department', ''),
                date_of_joining=datetime.strptime(sanitized_data['date_of_joining'], '%Y-%m-%d').date() if sanitized_data.get('date_of_joining') and sanitized_data['date_of_joining'].strip() else date.today()
            )
            
            db.session.add(employee)
            db.session.commit()
            
            return jsonify({
                'message': 'Employee added successfully',
                'employee_id': employee.id
            }), 201
            
        except ValueError as e:
            db.session.rollback()
            app.logger.error(f'Date validation error: {str(e)}')
            return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Database error while creating employee: {str(e)}')
            return jsonify({'error': 'Internal server error'}), 500
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Unexpected error in add_employee: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/delete-employee/<int:employee_id>', methods=['DELETE'])
@csrf.exempt  # Disable CSRF protection for this endpoint
def delete_employee(employee_id):
    """API endpoint to delete an employee"""
    try:
        print("DEBUG: Delete endpoint called for employee ID:", employee_id)
        
        employee = Employee.query.get(employee_id)
        if not employee:
            print("DEBUG: Employee not found")
            return jsonify({'error': 'Employee not found'}), 404
        
        print("DEBUG: Found employee:", employee.name)
        
        # Delete related attendance records first
        Attendance.query.filter_by(employee_id=employee_id).delete()
        
        # Delete the employee
        db.session.delete(employee)
        db.session.commit()
        
        print("DEBUG: Employee deleted successfully")
        return jsonify({'message': 'Employee deleted successfully'}), 200
        
    except Exception as e:
        print("DEBUG: Delete error:", str(e))
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance/<int:attendance_id>', methods=['PUT'])
@csrf.exempt  # Disable CSRF protection for this endpoint
def update_attendance(attendance_id):
    """
    API endpoint to update an existing attendance record.
    
    Args:
        attendance_id: ID of the attendance record to update
        
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        if not data.get('date'):
            return jsonify({'error': 'Date is required'}), 400
            
        # Validate date format
        try:
            attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
        # Validate date is not in future
        if attendance_date > date.today():
            return jsonify({'error': 'Date cannot be in the future'}), 400
            
        # Validate time format if provided
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        if data.get('in_time') and not re.match(time_pattern, data['in_time']):
            return jsonify({'error': 'Invalid in_time format. Use HH:MM'}), 400
            
        if data.get('out_time') and not re.match(time_pattern, data['out_time']):
            return jsonify({'error': 'Invalid out_time format. Use HH:MM'}), 400
            
        # Validate time logic
        if data.get('in_time') and data.get('out_time'):
            in_time = datetime.strptime(data['in_time'], '%H:%M').time()
            out_time = datetime.strptime(data['out_time'], '%H:%M').time()
            if out_time <= in_time:
                return jsonify({'error': 'Out time must be after in time'}), 400
        
        # Find existing attendance record
        attendance = Attendance.query.get_or_404(attendance_id)
        
        # Update attendance record
        attendance.date = attendance_date
        attendance.in_time = datetime.strptime(data['in_time'], '%H:%M').time() if data.get('in_time') else None
        attendance.out_time = datetime.strptime(data['out_time'], '%H:%M').time() if data.get('out_time') else None
        attendance.updated_at = datetime.utcnow()
        db.session.commit()
        app.logger.info(f'Updated attendance record {attendance_id} for employee {attendance.employee_id}')
        
        return jsonify({'message': 'Attendance updated successfully'}), 200
        
    except ValueError as e:
        db.session.rollback()
        app.logger.error(f'Attendance validation error: {str(e)}')
        return jsonify({'error': f'Invalid time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Database error while updating attendance: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/attendance/<int:employee_id>', methods=['POST'])
@csrf.exempt  # Disable CSRF protection for this endpoint
def mark_attendance(employee_id):
    """
    API endpoint to mark attendance for an employee.
    
    Args:
        employee_id: ID of the employee
        
    Returns:
        JSON response with success/error message
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        if not data.get('date'):
            return jsonify({'error': 'Date is required'}), 400
            
        # Validate date format
        try:
            attendance_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            
        # Validate date is not in future
        if attendance_date > date.today():
            return jsonify({'error': 'Date cannot be in the future'}), 400
            
        # Validate time format if provided
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        if data.get('in_time') and not re.match(time_pattern, data['in_time']):
            return jsonify({'error': 'Invalid in_time format. Use HH:MM'}), 400
            
        if data.get('out_time') and not re.match(time_pattern, data['out_time']):
            return jsonify({'error': 'Invalid out_time format. Use HH:MM'}), 400
            
        # Validate time logic
        if data.get('in_time') and data.get('out_time'):
            in_time = datetime.strptime(data['in_time'], '%H:%M').time()
            out_time = datetime.strptime(data['out_time'], '%H:%M').time()
            if out_time <= in_time:
                return jsonify({'error': 'Out time must be after in time'}), 400
        
        # Check if employee exists
        employee = Employee.query.get_or_404(employee_id)
        
        # Check if attendance already exists for this date
        existing_attendance = Attendance.query.filter_by(
            employee_id=employee_id,
            date=attendance_date
        ).first()
        
        if existing_attendance:
            # Update existing attendance
            existing_attendance.in_time = datetime.strptime(data['in_time'], '%H:%M').time() if data.get('in_time') else None
            existing_attendance.out_time = datetime.strptime(data['out_time'], '%H:%M').time() if data.get('out_time') else None
            existing_attendance.updated_at = datetime.utcnow()
            
            # Check if values actually changed to avoid unnecessary updates
            if (existing_attendance.in_time != datetime.strptime(data['in_time'], '%H:%M').time() if data.get('in_time') else None or 
                existing_attendance.out_time != datetime.strptime(data['out_time'], '%H:%M').time() if data.get('out_time') else None):
                
                db.session.commit()
                app.logger.info(f'Updated attendance for employee {employee_id} on {attendance_date}')
                return jsonify({'message': 'Attendance updated successfully'}), 200
            else:
                return jsonify({'message': 'No changes detected'}), 200
        else:
            # Create new attendance record
            attendance = Attendance(
                employee_id=employee_id,
                date=attendance_date,
                in_time=datetime.strptime(data['in_time'], '%H:%M').time() if data.get('in_time') else None,
                out_time=datetime.strptime(data['out_time'], '%H:%M').time() if data.get('out_time') else None
            )
            db.session.add(attendance)
            db.session.commit()
            app.logger.info(f'Created attendance for employee {employee_id} on {attendance_date}')
        
        return jsonify({'message': 'Attendance marked successfully'}), 200
        
    except ValueError as e:
        db.session.rollback()
        app.logger.error(f'Attendance validation error: {str(e)}')
        return jsonify({'error': f'Invalid time format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Database error while marking attendance: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/attendance/<int:employee_id>', methods=['GET'])
def get_attendance(employee_id):
    """
    API endpoint to retrieve attendance details for an employee.
    
    Args:
        employee_id: ID of the employee
        
    Returns:
        JSON response with attendance records
    """
    try:
        # Validate employee exists
        employee = Employee.query.filter_by(id=employee_id).first()
        if not employee:
            return jsonify({'error': 'Employee not found'}), 404
        
        # Get attendance records with pagination
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100 records
        
        attendance_query = Attendance.query.filter_by(employee_id=employee_id).order_by(Attendance.date.desc())
        attendance_pagination = attendance_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        attendance_records = [{
            'date': record.date.strftime('%Y-%m-%d'),
            'in_time': record.in_time.strftime('%H:%M') if record.in_time else None,
            'out_time': record.out_time.strftime('%H:%M') if record.out_time else None,
            'working_hours': round(record.working_hours, 2) if record.working_hours else None
        } for record in attendance_pagination.items]
        
        return jsonify({
            'attendance': attendance_records,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': attendance_pagination.total,
                'pages': attendance_pagination.pages,
                'has_next': attendance_pagination.has_next,
                'has_prev': attendance_pagination.has_prev
            }
        })
        
    except Exception as e:
        app.logger.error(f'Error retrieving attendance for employee {employee_id}: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/employee/<int:employee_id>')
def employee_details(employee_id):
    """
    Route to display employee details with attendance.
    
    Args:
        employee_id: ID of the employee
        
    Returns:
        Rendered HTML template for employee details
    """
    employee = Employee.query.get_or_404(employee_id)
    attendance_records = Attendance.query.filter_by(employee_id=employee_id).order_by(Attendance.date.desc()).all()
    return render_template('employee_details.html', employee=employee, attendance_records=attendance_records)

@app.route('/reports')
def reports():
    """
    Route to display department-wise employee count report.
    
    Returns:
        Rendered HTML template for reports
    """
    # Get department-wise employee count
    dept_query = db.session.query(
        Employee.department,
        db.func.count(Employee.id).label('count')
    ).group_by(Employee.department).all()
    
    # Convert SQLAlchemy Row objects to serializable format
    department_counts = [
        {'department': dept[0] or 'Unassigned', 'count': dept[1]} 
        for dept in dept_query
    ]
    
    # Get total employees
    total_employees = Employee.query.count()
    
    return render_template('reports.html', 
                         department_counts=department_counts,
                         total_employees=total_employees)

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        db.create_all()
        print("Database tables created successfully!")
    app.run(debug=True, use_reloader=False)
