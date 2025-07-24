from flask import Blueprint, request, jsonify
from app.models import User, Ticket, Order, PaymentMethod, db, TicketStatus, OrderStatus, Event, OrderItem, TicketType
from app.utils.auth import jwt_required
from app.utils.helpers import QRCodeGenerator
from app.schemas.schemas import UserUpdateSchema, PaymentMethodSchema
from app.middleware import validate_request_data

users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('/profile', methods=['GET'])
@jwt_required
def get_profile():
    """Get user profile"""
    user = request.current_user
    return jsonify({
        'user': user.to_dict()
    }), 200

@users_bp.route('/profile', methods=['PUT'])
@jwt_required
@validate_request_data(UserUpdateSchema)
def update_profile():
    """Update user profile"""
    user = request.current_user
    data = request.validated_data
    
    # Update user fields
    if 'firstName' in data:
        user.first_name = data['firstName']
    if 'lastName' in data:
        user.last_name = data['lastName']
    if 'phone' in data:
        user.phone = data['phone']
    if 'companyName' in data and user.user_type.value == 'company':
        user.company_name = data['companyName']
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@users_bp.route('/tickets', methods=['GET'])
@jwt_required
def get_user_tickets():
    """Get all tickets for current user"""
    user = request.current_user

    # Obtener todas las órdenes del usuario (sin filtrar por estado)
    orders = Order.query.filter_by(user_id=user.id).all()

    user_tickets = []
    for order in orders:
        for ticket in order.tickets:
            user_tickets.append({
                'id': ticket.id,
                'orderId': ticket.order_id,
                'eventName': ticket.event_name,
                'eventDate': ticket.event_date.isoformat(),
                'eventLocation': ticket.event_location,
                'quantity': 1,  # Cada ticket es individual
                'totalPrice': float(ticket.order.total_amount) / len(ticket.order.tickets) if ticket.order.tickets else 0,
                'purchaseDate': ticket.created_at.isoformat(),
                'status': ticket.status.value,
                'ticketNumber': ticket.ticket_number
            })

    return jsonify({
        'tickets': user_tickets,
        'total': len(user_tickets)
    }), 200

