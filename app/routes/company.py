from flask import Blueprint, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from app.models import Event, User, Order, OrderItem, Ticket, db
from app.utils.auth import jwt_required, company_required
from app.middleware import limiter

company_bp = Blueprint('company', __name__, url_prefix='/api/company')
# Activar CORS en todos los endpoints de este blueprint
CORS(company_bp)

@company_bp.route('/events', methods=['GET'])
@jwt_required
def list_company_events():
    """List events created by the authenticated company"""
    user = request.current_user
    user_type = getattr(user.user_type, 'value', user.user_type)
    if user_type != 'company':
        return jsonify({'error': 'Unauthorized'}), 403

    events = Event.query.filter_by(company_id=user.id).all()
    events_data = [
        {
            'id': event.id,
            'title': event.title,
            'description': event.description,  # <-- Añade esta línea
            'eventDate': event.event_date.isoformat(),
            'venue': event.venue,
            'category': event.category,
            'totalTickets': event.total_tickets,
            'basePrice': str(event.base_price),
            'isActive': event.is_active
        }
        for event in events
    ]
    return jsonify({'events': events_data}), 200

@company_bp.route('/customers', methods=['GET'])
@jwt_required
@company_required
def get_company_customers():
    """Get customers who bought tickets for company events"""
    user = request.current_user
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 20)
    event_id = request.args.get('event_id', type=int)
    
    # Build query to get customers
    query = db.session.query(
        User.id,
        User.first_name,
        User.last_name,
        User.email,
        User.phone,
        db.func.count(OrderItem.id).label('total_orders'),
        db.func.sum(OrderItem.total_price).label('total_spent'),
        db.func.max(Order.created_at).label('last_purchase')
    ).join(Order, User.id == Order.user_id).join(
        OrderItem, Order.id == OrderItem.order_id
    ).join(Event, OrderItem.event_id == Event.id).filter(
        Event.company_id == user.id
    )
    
    if event_id:
        query = query.filter(Event.id == event_id)
    
    query = query.group_by(User.id).order_by(db.desc('total_spent'))
    
    # Manual pagination for complex query
    offset = (page - 1) * per_page
    customers = query.offset(offset).limit(per_page).all()
    
    # Get total count
    total_count = db.session.query(
        db.func.count(db.distinct(User.id))
    ).join(Order, User.id == Order.user_id).join(
        OrderItem, Order.id == OrderItem.order_id
    ).join(Event, OrderItem.event_id == Event.id).filter(
        Event.company_id == user.id
    ).scalar()
    
    customers_data = []
    for customer in customers:
        # Get detailed order history for this customer
        orders = db.session.query(
            Order.id,
            Order.order_number,
            Order.created_at,
            OrderItem.quantity,
            OrderItem.total_price,
            Event.title.label('event_name')
        ).join(OrderItem, Order.id == OrderItem.order_id).join(
            Event, OrderItem.event_id == Event.id
        ).filter(
            Order.user_id == customer.id,
            Event.company_id == user.id
        ).all()
        
        customer_data = {
            'id': customer.id,
            'customerName': f"{customer.first_name} {customer.last_name}",
            'email': customer.email,
            'phone': customer.phone,
            'totalOrders': customer.total_orders,
            'totalSpent': float(customer.total_spent) if customer.total_spent else 0,
            'lastPurchase': customer.last_purchase.isoformat() if customer.last_purchase else None,
            'orders': []
        }
        
        for order in orders:
            customer_data['orders'].append({
                'orderId': order.id,
                'orderNumber': order.order_number,
                'eventName': order.event_name,
                'quantity': order.quantity,
                'totalPaid': float(order.total_price),
                'purchaseDate': order.created_at.isoformat() if order.created_at else None
            })
        
        customers_data.append(customer_data)
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return jsonify({
        'customers': customers_data,
        'pagination': {
            'page': page,
            'pages': total_pages,
            'perPage': per_page,
            'total': total_count,
            'hasNext': page < total_pages,
            'hasPrev': page > 1
        }
    }), 200

