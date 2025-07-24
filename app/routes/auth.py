from flask import Blueprint, request, jsonify
from flask_cors import CORS
from app.models import User, db, UserType
from app.utils.auth import JWTManager, jwt_required
from app.schemas.schemas import UserRegistrationSchema, UserLoginSchema
from app.middleware import validate_request_data

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
# Activar CORS en todos los endpoints de este blueprint
CORS(auth_bp)

@auth_bp.route('/register', methods=['POST'])
@validate_request_data(UserRegistrationSchema)
def register():
    """Register new user or company"""
    data = request.validated_data
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create new user
    user = User(
        email=data['email'],
        first_name=data['firstName'],
        last_name=data['lastName'],
        user_type=UserType.CUSTOMER if data['userType'] == 'customer' else UserType.COMPANY,
        phone=data.get('phone'),
        company_name=data.get('companyName') if data['userType'] == 'company' else None
    )
    
    user.set_password(data['password'])
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        access_token, refresh_token = JWTManager.generate_tokens(user)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'token': access_token,
            'refreshToken': refresh_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
@validate_request_data(UserLoginSchema)
def login():
    """User login"""
    data = request.validated_data
    
    # Find user by email
    user = User.query.filter_by(email=data['email']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 401
    
    # Generate tokens
    access_token, refresh_token = JWTManager.generate_tokens(user)
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'token': access_token,
        'refreshToken': refresh_token
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required
def logout():
    """User logout"""
    auth_header = request.headers.get('Authorization')
    refresh_token = request.json.get('refreshToken') if request.is_json else None
    
    if refresh_token:
        JWTManager.revoke_token(refresh_token)
    
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/refresh-token', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    refresh_token = request.json.get('refreshToken')
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400
    
    new_access_token = JWTManager.refresh_access_token(refresh_token)
    if not new_access_token:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401
    
    return jsonify({
        'token': new_access_token,
        'message': 'Token refreshed successfully'
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required
def get_current_user():
    """Get current user information"""
    user = request.current_user
    return jsonify({
        'user': user.to_dict()
    }), 200

@auth_bp.route('/verify-email', methods=['POST'])
@jwt_required
def verify_email():
    """Verify user email (placeholder for email verification)"""
    user = request.current_user
    user.email_verified = True
    db.session.commit()
    
    return jsonify({'message': 'Email verified successfully'}), 200

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required
def change_password():
    """Change user password"""
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = request.json
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password required'}), 400
    
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    
    user = request.current_user
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200
