# 🎫 Sistema de Tickets - Especificaciones Backend

## 📋 Descripción del Proyecto

Sistema completo de venta y gestión de tickets para eventos con autenticación diferenciada para usuarios finales y empresas organizadoras.

### Características Principales:
- Registro y login para usuarios y empresas
- Compra de tickets con carrito de compras
- Gestión de eventos (CRUD) para empresas
- Visualización y descarga de tickets con códigos QR
- Sistema de pagos integrado
- Dashboard para empresas con analytics
- Validación de tickets mediante QR

---

## 🗄️ ESTRUCTURA DE BASE DE DATOS

### 1. Tabla `users`
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_type ENUM('customer', 'company') NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    company_name VARCHAR(255), -- Solo para empresas
    phone VARCHAR(20),
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_email (email),
    INDEX idx_user_type (user_type)
);
```

### 2. Tabla `user_sessions`
```sql
CREATE TABLE user_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    device_info TEXT,
    ip_address VARCHAR(45),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_token_hash (token_hash),
    INDEX idx_user_expires (user_id, expires_at)
);
```

### 3. Tabla `events`
```sql
CREATE TABLE events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    company_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_date DATETIME NOT NULL,
    venue VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    category VARCHAR(100),
    image_url VARCHAR(500),
    total_tickets INT NOT NULL,
    available_tickets INT NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_company_date (company_id, event_date),
    INDEX idx_city_date (city, event_date),
    INDEX idx_category (category)
);
```

### 4. Tabla `ticket_types`
```sql
CREATE TABLE ticket_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    event_id INT NOT NULL,
    name VARCHAR(100) NOT NULL, -- VIP, General, Estudiante
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    quantity_available INT NOT NULL,
    quantity_sold INT DEFAULT 0,
    benefits TEXT, -- JSON con beneficios
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    INDEX idx_event_type (event_id, name)
);
```

### 5. Tabla `orders`
```sql
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'completed', 'cancelled', 'refunded') DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_id VARCHAR(255), -- ID del procesador de pagos
    billing_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_status (user_id, status),
    INDEX idx_order_number (order_number)
);
```

### 6. Tabla `order_items`
```sql
CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    event_id INT NOT NULL,
    ticket_type_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(id) ON DELETE CASCADE
);
```

### 7. Tabla `tickets`
```sql
CREATE TABLE tickets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    event_id INT NOT NULL,
    ticket_type_id INT NOT NULL,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    qr_code VARCHAR(255) UNIQUE NOT NULL,
    -- Campos desnormalizados para evitar JOINs constantes
    event_name VARCHAR(255) NOT NULL,
    event_location VARCHAR(255) NOT NULL,
    event_date DATETIME NOT NULL,
    holder_name VARCHAR(255),
    holder_email VARCHAR(255),
    seat_number VARCHAR(20), -- Si aplica
    section VARCHAR(50), -- Si aplica
    status ENUM('valid', 'used', 'cancelled') DEFAULT 'valid',
    used_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
    FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(id) ON DELETE CASCADE,
    INDEX idx_order_status (order_id, status),
    INDEX idx_qr_code (qr_code),
    INDEX idx_ticket_number (ticket_number)
);
```

### 8. Tabla `payment_methods`
```sql
CREATE TABLE payment_methods (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    type ENUM('credit-card', 'paypal', 'apple-pay') NOT NULL,
    provider VARCHAR(50), -- Visa, Mastercard, PayPal, etc.
    card_type VARCHAR(50), -- Visa, Mastercard, American Express
    last_four_digits VARCHAR(4),
    cardholder_name VARCHAR(255),
    expiry_month INT,
    expiry_year INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_default (user_id, is_default)
);
```

### 9. Tabla `ticket_validations`
```sql
CREATE TABLE ticket_validations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_id INT NOT NULL,
    validated_by INT, -- ID del usuario que validó
    validation_method ENUM('qr_scan', 'manual', 'app') NOT NULL,
    location VARCHAR(255),
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (validated_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_ticket_date (ticket_id, validated_at)
);
```

---

## 🛣️ RUTAS API REQUERIDAS

### Autenticación
```
POST   /api/auth/register          - Registro de usuarios/empresas
POST   /api/auth/login             - Login con email/password  
POST   /api/auth/logout            - Logout y limpieza de sesión
POST   /api/auth/refresh-token     - Renovar JWT token
GET    /api/auth/me                - Obtener info del usuario actual
```

**Campos requeridos para registro:**
```json
{
  "email": "string",
  "password": "string", 
  "firstName": "string",
  "lastName": "string",
  "phone": "string?",
  "userType": "customer | company",
  "companyName": "string?" // Solo si userType === 'company'
}
```

**Respuesta de login:**
```json
{
  "user": {
    "id": "string",
    "email": "string", 
    "firstName": "string",
    "lastName": "string",
    "userType": "customer | company",
    "companyName": "string?",
    "createdAt": "string"
  },
  "token": "string",
  "refreshToken": "string"
}
```

### Gestión de Usuarios
```
GET    /api/users/profile          - Ver perfil completo
PUT    /api/users/profile          - Actualizar datos del perfil
POST   /api/users/upload-avatar    - Subir foto de perfil
GET    /api/users/tickets          - Listar todos los tickets del usuario
GET    /api/users/orders           - Órdenes del usuario
GET    /api/users/payment-methods  - Métodos de pago guardados
POST   /api/users/payment-methods  - Agregar nuevo método de pago
PUT    /api/users/payment-methods/:id - Actualizar método de pago
DELETE /api/users/payment-methods/:id - Eliminar método de pago
```

**Estructura UserTicket (para /api/users/tickets):**
```json
{
  "id": "string",
  "orderId": "string", 
  "eventName": "string",
  "eventDate": "string",
  "eventLocation": "string", 
  "quantity": "number",
  "totalPrice": "number",
  "purchaseDate": "string",
  "status": "valid | used | cancelled",
  "ticketNumber": "string"
}
```

**Estructura PaymentMethod:**
```json
{
  "id": "string",
  "type": "credit-card | paypal | apple-pay",
  "lastFour": "string?", 
  "cardType": "string?", // Visa, Mastercard, etc.
  "isDefault": "boolean",
  "expiryDate": "string?" // MM/YY format
}
```

### Gestión de Tickets
```
GET    /api/tickets/:id            - Detalle específico de un ticket
GET    /api/tickets/:id/qr         - Generar código QR del ticket
GET    /api/tickets/:id/download   - Descargar ticket como imagen PNG
POST   /api/tickets/validate       - Validar ticket por código QR
```

### Gestión de Eventos (Solo Empresas)
```
GET    /api/events                 - Listar eventos públicos
GET    /api/events/:id             - Detalle de evento específico
POST   /api/events                 - Crear nuevo evento
PUT    /api/events/:id             - Editar evento
DELETE /api/events/:id             - Eliminar evento
PATCH  /api/events/:id/status      - Activar/desactivar evento
GET    /api/company/events         - Eventos de mi empresa
GET    /api/company/customers      - Lista de compradores
```

**Estructura Event:**
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "eventDate": "string",
  "venue": "string", 
  "address": "string",
  "city": "string",
  "category": "string",
  "imageUrl": "string",
  "totalTickets": "number",
  "availableTickets": "number",
  "basePrice": "number"
}
```

