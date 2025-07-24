"""
🎫 Sistema de Tickets - Esquemas de Validación
Esquemas para validar datos de entrada basados en las especificaciones del README.MD
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import User, Event, Order, Ticket, PaymentMethod

# Base validation patterns
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PHONE_REGEX = r'^\+?[\d\s\-\(\)]{8,20}$'

class UserRegistrationSchema(Schema):
    """Schema for user registration"""
    email = fields.Email(required=True, validate=validate.Regexp(EMAIL_REGEX))
    password = fields.Str(required=True, validate=validate.Length(min=8))
    firstName = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    lastName = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    phone = fields.Str(allow_none=True, validate=validate.Regexp(PHONE_REGEX))
    userType = fields.Str(required=True, validate=validate.OneOf(['customer', 'company']))
    companyName = fields.Str(allow_none=True, validate=validate.Length(max=255))
    
    @validates('companyName')
    def validate_company_name(self, value):
        """Validate that companyName is provided for company users"""
        user_type = self.context.get('userType')
        if user_type == 'company' and not value:
            raise ValidationError('Company name is required for company accounts')

class UserLoginSchema(Schema):
    """Schema for user login"""
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class UserUpdateSchema(Schema):
    """Schema for updating user profile"""
    firstName = fields.Str(validate=validate.Length(min=2, max=100))
    lastName = fields.Str(validate=validate.Length(min=2, max=100))
    phone = fields.Str(allow_none=True, validate=validate.Regexp(PHONE_REGEX))
    companyName = fields.Str(allow_none=True, validate=validate.Length(max=255))

class EventCreateSchema(Schema):
    """Schema for creating events"""
    title = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    description = fields.Str(allow_none=True)
    eventDate = fields.DateTime(required=True, format='iso')
    venue = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    address = fields.Str(allow_none=True)
    city = fields.Str(allow_none=True, validate=validate.Length(max=100))
    country = fields.Str(allow_none=True, validate=validate.Length(max=100))
    category = fields.Str(allow_none=True, validate=validate.Length(max=100))
    imageUrl = fields.Url(allow_none=True)
    totalTickets = fields.Int(required=True, validate=validate.Range(min=1, max=100000))
    basePrice = fields.Decimal(required=True, validate=validate.Range(min=0))

class EventUpdateSchema(Schema):
    """Schema for updating events"""
    title = fields.Str(validate=validate.Length(min=3, max=255))
    description = fields.Str(allow_none=True)
    eventDate = fields.DateTime(format='iso')
    venue = fields.Str(validate=validate.Length(min=3, max=255))
    address = fields.Str(allow_none=True)
    city = fields.Str(validate=validate.Length(max=100))
    country = fields.Str(validate=validate.Length(max=100))
    category = fields.Str(validate=validate.Length(max=100))
    imageUrl = fields.Url(allow_none=True)
    totalTickets = fields.Int(validate=validate.Range(min=1, max=100000))
    basePrice = fields.Decimal(validate=validate.Range(min=0))
    isActive = fields.Bool()

class TicketTypeSchema(Schema):
    """Schema for ticket types"""
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    description = fields.Str(allow_none=True)
    price = fields.Decimal(required=True, validate=validate.Range(min=0))
    quantityAvailable = fields.Int(required=True, validate=validate.Range(min=1))
    benefits = fields.Str(allow_none=True)  # JSON string

class PaymentMethodSchema(Schema):
    """Schema for payment methods"""
    type = fields.Str(required=True, validate=validate.OneOf(['credit-card', 'paypal', 'apple-pay']))
    provider = fields.Str(allow_none=True, validate=validate.Length(max=50))
    cardType = fields.Str(allow_none=True, validate=validate.Length(max=50))
    lastFourDigits = fields.Str(allow_none=True, validate=validate.Length(equal=4))
    cardholderName = fields.Str(allow_none=True, validate=validate.Length(max=255))
    expiryMonth = fields.Int(allow_none=True, validate=validate.Range(min=1, max=12))
    expiryYear = fields.Int(allow_none=True, validate=validate.Range(min=2024, max=2050))
    isDefault = fields.Bool(missing=False)
    cardNumber = fields.Str(allow_none=True, validate=validate.Length(equal=16))  # <-- Añade esta línea

class OrderCreateSchema(Schema):
    """Schema for creating orders"""
    items = fields.List(fields.Dict(), required=True, validate=validate.Length(min=1))
    paymentMethodId = fields.Int(allow_none=True)
    billingAddress = fields.Str(allow_none=True)

class OrderItemSchema(Schema):
    """Schema for order items"""
    eventId = fields.Int(required=True)
    ticketTypeId = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1, max=10))

class TicketValidationSchema(Schema):
    """Schema for ticket validation"""
    qrCode = fields.Str(required=True)
    location = fields.Str(allow_none=True, validate=validate.Length(max=255))
    validationMethod = fields.Str(required=True, validate=validate.OneOf(['qr_scan', 'manual', 'app']))

class SearchEventsSchema(Schema):
    """Schema for searching events"""
    page = fields.Int(validate=validate.Range(min=1), missing=1)
    perPage = fields.Int(validate=validate.Range(min=1, max=100), missing=20)
    category = fields.Str(allow_none=True)
    city = fields.Str(allow_none=True)
    search = fields.Str(allow_none=True)
    dateFrom = fields.DateTime(allow_none=True, format='iso')
    dateTo = fields.DateTime(allow_none=True, format='iso')
    minPrice = fields.Decimal(allow_none=True, validate=validate.Range(min=0))
    maxPrice = fields.Decimal(allow_none=True, validate=validate.Range(min=0))

class PasswordChangeSchema(Schema):
    """Schema for changing password"""
    currentPassword = fields.Str(required=True)
    newPassword = fields.Str(required=True, validate=validate.Length(min=8))
    confirmPassword = fields.Str(required=True)
    
    @validates('confirmPassword')
    def validate_passwords_match(self, value):
        """Validate that new passwords match"""
        new_password = self.context.get('newPassword')
        if new_password and value != new_password:
            raise ValidationError('Passwords do not match')

# Export all schemas
__all__ = [
    'UserRegistrationSchema',
    'UserLoginSchema', 
    'UserUpdateSchema',
    'EventCreateSchema',
    'EventUpdateSchema',
    'TicketTypeSchema',
    'PaymentMethodSchema',
    'OrderCreateSchema',
    'OrderItemSchema',
    'TicketValidationSchema',
    'SearchEventsSchema',
    'PasswordChangeSchema'
]

class TicketValidationSchema(Schema):
    qrCode = fields.Str(required=True)
    location = fields.Str()
    validationMethod = fields.Str(validate=validate.OneOf(['qr_scan', 'manual', 'app']))
