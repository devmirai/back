from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import bcrypt
import random
import string
import base64
import os

db = SQLAlchemy()

class UserType(Enum):
    CUSTOMER = 'customer'
    COMPANY = 'company'

class OrderStatus(Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    REFUNDED = 'refunded'

class TicketStatus(Enum):
    VALID = 'valid'
    USED = 'used'
    CANCELLED = 'cancelled'

class PaymentMethodType(Enum):
    CREDIT_CARD = 'credit-card'
    PAYPAL = 'paypal'
    APPLE_PAY = 'apple-pay'

class ValidationMethod(Enum):
    QR_SCAN = 'qr_scan'
    MANUAL = 'manual'
    APP = 'app'


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.Enum(UserType), nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('UserSession', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('Event', backref='company', lazy=True, cascade='all, delete-orphan')
    payment_methods = db.relationship('PaymentMethod', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'firstName': self.first_name,
            'lastName': self.last_name,
            'userType': self.user_type.value,
            'phone': self.phone,
            'avatarUrl': self.avatar_url,
            'isActive': self.is_active,
            'emailVerified': self.email_verified,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if self.user_type == UserType.COMPANY:
            data['companyName'] = self.company_name
            
        return data


class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    device_info = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (
        db.Index('idx_user_expires', 'user_id', 'expires_at'),
    )


class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.DateTime, nullable=False)
    venue = db.Column(db.String(255), nullable=False)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    category = db.Column(db.String(100), nullable=True, index=True)
    image_url = db.Column(db.String(500), nullable=True)
    total_tickets = db.Column(db.Integer, nullable=False)
    available_tickets = db.Column(db.Integer, nullable=False)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ticket_types = db.relationship('TicketType', backref='event', lazy=True, cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='event', lazy=True, cascade='all, delete-orphan')
    tickets = db.relationship('Ticket', backref='event', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_company_date', 'company_id', 'event_date'),
        db.Index('idx_city_date', 'city', 'event_date'),
    )
    
    def to_dict(self):
        """Convert event to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'eventDate': self.event_date.isoformat() if self.event_date else None,
            'venue': self.venue,
            'address': self.address,
            'city': self.city,
            'country': self.country,
            'category': self.category,
            'imageUrl': self.image_url,
            'totalTickets': self.total_tickets,
            'availableTickets': self.available_tickets,
            'basePrice': str(self.base_price),
            'isActive': self.is_active
        }


class TicketType(db.Model):
    __tablename__ = 'ticket_types'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)
    quantity_sold = db.Column(db.Integer, default=0)
    benefits = db.Column(db.Text, nullable=True)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='ticket_type', lazy=True)
    tickets = db.relationship('Ticket', backref='ticket_type', lazy=True)
    
    __table_args__ = (
        db.Index('idx_event_type', 'event_id', 'name'),
    )


class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_id = db.Column(db.String(255), nullable=True)
    billing_address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    tickets = db.relationship('Ticket', backref='order', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_user_status', 'user_id', 'status'),
    )

    @staticmethod
    def generate_order_number():
        """Genera un número único de orden tipo ORD-XXXXXX"""
        prefix = "ORD-"
        suffix = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{suffix}"


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    ticket_type_id = db.Column(db.Integer, db.ForeignKey('ticket_types.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Ticket(db.Model):
    __tablename__ = 'tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    ticket_type_id = db.Column(db.Integer, db.ForeignKey('ticket_types.id'), nullable=False)
    ticket_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    qr_code = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # Denormalized fields
    event_name = db.Column(db.String(255), nullable=False)
    event_location = db.Column(db.String(255), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    holder_name = db.Column(db.String(255), nullable=True)
    holder_email = db.Column(db.String(255), nullable=True)
    seat_number = db.Column(db.String(20), nullable=True)
    section = db.Column(db.String(50), nullable=True)
    
    status = db.Column(db.Enum(TicketStatus), default=TicketStatus.VALID)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    validations = db.relationship('TicketValidation', backref='ticket', lazy=True, cascade='all, delete-orphan')
    
    __table_args__ = (
        db.Index('idx_order_status', 'order_id', 'status'),
    )

    @staticmethod
    def generate_ticket_number():
        """Genera un número único de ticket tipo TCK-XXXXXX"""
        prefix = "TCK-"
        suffix = ''.join(random.choices(string.digits, k=6))
        return f"{prefix}{suffix}"

    @staticmethod
    def generate_qr_code():
        """Genera un string único para el QR del ticket"""
        random_bytes = os.urandom(12)
        return base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')


class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum(PaymentMethodType), nullable=False)
    provider = db.Column(db.String(50), nullable=True)
    card_type = db.Column(db.String(50), nullable=True)
    cardholder_name = db.Column(db.String(255), nullable=True)
    expiry_month = db.Column(db.Integer, nullable=True)
    expiry_year = db.Column(db.Integer, nullable=True)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    card_number = db.Column(db.String(16), nullable=True)  # <-- Añade este campo
    
    __table_args__ = (
        db.Index('idx_user_default', 'user_id', 'is_default'),
    )


class TicketValidation(db.Model):
    __tablename__ = 'ticket_validations'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=False)
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    validation_method = db.Column(db.Enum(ValidationMethod), nullable=False)
    location = db.Column(db.String(255), nullable=True)
    validated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    validator = db.relationship('User', foreign_keys=[validated_by])
    
    __table_args__ = (
        db.Index('idx_ticket_date', 'ticket_id', 'validated_at'),
    )
