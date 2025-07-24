from flask import Blueprint, request, jsonify
from flask_cors import CORS
from datetime import datetime
from app.models import Event, TicketType, User, db
from app.utils.auth import jwt_required, company_required
from app.schemas.schemas import EventCreateSchema, TicketTypeSchema
from app.middleware import validate_request_data

events_bp = Blueprint('events', __name__, url_prefix='/api/events')
# Activar CORS en todos los endpoints de este blueprint
CORS(events_bp)

@events_bp.route('', methods=['GET'])
def get_events():
    """Get public events list with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 20)
    category = request.args.get('category')
    city = request.args.get('city')
    search = request.args.get('search')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Build query
    query = Event.query.filter(Event.is_active == True)
    
    # Apply filters
    if category:
        query = query.filter(Event.category.ilike(f'%{category}%'))
    
    if city:
        query = query.filter(Event.city.ilike(f'%{city}%'))
    
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Event.title.ilike(search_filter),
                Event.description.ilike(search_filter),
                Event.venue.ilike(search_filter)
            )
        )
    
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            query = query.filter(Event.event_date >= date_from_obj)
        except ValueError:
            return jsonify({'error': 'Invalid date_from format'}), 400
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            query = query.filter(Event.event_date <= date_to_obj)
        except ValueError:
            return jsonify({'error': 'Invalid date_to format'}), 400
    
    # Order by event date
    query = query.order_by(Event.event_date.asc())
    
    # Paginate
    events_pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    events_data = []
    for event in events_pagination.items:
        event_dict = event.to_dict()
        
        # Add ticket types
        ticket_types = []
        for ticket_type in event.ticket_types:
            ticket_types.append({
                'id': ticket_type.id,
                'name': ticket_type.name,
                'description': ticket_type.description,
                'price': float(ticket_type.price),
                'quantityAvailable': ticket_type.quantity_available,
                'quantitySold': ticket_type.quantity_sold
            })
        
        event_dict['ticketTypes'] = ticket_types
        events_data.append(event_dict)
    
    return jsonify({
        'events': events_data,
        'pagination': {
            'page': page,
            'pages': events_pagination.pages,
            'perPage': per_page,
            'total': events_pagination.total,
            'hasNext': events_pagination.has_next,
            'hasPrev': events_pagination.has_prev
        }
    }), 200

@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get specific event details"""
    event = Event.query.filter_by(id=event_id, is_active=True).first()
    
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    
    event_data = event.to_dict()
    
    # Add ticket types
    ticket_types = []
    for ticket_type in event.ticket_types:
        ticket_types.append({
            'id': ticket_type.id,
            'name': ticket_type.name,
            'description': ticket_type.description,
            'price': float(ticket_type.price),
            'quantityAvailable': ticket_type.quantity_available,
            'quantitySold': ticket_type.quantity_sold,
            'benefits': ticket_type.benefits
        })
    
    event_data['ticketTypes'] = ticket_types
    
    # Add company info
    company = User.query.get(event.company_id)
    event_data['company'] = {
        'id': company.id,
        'name': company.company_name,
        'email': company.email
    }
    
    return jsonify({
        'event': event_data
    }), 200