@company_bp.route('/analytics', methods=['GET'])
@jwt_required
@company_required
def get_company_analytics():
    """Get analytics for company events"""
    user = request.current_user
    
    # Get time period from query params
    period = request.args.get('period', 'month')  # 'week', 'month', 'year'
    
    if period == 'week':
        days_back = 7
    elif period == 'month':
        days_back = 30
    elif period == 'year':
        days_back = 365
    else:
        days_back = 30
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Get company events
    events = Event.query.filter_by(company_id=user.id).all()
    event_ids = [e.id for e in events]
    
    if not event_ids:
        return jsonify({
            'analytics': {
                'totalRevenue': 0,
                'totalTicketsSold': 0,
                'totalEvents': 0,
                'activeEvents': 0,
                'topEvents': [],
                'revenueByPeriod': [],
                'ticketsByPeriod': []
            }
        }), 200
    
    # Calculate total metrics
    total_revenue = db.session.query(
        db.func.sum(OrderItem.total_price)
    ).filter(
        OrderItem.event_id.in_(event_ids)
    ).scalar() or 0
    
    total_tickets_sold = db.session.query(
        db.func.sum(OrderItem.quantity)
    ).filter(
        OrderItem.event_id.in_(event_ids)
    ).scalar() or 0
    
    total_events = len(events)
    active_events = len([e for e in events if e.is_active])
    
    # Get top events by revenue
    top_events = db.session.query(
        Event.id,
        Event.title,
        db.func.sum(OrderItem.total_price).label('revenue'),
        db.func.sum(OrderItem.quantity).label('tickets_sold')
    ).join(OrderItem, Event.id == OrderItem.event_id).filter(
        Event.company_id == user.id
    ).group_by(Event.id).order_by(db.desc('revenue')).limit(5).all()
    
    top_events_data = []
    for event in top_events:
        top_events_data.append({
            'eventId': event.id,
            'eventName': event.title,
            'revenue': float(event.revenue) if event.revenue else 0,
            'ticketsSold': event.tickets_sold or 0
        })
    
    # Get period-based analytics (simplified - would need more complex grouping for real implementation)
    period_revenue = db.session.query(
        db.func.sum(OrderItem.total_price)
    ).join(Order, OrderItem.order_id == Order.id).filter(
        OrderItem.event_id.in_(event_ids),
        Order.created_at >= start_date
    ).scalar() or 0
    
    period_tickets = db.session.query(
        db.func.sum(OrderItem.quantity)
    ).join(Order, OrderItem.order_id == Order.id).filter(
        OrderItem.event_id.in_(event_ids),
        Order.created_at >= start_date
    ).scalar() or 0
    
    return jsonify({
        'analytics': {
            'totalRevenue': float(total_revenue),
            'totalTicketsSold': total_tickets_sold,
            'totalEvents': total_events,
            'activeEvents': active_events,
            'topEvents': top_events_data,
            'periodAnalytics': {
                'period': period,
                'revenue': float(period_revenue),
                'ticketsSold': period_tickets
            }
        }
    }), 200

