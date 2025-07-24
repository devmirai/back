"""
Sistema de Tickets - Utilidades Helper
Funciones auxiliares para QR codes, validaciones, etc.
"""

import io
import base64
import qrcode
import random
import string
import bleach
from PIL import Image  
from datetime import datetime, timedelta
import re

# Test comment to force file update

class QRCodeGenerator:
    """Generador de códigos QR para tickets"""
    
    @staticmethod
    def generate_ticket_qr(ticket_id, event_id, validation_token):
        """Generate QR code for ticket validation"""
        qr_data = {
            'ticket_id': ticket_id,
            'event_id': event_id,
            'token': validation_token,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Create QR code string
        qr_string = f"TICKET:{ticket_id}|EVENT:{event_id}|TOKEN:{validation_token}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        # Create image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for API response
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return qr_base64

    @staticmethod
    def validate_qr_code(qr_code_data):
        """Validate QR code format and extract data"""
        try:
            # Expected format: TICKET:123|EVENT:456|TOKEN:abc123
            if not qr_code_data.startswith('TICKET:'):
                return None
                
            parts = qr_code_data.split('|')
            if len(parts) != 3:
                return None
                
            ticket_id = parts[0].replace('TICKET:', '')
            event_id = parts[1].replace('EVENT:', '')
            token = parts[2].replace('TOKEN:', '')
            
            return {
                'ticket_id': int(ticket_id),
                'event_id': int(event_id),
                'token': token
            }
        except (ValueError, IndexError):
            return None

class SecurityHelper:
    """Security utilities"""
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate a secure random token"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def sanitize_input(text, max_length=None):
        """Sanitize user input to prevent XSS"""
        if not text:
            return ''
            
        # Remove HTML tags
        clean_text = bleach.clean(text, tags=[], strip=True)
        
        # Trim if max_length specified
        if max_length and len(clean_text) > max_length:
            clean_text = clean_text[:max_length]
            
        return clean_text.strip()
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        if not phone:
            return True  # Optional field
            
        # Remove all non-digit characters
        digits_only = re.sub(r'[^\d+]', '', phone)
        
        # Must be between 8-20 characters and can start with +
        if len(digits_only) < 8 or len(digits_only) > 20:
            return False
            
        return True

class DateHelper:
    """Date and time utilities"""
    
    @staticmethod
    def is_future_date(date_obj):
        """Check if date is in the future"""
        return date_obj > datetime.utcnow()
    
    @staticmethod
    def format_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
        """Format datetime object to string"""
        if not dt:
            return None
        return dt.strftime(format_str)
    
    @staticmethod
    def parse_iso_datetime(date_string):
        """Parse ISO format datetime string"""
        try:
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

class PaginationHelper:
    """Pagination utilities"""
    
    @staticmethod
    def paginate_query(query, page=1, per_page=20, max_per_page=100):
        """Paginate a SQLAlchemy query"""
        # Validate inputs
        page = max(1, int(page))
        per_page = min(max_per_page, max(1, int(per_page)))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        
        # Calculate pagination info
        has_prev = page > 1
        has_next = (page * per_page) < total
        total_pages = (total + per_page - 1) // per_page
        
        return {
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_page': page - 1 if has_prev else None,
                'next_page': page + 1 if has_next else None
            }
        }

class ValidationHelper:
    """Data validation utilities"""
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
            
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
            
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
            
        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"
            
        return True, "Password is valid"
    
    @staticmethod
    def validate_event_date(event_date):
        """Validate event date is in the future"""
        if not isinstance(event_date, datetime):
            return False, "Invalid date format"
            
        if event_date <= datetime.utcnow():
            return False, "Event date must be in the future"
            
        # Don't allow events more than 2 years in the future
        max_future = datetime.utcnow() + timedelta(days=730)
        if event_date > max_future:
            return False, "Event date cannot be more than 2 years in the future"
            
        return True, "Date is valid"
