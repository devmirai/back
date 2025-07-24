from flask import Blueprint, request, jsonify
from flask_cors import CORS
from datetime import datetime
from app.models import Ticket, TicketValidation, User, db, TicketStatus, ValidationMethod
from app.utils.auth import jwt_required
from app.utils.helpers import QRCodeGenerator
from app.schemas.schemas import TicketValidationSchema
from app.middleware import validate_request_data
import json

def validate_qr_code(qr_code):
    """Simple QR code validation - extracts ticket info from QR code"""
    try:
        # Assuming QR code contains JSON with ticket info
        qr_info = json.loads(qr_code)
        if 'ticket_number' not in qr_info:
            return None, "Invalid QR code format - missing ticket_number"
        return qr_info, None
    except json.JSONDecodeError:
        # If not JSON, try simple ticket number format
        return {'ticket_number': qr_code}, None

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')

# Activar CORS en todos los endpoints de este blueprint
CORS(tickets_bp)

@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
@jwt_required
def get_ticket(ticket_id):
    """Get specific ticket details"""
    user = request.current_user
    
    # Find ticket - user can only access their own tickets unless they're company
    if user.user_type.value == 'company':
        # Company can access tickets for their events
        ticket = Ticket.query.join(Ticket.event).filter(
            Ticket.id == ticket_id,
            Ticket.event.has(company_id=user.id)
        ).first()
    else:
        # Customer can only access their own tickets
        ticket = Ticket.query.join(Ticket.order).filter(
            Ticket.id == ticket_id,
            Ticket.order.has(user_id=user.id)
        ).first()
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    ticket_data = {
        'id': ticket.id,
        'ticketNumber': ticket.ticket_number,
        'eventName': ticket.event_name,
        'eventLocation': ticket.event_location,
        'eventDate': ticket.event_date.isoformat() if ticket.event_date else None,
        'holderName': ticket.holder_name,
        'holderEmail': ticket.holder_email,
        'seatNumber': ticket.seat_number,
        'section': ticket.section,
        'status': ticket.status.value,
        'usedAt': ticket.used_at.isoformat() if ticket.used_at else None,
        'createdAt': ticket.created_at.isoformat() if ticket.created_at else None,
        'orderId': ticket.order_id,
        'eventId': ticket.event_id
    }
    
    return jsonify({
        'ticket': ticket_data
    }), 200

