"""
Test cases for HRMS Flask application.
"""

import pytest
import json
from datetime import datetime, date
from app import app, db, Employee, Attendance


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


class TestEmployeeAPI:
    """Test employee API endpoints."""
    
    def test_get_employees_empty(self, client):
        """Test getting employees when database is empty."""
        response = client.get('/api/v1/employees')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['employees'] == []
        assert 'pagination' in data
        assert 'api_version' in data
    
    def test_add_employee_success(self, client):
        """Test adding a valid employee."""
        employee_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'department': 'IT',
            'designation': 'Developer',
            'date_of_joining': '2024-01-15'
        }
        
        response = client.post('/api/v1/employees', 
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Employee added successfully'
        assert 'employee_id' in data
    
    def test_add_employee_invalid_email(self, client):
        """Test adding employee with invalid email."""
        employee_data = {
            'name': 'John Doe',
            'email': 'invalid-email',
            'department': 'IT'
        }
        
        response = client.post('/api/v1/employees',
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid email format' in data['error']
    
    def test_add_employee_duplicate_email(self, client):
        """Test adding employee with duplicate email."""
        # First employee
        employee_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'department': 'IT'
        }
        client.post('/api/v1/employees',
                  data=json.dumps(employee_data),
                  content_type='application/json')
        
        # Duplicate employee
        response = client.post('/api/v1/employees',
                             data=json.dumps(employee_data),
                             content_type='application/json')
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Email already exists' in data['error']


class TestAttendanceAPI:
    """Test attendance API endpoints."""
    
    def test_mark_attendance_success(self, client):
        """Test marking attendance successfully."""
        # First add an employee
        employee_data = {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'department': 'HR'
        }
        response = client.post('/api/v1/employees',
                             data=json.dumps(employee_data),
                             content_type='application/json')
        employee_id = json.loads(response.data)['employee_id']
        
        # Mark attendance
        attendance_data = {
            'date': '2024-01-15',
            'in_time': '09:00',
            'out_time': '18:00'
        }
        
        response = client.post(f'/api/attendance/{employee_id}',
                             data=json.dumps(attendance_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Attendance marked successfully'
    
    def test_mark_attendance_invalid_time(self, client):
        """Test marking attendance with invalid time format."""
        employee_data = {
            'name': 'Test Employee',
            'email': 'test@example.com',
            'department': 'IT'
        }
        response = client.post('/api/v1/employees',
                             data=json.dumps(employee_data),
                             content_type='application/json')
        employee_id = json.loads(response.data)['employee_id']
        
        attendance_data = {
            'date': '2024-01-15',
            'in_time': '25:00',  # Invalid time
            'out_time': '18:00'
        }
        
        response = client.post(f'/api/attendance/{employee_id}',
                             data=json.dumps(attendance_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestHealthCheck:
    """Test health check endpoint."""
    
    def test_health_check_success(self, client):
        """Test successful health check."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'database' in data


class TestInputValidation:
    """Test input validation functions."""
    
    def test_sanitize_input_html(self):
        """Test HTML sanitization."""
        from app import sanitize_input
        
        # Test HTML injection
        malicious_input = '<script>alert("xss")</script>'
        sanitized = sanitize_input(malicious_input)
        assert '&lt;script&gt;alert("xss")&lt;/script&gt;' in sanitized
        assert '<script>' not in sanitized
    
    def test_sanitize_input_dict(self):
        """Test dictionary sanitization."""
        from app import sanitize_input
        
        malicious_data = {
            'name': '<script>alert("xss")</script>',
            'email': 'test@example.com'
        }
        sanitized = sanitize_input(malicious_data)
        assert sanitized['name'] != malicious_data['name']
        assert sanitized['email'] == malicious_data['email']


if __name__ == '__main__':
    pytest.main([__file__])