@users_bp.route('/orders', methods=['GET'])
@jwt_required
def get_user_orders():
    """Get all orders for current user"""
    user = request.current_user
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 20)
    
    orders_pagination = Order.query.filter_by(user_id=user.id).order_by(
        Order.created_at.desc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    orders_data = []
    for order in orders_pagination.items:
        order_data = {
            'id': order.id,
            'orderNumber': order.order_number,
            'totalAmount': float(order.total_amount),
            'status': order.status.value,
            'paymentMethod': order.payment_method,
            'createdAt': order.created_at.isoformat(),
            'items': []
        }
        
        for item in order.items:
            order_data['items'].append({
                'eventId': item.event_id,
                'eventName': item.event.title,
                'ticketTypeId': item.ticket_type_id,
                'quantity': item.quantity,
                'unitPrice': float(item.unit_price),
                'totalPrice': float(item.total_price)
            })
        
        orders_data.append(order_data)
    
    return jsonify({
        'orders': orders_data,
        'pagination': {
            'page': page,
            'pages': orders_pagination.pages,
            'perPage': per_page,
            'total': orders_pagination.total,
            'hasNext': orders_pagination.has_next,
            'hasPrev': orders_pagination.has_prev
        }
    }), 200

@users_bp.route('/orders', methods=['POST'])
@jwt_required
def create_order():
    """Create a new order for current user"""
    user = request.current_user
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400

    data = request.json
    items = data.get('items', [])
    payment_method = data.get('paymentMethod')
    billing_address = data.get('billingAddress')

    if not items or not payment_method:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # 1. Crear la orden
        order = Order(
            user_id=user.id,
            order_number=Order.generate_order_number(),
            total_amount=sum(item['totalPrice'] for item in items),
            status=OrderStatus.PENDING,
            payment_method=payment_method,
            billing_address=billing_address
        )
        db.session.add(order)
        db.session.flush()  # Para obtener order.id

        order_items = []
        # 2. Crear los OrderItems
        for item in items:
            event = Event.query.get(item['eventId'])
            if not event:
                db.session.rollback()
                return jsonify({'error': f"Event with id {item['eventId']} not found"}), 404

            ticket_type = TicketType.query.get(item['ticketTypeId'])
            if not ticket_type:
                db.session.rollback()
                return jsonify({'error': f"TicketType with id {item['ticketTypeId']} not found"}), 404

            order_item = OrderItem(
                order_id=order.id,
                event_id=item['eventId'],
                ticket_type_id=item['ticketTypeId'],
                quantity=item['quantity'],
                unit_price=item['unitPrice'],
                total_price=item['totalPrice']
            )
            db.session.add(order_item)
            order_items.append((order_item, event, ticket_type, item['quantity']))

        db.session.flush()  # Para obtener los ids de order_items si se necesitan

        created_tickets = []
        tickets_data = []
        # 3. Crear los tickets asociados
        for order_item, event, ticket_type, quantity in order_items:
            for _ in range(quantity):
                ticket_number = Ticket.generate_ticket_number()
                qr_code = QRCodeGenerator.generate_ticket_qr(0, event.id, ticket_number)
                ticket = Ticket(
                    order_id=order.id,
                    event_id=event.id,
                    ticket_type_id=ticket_type.id,
                    event_name=event.title,
                    event_date=event.event_date,
                    event_location=event.venue,
                    ticket_number=ticket_number,
                    qr_code=qr_code,
                    status=TicketStatus.VALID,
                    holder_name=user.first_name + " " + user.last_name,
                    holder_email=user.email
                    # Removido: seat_number, section
                )
                db.session.add(ticket)
                created_tickets.append(ticket)

        db.session.commit()  # Ahora los tickets tienen id

        # 4. Generar QR y actualizar tickets
        for ticket in created_tickets:
            qr_code = QRCodeGenerator.generate_ticket_qr(ticket.id, ticket.event_id, ticket.ticket_number)
            ticket.qr_code = qr_code
            tickets_data.append({
                "id": ticket.id,  # <-- Añade el id aquí
                "ticketNumber": ticket.ticket_number,
                "qrCode": qr_code,
                "eventName": ticket.event_name,
                "eventDate": ticket.event_date.isoformat() if ticket.event_date else None,
                "eventLocation": ticket.event_location
            })

        db.session.commit()  # Guardar los QR

        return jsonify({
            "message": "Order created successfully",
            "order": {
                "id": order.id,
                "orderNumber": order.order_number,
                "totalAmount": float(order.total_amount),
                "status": order.status.value,
                "createdAt": order.created_at.isoformat()
            },
            "tickets": tickets_data
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create order', 'details': str(e)}), 500

@users_bp.route('/payment-methods', methods=['GET'])
@jwt_required
def get_payment_methods():
    """Get user's payment methods"""
    user = request.current_user
    
    payment_methods = PaymentMethod.query.filter_by(
        user_id=user.id,
        is_active=True
    ).all()
    
    methods_data = []
    for method in payment_methods:
        methods_data.append({
            'id': method.id,
            'type': method.type.value if hasattr(method.type, 'value') else method.type,
            # 'lastFour': method.last_four_digits,  # <-- Removido lastFourDigits
            'cardType': method.card_type,
            'isDefault': method.is_default,
            'expiryDate': f"{method.expiry_month:02d}/{method.expiry_year % 100:02d}" if method.expiry_month else None,
            'cardNumber': method.card_number
        })
    
    return jsonify({
        'paymentMethods': methods_data
    }, 200)

@users_bp.route('/payment-methods', methods=['POST'])
@jwt_required
@validate_request_data(PaymentMethodSchema)
def add_payment_method():
    """Add new payment method"""
    user = request.current_user
    data = request.validated_data
    
    # If this is set as default, unset other defaults
    if data.get('isDefault', False):
        PaymentMethod.query.filter_by(
            user_id=user.id,
            is_default=True
        ).update({'is_default': False})
    
    payment_method = PaymentMethod(
        user_id=user.id,
        type=data['type'],
        provider=data.get('provider'),
        card_type=data.get('cardType'),
        # last_four_digits=data.get('lastFourDigits'),  # <-- Removido lastFourDigits
        cardholder_name=data.get('cardholderName'),
        expiry_month=data.get('expiryMonth'),
        expiry_year=data.get('expiryYear'),
        is_default=data.get('isDefault', False),
        card_number=data.get('cardNumber')
    )
    
    try:
        db.session.add(payment_method)
        db.session.commit()
        
        return jsonify({
            'message': 'Payment method added successfully',
            'paymentMethod': {
                'id': payment_method.id,
                'type': payment_method.type.value if hasattr(payment_method.type, 'value') else payment_method.type,
                'cardType': payment_method.card_type,
                'isDefault': payment_method.is_default,
                'cardNumber': payment_method.card_number
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add payment method', 'details': str(e)}), 500

@users_bp.route('/payment-methods/<int:method_id>', methods=['PUT'])
@jwt_required
def update_payment_method(method_id):
    """Update payment method"""
    user = request.current_user
    
    payment_method = PaymentMethod.query.filter_by(
        id=method_id,
        user_id=user.id,
        is_active=True
    ).first()
    
    if not payment_method:
        return jsonify({'error': 'Payment method not found'}), 404
    
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = request.json
    
    # If setting as default, unset other defaults
    if data.get('isDefault', False):
        PaymentMethod.query.filter_by(
            user_id=user.id,
            is_default=True
        ).update({'is_default': False})
        payment_method.is_default = True
    
    try:
        db.session.commit()
        return jsonify({'message': 'Payment method updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update payment method', 'details': str(e)}), 500

@users_bp.route('/payment-methods/<int:method_id>', methods=['DELETE'])
@jwt_required
def delete_payment_method(method_id):
    """Delete payment method"""
    user = request.current_user
    
    payment_method = PaymentMethod.query.filter_by(
        id=method_id,
        user_id=user.id,
        is_active=True
    ).first()
    
    if not payment_method:
        return jsonify({'error': 'Payment method not found'}), 404
    
    # Soft delete
    payment_method.is_active = False
    
    try:
        db.session.commit()
        return jsonify({'message': 'Payment method deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete payment method', 'details': str(e)}), 500

@users_bp.route('/upload-avatar', methods=['POST'])
@jwt_required
def upload_avatar():
    """Upload user avatar (placeholder implementation)"""
    # This would integrate with cloud storage service like Cloudinary or AWS S3
    return jsonify({
        'message': 'Avatar upload not implemented yet',
        'info': 'This endpoint would integrate with cloud storage service'
    }), 501