@tickets_bp.route('/<int:ticket_id>/qr', methods=['GET'])
@jwt_required
def get_ticket_qr(ticket_id):
    """Generate QR code for ticket"""
    user = request.current_user
    
    # Find ticket - user can only access their own tickets
    ticket = Ticket.query.join(Ticket.order).filter(
        Ticket.id == ticket_id,
        Ticket.order.has(user_id=user.id)
    ).first()
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    if ticket.status != TicketStatus.VALID:
        return jsonify({'error': 'Ticket is not valid for QR generation'}), 400
    
    try:
        qr_base64 = QRCodeGenerator.generate_ticket_qr(ticket)
        
        return jsonify({
            'qrCode': qr_base64,
            'ticketNumber': ticket.ticket_number,
            'eventName': ticket.event_name,
            'eventDate': ticket.event_date.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate QR code', 'details': str(e)}), 500

@tickets_bp.route('/<int:ticket_id>/download', methods=['GET'])
@jwt_required
def download_ticket(ticket_id):
    """Download ticket as PNG image"""
    user = request.current_user
    
    # Find ticket - user can only access their own tickets
    ticket = Ticket.query.join(Ticket.order).filter(
        Ticket.id == ticket_id,
        Ticket.order.has(user_id=user.id)
    ).first()
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    if ticket.status != TicketStatus.VALID:
        return jsonify({'error': 'Ticket is not valid for download'}), 400
    
    try:
        # Generate QR code first
        qr_base64 = QRCodeGenerator.generate_ticket_qr(ticket)
        
        # Generate full ticket image
        ticket_image_base64 = QRCodeGenerator.generate_ticket_image(ticket, qr_base64)
        
        return jsonify({
            'ticketImage': ticket_image_base64,
            'filename': f'ticket_{ticket.ticket_number}.png',
            'ticketNumber': ticket.ticket_number
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to generate ticket image', 'details': str(e)}), 500

@tickets_bp.route('/validate', methods=['POST'])
@jwt_required
@validate_request_data(TicketValidationSchema)
def validate_ticket():
    """Validate ticket by QR code"""
    user = request.current_user
    data = request.validated_data
    
    # Only company users can validate tickets
    if user.user_type.value != 'company':
        return jsonify({'error': 'Only companies can validate tickets'}), 403
    
    qr_code = data['qrCode']
    location = data.get('location')
    validation_method = data.get('validationMethod', 'qr_scan')
    
    # Parse QR code
    qr_info, error = validate_qr_code(qr_code)
    if error:
        return jsonify({'error': error}), 400
    
    # Find ticket by ticket number
    ticket = Ticket.query.filter_by(
        ticket_number=qr_info['ticket_number']
    ).first()
    
    if not ticket:
        return jsonify({'error': 'Ticket not found'}), 404
    
    # Verify this company owns the event
    if ticket.event.company_id != user.id:
        return jsonify({'error': 'You can only validate tickets for your events'}), 403
    
    # Check ticket status
    if ticket.status == TicketStatus.USED:
        return jsonify({
            'error': 'Ticket already used',
            'usedAt': ticket.used_at.isoformat(),
            'ticketNumber': ticket.ticket_number
        }), 400
    
    if ticket.status == TicketStatus.CANCELLED:
        return jsonify({
            'error': 'Ticket is cancelled',
            'ticketNumber': ticket.ticket_number
        }), 400
    
    # Validate ticket
    ticket.status = TicketStatus.USED
    ticket.used_at = datetime.utcnow()
    
    # Record validation
    validation = TicketValidation(
        ticket_id=ticket.id,
        validated_by=user.id,
        validation_method=ValidationMethod(validation_method),
        location=location
    )
    
    try:
        db.session.add(validation)
        db.session.commit()
        
        return jsonify({
            'message': 'Ticket validated successfully',
            'ticket': {
                'ticketNumber': ticket.ticket_number,
                'eventName': ticket.event_name,
                'holderName': ticket.holder_name,
                'validatedAt': ticket.used_at.isoformat(),
                'eventDate': ticket.event_date.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to validate ticket', 'details': str(e)}), 500

@tickets_bp.route('/batch-validate', methods=['POST'])
@jwt_required
def batch_validate_tickets():
    """Validate multiple tickets at once"""
    user = request.current_user
    
    # Only company users can validate tickets
    if user.user_type.value != 'company':
        return jsonify({'error': 'Only companies can validate tickets'}), 403
    
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
    
    data = request.json
    qr_codes = data.get('qrCodes', [])
    location = data.get('location')
    
    if not qr_codes or len(qr_codes) > 50:  # Limit batch size
        return jsonify({'error': 'Provide 1-50 QR codes for validation'}), 400
    
    results = []
    
    for qr_code in qr_codes:
        # Parse QR code
        qr_info, error = validate_qr_code(qr_code)
        if error:
            results.append({
                'qrCode': qr_code,
                'success': False,
                'error': error
            })
            continue
        
        # Find and validate ticket
        ticket = Ticket.query.filter_by(
            ticket_number=qr_info['ticket_number']
        ).first()
        
        if not ticket:
            results.append({
                'qrCode': qr_code,
                'success': False,
                'error': 'Ticket not found'
            })
            continue
        
        # Verify this company owns the event
        if ticket.event.company_id != user.id:
            results.append({
                'qrCode': qr_code,
                'success': False,
                'error': 'Not your event'
            })
            continue
        
        # Check if already used
        if ticket.status == TicketStatus.USED:
            results.append({
                'qrCode': qr_code,
                'success': False,
                'error': 'Already used',
                'ticketNumber': ticket.ticket_number
            })
            continue
        
        # Validate ticket
        try:
            ticket.status = TicketStatus.USED
            ticket.used_at = datetime.utcnow()
            
            validation = TicketValidation(
                ticket_id=ticket.id,
                validated_by=user.id,
                validation_method=ValidationMethod.QR_SCAN,
                location=location
            )
            
            db.session.add(validation)
            
            results.append({
                'qrCode': qr_code,
                'success': True,
                'ticketNumber': ticket.ticket_number,
                'eventName': ticket.event_name,
                'holderName': ticket.holder_name
            })
            
        except Exception as e:
            results.append({
                'qrCode': qr_code,
                'success': False,
                'error': f'Validation failed: {str(e)}'
            })
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Batch validation failed', 'details': str(e)}), 500
    
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    return jsonify({
        'message': f'Batch validation completed: {successful} successful, {failed} failed',
        'results': results,
        'summary': {
            'total': len(results),
            'successful': successful,
            'failed': failed
        }
    }), 200