**Estructura EventPurchaser (para empresas):**
```json
{
  "id": "string",
  "customerName": "string",
  "email": "string", 
  "phone": "string?",
  "quantity": "number",
  "totalPaid": "number",
  "purchaseDate": "string",
  "orderId": "string"
}
```

### Sistema de Compras
```
POST   /api/cart/add               - Agregar al carrito
GET    /api/cart                   - Ver carrito actual
PUT    /api/cart/update            - Actualizar cantidad
DELETE /api/cart/remove            - Remover del carrito
POST   /api/orders                 - Crear orden de compra
GET    /api/orders/:id             - Detalle de orden
POST   /api/payments/process       - Procesar pago
POST   /api/payments/webhook       - Webhook de confirmación
```

### Búsqueda y Filtros
```
GET    /api/search/events          - Búsqueda de eventos
GET    /api/events/categories      - Lista de categorías
GET    /api/events/cities          - Lista de ciudades
GET    /api/events/featured        - Eventos destacados
```

### Utilidades del Sistema
```
GET    /api/health                 - Health check del API
GET    /api/version                - Versión del API
POST   /api/upload/image           - Subir imágenes
```

---

## 🔐 ESPECIFICACIONES DE SEGURIDAD

### Autenticación JWT
- **Access Token**: Duración 15 minutos
- **Refresh Token**: Duración 7 días
- **Algoritmo**: HS256 o RS256
- **Claims requeridos**: `user_id`, `user_type`, `email`, `exp`, `iat`

