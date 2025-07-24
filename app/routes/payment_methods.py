from flask import Blueprint, jsonify, request
from flask_cors import CORS
from app.utils.auth import jwt_required
from app.models import PaymentMethod, db

payment_methods_bp = Blueprint('payment_methods', __name__)
# Activar CORS en todos los endpoints de este blueprint
CORS(payment_methods_bp)

@payment_methods_bp.route('/api/payment-methods', methods=['GET'])
@jwt_required
def get_payment_methods():
    user = getattr(request, 'current_user', None)
    if not user:
        return jsonify({'error': 'User not found'}), 401
    methods = PaymentMethod.query.filter_by(user_id=user.id).all()
    result = [
        {
            "id": m.id,
            "type": m.type.value if hasattr(m.type, 'value') else m.type,
            "provider": m.provider,
            "card_type": m.card_type,
            "cardholder_name": m.cardholder_name,
            "expiry_month": m.expiry_month,
            "expiry_year": m.expiry_year,
            "is_default": m.is_default,
            "is_active": m.is_active,
            "card_number": m.card_number
        }
        for m in methods
    ]
    return jsonify(result)