@company_bp.route('/events/<int:event_id>/attendees', methods=['GET'])
@jwt_required
@company_required
def get_event_attendees(event_id):
    """Get attendees list for specific event"""
    user = request.current_user
    
    # Verify event belongs to company
    event = Event.query.filter_by(id=event_id, company_id=user.id).first()
    if not event:
        return jsonify({'error': 'Event not found or access denied'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 50)
    
    # Get tickets for this event
    tickets_pagination = Ticket.query.filter_by(event_id=event_id).join(
        Order, Ticket.order_id == Order.id
    ).order_by(Ticket.created_at.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    attendees_data = []
    for ticket in tickets_pagination.items:
        order = ticket.order
        user_info = order.user
        
        attendees_data.append({
            'ticketId': ticket.id,
            'ticketNumber': ticket.ticket_number,
            'customerName': f"{user_info.first_name} {user_info.last_name}",
            'customerEmail': user_info.email,
            'customerPhone': user_info.phone,
            'holderName': ticket.holder_name,
            'seatNumber': ticket.seat_number,
            'section': ticket.section,
            'status': ticket.status.value,
            'purchaseDate': order.created_at.isoformat(),
            'usedAt': ticket.used_at.isoformat() if ticket.used_at else None
        })
    
    return jsonify({
        'attendees': attendees_data,
        'pagination': {
            'page': page,
            'pages': tickets_pagination.pages,
            'perPage': per_page,
            'total': tickets_pagination.total,
            'hasNext': tickets_pagination.has_next,
            'hasPrev': tickets_pagination.has_prev
        },
        'eventInfo': {
            'id': event.id,
            'title': event.title,
            'eventDate': event.event_date.isoformat(),
            'venue': event.venue
        }
    }), 200

@company_bp.route('/dashboard', methods=['GET'])
@jwt_required
@company_required
def get_dashboard_summary():
    """Get dashboard summary for company"""
    user = request.current_user
    
    # Get basic counts
    total_events = Event.query.filter_by(company_id=user.id).count()
    active_events = Event.query.filter_by(company_id=user.id, is_active=True).count()
    
    # Get recent events
    recent_events = Event.query.filter_by(
        company_id=user.id
    ).order_by(Event.created_at.desc()).limit(5).all()
    
    recent_events_data = []
    for event in recent_events:
        tickets_sold = sum(tt.quantity_sold for tt in event.ticket_types)
        recent_events_data.append({
            'id': event.id,
            'title': event.title,
            'eventDate': event.event_date.isoformat(),
            'isActive': event.is_active,
            'ticketsSold': tickets_sold,
            'totalTickets': event.total_tickets
        })
    
    # Get total revenue (simplified)
    event_ids = [e.id for e in Event.query.filter_by(company_id=user.id).all()]
    total_revenue = 0
    if event_ids:
        total_revenue = db.session.query(
            db.func.sum(OrderItem.total_price)
        ).filter(OrderItem.event_id.in_(event_ids)).scalar() or 0
    
    return jsonify({
        'dashboard': {
            'totalEvents': total_events,
            'activeEvents': active_events,
            'totalRevenue': float(total_revenue),
            'recentEvents': recent_events_data
        }
    }), 200

@company_bp.route('/buyers', methods=['GET'])
@jwt_required
def list_company_buyers():
    """List unique buyers for the authenticated company"""
    user = request.current_user
    user_type = getattr(user.user_type, 'value', user.user_type)
    if user_type != 'company':
        return jsonify({'error': 'Unauthorized'}), 403

    # Obtener IDs de eventos de la empresa
    event_ids = [event.id for event in Event.query.filter_by(company_id=user.id).all()]
    if not event_ids:
        return jsonify({'buyers': []}), 200

    # Obtener IDs de órdenes que tengan items para esos eventos
    order_ids = db.session.query(OrderItem.order_id).filter(OrderItem.event_id.in_(event_ids)).distinct().all()
    order_ids = [oid[0] for oid in order_ids]

    # Obtener usuarios compradores
    buyers = User.query.join(Order, User.id == Order.user_id).filter(Order.id.in_(order_ids)).distinct().all()
    buyers_data = []
    for buyer in buyers:
        # Obtener todas las órdenes del comprador para eventos de la empresa
        orders = Order.query.filter(Order.user_id == buyer.id, Order.id.in_(order_ids)).all()
        tickets_info = []
        for order in orders:
            for ticket in order.tickets:
                if ticket.event_id in event_ids:
                    tickets_info.append({
                        'ticketId': ticket.id,
                        'ticketNumber': ticket.ticket_number,
                        'eventName': ticket.event_name,
                        'quantity': 1,
                        'totalPaid': float(order.total_amount),
                        'purchaseDate': order.created_at.isoformat(),
                    })
        buyers_data.append({
            'id': buyer.id,
            'customerName': f"{buyer.first_name} {buyer.last_name}",
            'email': buyer.email,
            'phone': buyer.phone,
            'tickets': tickets_info
        })

    return jsonify({'buyers': buyers_data}), 200