### Middleware de Protección
```javascript
// Aplicar a rutas protegidas:
- JWT validation
- Rate limiting (100 req/min por IP)
- Request validation (Joi/Yup)
- Sanitización de inputs
- CORS configurado
- Helmet para headers de seguridad
```

### Validaciones Importantes
- **Passwords**: Mínimo 8 caracteres, bcrypt con salt rounds 12
- **Emails**: Validación RFC5322
- **XSS Protection**: Sanitizar todos los inputs de usuario
- **SQL Injection**: Usar prepared statements
- **File uploads**: Validar tipo MIME y tamaño (máx 5MB para imágenes)

---

## 💾 TECNOLOGÍAS RECOMENDADAS

### Backend Framework
```bash
# Opción 1: Node.js + Express
npm install express cors helmet bcryptjs jsonwebtoken
npm install mysql2 sequelize joi multer
npm install stripe qrcode canvas

# Opción 2: Python + FastAPI  
pip install fastapi uvicorn sqlalchemy bcrypt
pip install python-jose mysql-connector-python
pip install stripe qrcode pillow
```

### Base de Datos
- **MySQL 8.0+** o **PostgreSQL 13+**
- **Redis** para sessions y caching
- **Cloudinary** o **AWS S3** para almacenamiento de imágenes

---

## 📝 NOTAS DE IMPLEMENTACIÓN

### Prioridades de Desarrollo
1. **FASE 1**: Autenticación + Perfil + Tickets básicos
2. **FASE 2**: CRUD de eventos para empresas  
3. **FASE 3**: Sistema de compras y pagos
4. **FASE 4**: Validación de tickets y analytics

### Campos Críticos del Frontend
- Los campos `status` de tickets deben ser exactamente: `'valid' | 'used' | 'cancelled'`
- Los tipos de payment methods: `'credit-card' | 'paypal' | 'apple-pay'`
- La estructura UserTicket debe incluir campos desnormalizados para performance
- Los códigos QR deben generarse con información completa del ticket

### Consideraciones de Performance
- Usar índices en campos de búsqueda frecuente
- Desnormalizar datos en tabla tickets para evitar JOINs
- Implementar caching para eventos populares
- Paginar resultados de búsqueda (máx 20 items por página)

---

## 🎯 ENDPOINTS PRIORITARIOS PARA MVP

### Implementar PRIMERO (Semana 1):
```
POST /api/auth/register
POST /api/auth/login  
GET  /api/auth/me
GET  /api/users/tickets
GET  /api/tickets/:id/qr
```

### Implementar SEGUNDO (Semana 2):
```
POST /api/events
GET  /api/events
GET  /api/company/events
GET  /api/company/customers
```

### Implementar TERCERO (Semana 3):
```
POST /api/orders
POST /api/payments/process
GET  /api/users/payment-methods
```

---

**Fecha de creación**: Julio 2025  
**Proyecto**: Sistema de Tickets  
**Frontend**: React + TypeScript + Ant Design  
**Estado**: Especificaciones para implementación backend
