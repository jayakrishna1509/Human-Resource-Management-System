"""
Database models for HRMS application

This module defines the SQLAlchemy models for Employee and Attendance entities.
"""

from datetime import datetime, date, time

# This will be imported after app initialization
db = None

def init_db(database):
    """Initialize the database reference"""
    global db
    db = database

class Employee(db.Model):
    """
    Employee model representing employee information in the HRMS.
    
    Attributes:
        id (int): Primary key
        name (str): Employee full name
        email (str): Employee email address (unique)
        address (str): Employee residential address
        phone (str): Employee phone number
        designation (str): Job title/position
        department (str): Department name
        date_of_joining (date): Date when employee joined the company
        created_at (datetime): Timestamp when record was created
        updated_at (datetime): Timestamp when record was last updated
        attendance (relationship): One-to-many relationship with Attendance records
    """
    __tablename__ = 'employees'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    designation = db.Column(db.String(100))
    department = db.Column(db.String(100))
    date_of_joining = db.Column(db.Date, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with attendance records
    attendance = db.relationship('Attendance', backref='employee', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        """String representation of Employee object."""
        return f'<Employee {self.name}>'
    
    def to_dict(self):
        """
        Convert Employee object to dictionary.
        
        Returns:
            dict: Dictionary representation of employee data
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'address': self.address,
            'phone': self.phone,
            'designation': self.designation,
            'department': self.department,
            'date_of_joining': self.date_of_joining.strftime('%Y-%m-%d') if self.date_of_joining else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class Attendance(db.Model):
    """
    Attendance model tracking employee check-in and check-out times.
    
    Attributes:
        id (int): Primary key
        employee_id (int): Foreign key referencing Employee
        date (date): Date of attendance record
        in_time (time): Check-in time
        out_time (time): Check-out time
        created_at (datetime): Timestamp when record was created
        updated_at (datetime): Timestamp when record was last updated
    """
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    in_time = db.Column(db.Time)
    out_time = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate attendance records for same employee on same date
    __table_args__ = (db.UniqueConstraint('employee_id', 'date', name='unique_employee_date'),)
    
    def __repr__(self):
        """String representation of Attendance object."""
        return f'<Attendance Employee:{self.employee_id} Date:{self.date}>'
    
    def to_dict(self):
        """
        Convert Attendance object to dictionary.
        
        Returns:
            dict: Dictionary representation of attendance data
        """
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'in_time': self.in_time.strftime('%H:%M') if self.in_time else None,
            'out_time': self.out_time.strftime('%H:%M') if self.out_time else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
    
    @property
    def working_hours(self):
        """
        Calculate total working hours for the day.
        
        Returns:
            float: Total working hours in decimal format, or None if times are incomplete
        """
        if self.in_time and self.out_time:
            # Convert time objects to datetime for calculation
            in_datetime = datetime.combine(date.today(), self.in_time)
            out_datetime = datetime.combine(date.today(), self.out_time)
            
            # Calculate difference in hours
            diff = out_datetime - in_datetime
            return diff.total_seconds() / 3600  # Convert seconds to hours
        
        return None