@events_bp.route('', methods=['POST'])
@jwt_required
@company_required
@validate_request_data(EventCreateSchema)
def create_event():
    """Create new event (company only)"""
    user = request.current_user
    data = request.validated_data

    event = Event(
        company_id=user.id,
        title=data['title'],
        description=data.get('description'),
        event_date=data['eventDate'],
        venue=data['venue'],
        address=data.get('address'),
        city=data.get('city'),
        country=data.get('country'),
        category=data.get('category'),
        image_url=data.get('imageUrl'),
        total_tickets=data['totalTickets'],
        available_tickets=data['totalTickets'],
        base_price=data['basePrice']
    )

    try:
        db.session.add(event)
        db.session.flush()  # Get event ID

        # Create default ticket type
        default_ticket = TicketType(
            event_id=event.id,
            name='General',
            description='Acceso general al evento',
            price=data['basePrice'],
            quantity_available=data['totalTickets']
        )

        db.session.add(default_ticket)
        db.session.commit()

        event_data = event.to_dict()
        # Add ticket types
        ticket_types = []
        for ticket_type in event.ticket_types:
            ticket_types.append({
                'id': ticket_type.id,
                'name': ticket_type.name,
                'description': ticket_type.description,
                'price': float(ticket_type.price),
                'quantityAvailable': ticket_type.quantity_available,
                'quantitySold': ticket_type.quantity_sold,
                'benefits': ticket_type.benefits
            })
        event_data['ticketTypes'] = ticket_types
        # Add company info
        company = User.query.get(event.company_id)
        event_data['company'] = {
            'id': company.id,
            'name': company.company_name,
            'email': company.email
        }
        return jsonify({
            'message': 'Event created successfully',
            'event': event_data
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create event', 'details': str(e)}), 500

@events_bp.route('/<int:event_id>', methods=['DELETE'])
@jwt_required
@company_required
def delete_event(event_id):
    """Delete event (only by owning company)"""
    user = request.current_user
    
    event = Event.query.filter_by(id=event_id, company_id=user.id).first()
    
    if not event:
        return jsonify({'error': 'Event not found or access denied'}), 404
    
    # Check if there are any orders for this event
    orders_count = OrderItem.query.filter_by(event_id=event_id).count()
    if orders_count > 0:
        return jsonify({'error': 'Cannot delete event with existing orders'}), 400
    
    try:
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Event deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete event', 'details': str(e)}), 500

@events_bp.route('/<int:event_id>/status', methods=['PATCH'])
@jwt_required
@company_required
def toggle_event_status(event_id):
    """Activate/deactivate event"""
    user = request.current_user
    
    event = Event.query.filter_by(id=event_id, company_id=user.id).first()
    
    if not event:
        return jsonify({'error': 'Event not found or access denied'}), 404
    
    event.is_active = not event.is_active
    
    try:
        db.session.commit()
        status = 'activated' if event.is_active else 'deactivated'
        return jsonify({'message': f'Event {status} successfully', 'isActive': event.is_active}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update event status', 'details': str(e)}), 500

@events_bp.route('/<int:event_id>/ticket-types', methods=['POST'])
@jwt_required
@company_required
@validate_request_data(TicketTypeSchema)
def add_ticket_type(event_id):
    """Add ticket type to event"""
    user = request.current_user
    data = request.validated_data
    
    event = Event.query.filter_by(id=event_id, company_id=user.id).first()
    
    if not event:
        return jsonify({'error': 'Event not found or access denied'}), 404
    
    ticket_type = TicketType(
        event_id=event_id,
        name=data['name'],
        description=data.get('description'),
        price=data['price'],
        quantity_available=data['quantityAvailable'],
        benefits=data.get('benefits')
    )
    
    try:
        db.session.add(ticket_type)
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket type added successfully',
            'ticketType': {
                'id': ticket_type.id,
                'name': ticket_type.name,
                'description': ticket_type.description,
                'price': float(ticket_type.price),
                'quantityAvailable': ticket_type.quantity_available
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add ticket type', 'details': str(e)}), 500

@events_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get list of event categories"""
    categories = db.session.query(Event.category).filter(
        Event.category.isnot(None),
        Event.is_active == True
    ).distinct().all()
    
    category_list = [cat[0] for cat in categories if cat[0]]
    
    return jsonify({
        'categories': sorted(category_list)
    }), 200

@events_bp.route('/cities', methods=['GET'])
def get_cities():
    """Get list of cities with events"""
    cities = db.session.query(Event.city).filter(
        Event.city.isnot(None),
        Event.is_active == True
    ).distinct().all()
    
    city_list = [city[0] for city in cities if city[0]]
    
    return jsonify({
        'cities': sorted(city_list)
    }), 200

@events_bp.route('/featured', methods=['GET'])
def get_featured_events():
    """Get featured events (placeholder - would implement featured logic)"""
    events = Event.query.filter(
        Event.is_active == True,
        Event.event_date > datetime.utcnow()
    ).order_by(Event.created_at.desc()).limit(6).all()
    
    events_data = []
    for event in events:
        event_dict = event.to_dict()
        events_data.append(event_dict)
    
    return jsonify({
        'featuredEvents': events_data
    }), 200
