"""
🎫 Sistema de Tickets - Utilidades de Autenticación
Sistema JWT completo basado en las especificaciones del README.MD
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app, g
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required as _jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models import User, UserSession, UserType, db
import secrets
import hashlib

# Initialize JWT manager
jwt_manager = JWTManager()

def init_jwt(app):
    """Initialize JWT with Flask app"""
    jwt_manager.init_app(app)
    
    @jwt_manager.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if token is revoked/blocked"""
        # TODO: Implement token blacklist using Redis
        return False
    
    @jwt_manager.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401
    
    @jwt_manager.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401
    
    @jwt_manager.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token is required'}), 401

class JWTManager:
    @staticmethod
    def generate_tokens(user):
        """Generate access and refresh tokens for user"""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'user_type': user.user_type.value,
            'email': user.email,
            'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': now,
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'exp': now + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
            'iat': now,
            'type': 'refresh'
        }
        
        access_token = jwt.encode(
            access_payload, 
            current_app.config['JWT_SECRET_KEY'], 
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        refresh_token = jwt.encode(
            refresh_payload, 
            current_app.config['JWT_SECRET_KEY'], 
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        # Store refresh token in database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            device_info=request.headers.get('User-Agent'),
            ip_address=request.remote_addr,
            expires_at=now + current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
        )
        db.session.add(session)
        db.session.commit()
        
        return access_token, refresh_token
    
    @staticmethod
    def decode_token(token, token_type='access'):
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            
            if payload.get('type') != token_type:
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """Generate new access token from refresh token"""
        payload = JWTManager.decode_token(refresh_token, 'refresh')
        if not payload:
            return None
            
        # Verify refresh token exists in database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = UserSession.query.filter_by(
            token_hash=token_hash,
            is_active=True
        ).first()
        
        if not session or session.expires_at < datetime.utcnow():
            return None
            
        # Generate new access token
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return None
            
        now = datetime.utcnow()
        access_payload = {
            'user_id': user.id,
            'user_type': user.user_type.value,
            'email': user.email,
            'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'iat': now,
            'type': 'access'
        }
        
        access_token = jwt.encode(
            access_payload, 
            current_app.config['JWT_SECRET_KEY'], 
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        # Update session last used
        session.last_used_at = now
        db.session.commit()
        
        return access_token
    
    @staticmethod
    def revoke_token(refresh_token):
        """Revoke refresh token"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = UserSession.query.filter_by(token_hash=token_hash).first()
        if session:
            session.is_active = False
            db.session.commit()
            return True
        return False


def jwt_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
            
        try:
            token = auth_header.split(' ')[1]  # Bearer <token>
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
            
        payload = JWTManager.decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
            
        # Get user from database
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
            
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def company_required(f):
    """Decorator to require company user type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
            
        if request.current_user.user_type.value != 'company':
            return jsonify({'error': 'Company access required'}), 403
            
        return f(*args, **kwargs)
    
    return decorated_function


def customer_required(f):
    """Decorator to require customer user type"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'error': 'Authentication required'}), 401
            
        if request.current_user.user_type.value != 'customer':
            return jsonify({'error': 'Customer access required'}), 403
            
        return f(*args, **kwargs)
    
    return decorated_function
