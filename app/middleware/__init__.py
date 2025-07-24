from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import re

# Rate limiter instance
limiter = None

def init_limiter(app):
    """Initialize rate limiter with app"""
    global limiter
    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri='memory://',  # Force memory storage
        default_limits=["100 per minute", "1000 per hour"]
    )
    limiter.init_app(app)
    return limiter

def validate_request_data(schema_class):
    """Decorator to validate request JSON data against schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            try:
                schema = schema_class()
                data = schema.load(request.json)
                request.validated_data = data
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'error': 'Validation error', 'details': str(e)}), 400
        
        return decorated_function
    return decorator

def sanitize_input(data):
    """Sanitize input data to prevent XSS"""
    if isinstance(data, dict):
        return {key: sanitize_input(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    elif isinstance(data, str):
        # Remove potentially dangerous characters
        data = re.sub(r'[<>"\']', '', data)
        return data.strip()
    return data

def validate_file_upload(allowed_extensions=None, max_size=None):
    """Decorator to validate file uploads"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if max_size is None:
        max_size = 5 * 1024 * 1024  # 5MB
        
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
                
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
                
            # Check file extension
            if '.' not in file.filename:
                return jsonify({'error': 'File must have an extension'}), 400
                
            ext = file.filename.rsplit('.', 1)[1].lower()
            if ext not in allowed_extensions:
                return jsonify({'error': f'Allowed extensions: {", ".join(allowed_extensions)}'}), 400
                
            # Check file size
            file.seek(0, 2)  # Seek to end
            size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if size > max_size:
                return jsonify({'error': f'File too large. Max size: {max_size / 1024 / 1024:.1f}MB'}), 400
                
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def cors_headers():
    """Add CORS headers to response"""
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
        'Access-Control-Max-Age': '86400'
    }
    return headers
