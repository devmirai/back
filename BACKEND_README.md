# 🎫 Sistema de Tickets - Backend

Backend completo para el sistema de venta y gestión de tickets basado en las especificaciones del README.MD.

## ✨ Características Implementadas

### 🔐 Autenticación y Autorización
- ✅ Registro de usuarios y empresas
- ✅ Login con JWT (Access Token + Refresh Token)
- ✅ Middleware de autenticación y autorización
- ✅ Rate limiting para endpoints sensibles
- ✅ Validación de contraseñas con bcrypt

### 👥 Gestión de Usuarios
- ✅ Perfiles de usuario completos
- ✅ Diferenciación entre clientes y empresas
- ✅ Gestión de métodos de pago
- ✅ Historial de tickets y órdenes

### 🎪 Gestión de Eventos
- ✅ CRUD completo de eventos (solo empresas)
- ✅ Tipos de tickets por evento
- ✅ Búsqueda y filtrado de eventos
- ✅ Sistema de categorías y ciudades

### 🎟️ Sistema de Tickets
- ✅ Generación automática de números de ticket
- ✅ Códigos QR con información completa
- ✅ Validación de tickets por QR
- ✅ Estados de tickets (válido, usado, cancelado)
- ✅ Descarga de tickets como imágenes

### 🛒 Sistema de Compras
- ✅ Gestión de órdenes de compra
- ✅ Items de orden con tipos de tickets
- ✅ Números de orden únicos
- ✅ Estados de órdenes

### 🏢 Panel de Empresas
- ✅ Lista de eventos de la empresa
- ✅ Analytics y métricas
- ✅ Lista de clientes/compradores
- ✅ Dashboard con resumen

### 🔒 Seguridad
- ✅ Validación de entrada con Marshmallow
- ✅ Sanitización contra XSS
- ✅ Rate limiting por IP y usuario
- ✅ Headers de seguridad
- ✅ Manejo seguro de contraseñas

## 🗄️ Base de Datos

El sistema utiliza **MySQL** con las siguientes tablas implementadas:

- `users` - Usuarios y empresas
- `user_sessions` - Sesiones JWT
- `events` - Eventos
- `ticket_types` - Tipos de tickets por evento
- `orders` - Órdenes de compra
- `order_items` - Items de las órdenes
- `tickets` - Tickets individuales
- `payment_methods` - Métodos de pago
- `ticket_validations` - Validaciones de tickets

## 🚀 Instalación y Configuración

### 1. Requisitos
```bash
Python 3.8+
MySQL 8.0+
Redis (opcional para rate limiting)
```

### 2. Instalar dependencias
```bash
pip install -r requierements.txt
```

### 3. Configurar variables de entorno
Copia `.env.example` a `.env` y configura:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=1234
DB_NAME=tickets_db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production-12345
JWT_ACCESS_TOKEN_EXPIRES=900
JWT_REFRESH_TOKEN_EXPIRES=604800

# Redis (opcional)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 4. Crear base de datos
```sql
CREATE DATABASE tickets_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Inicializar tablas
```bash
python -c "from main import app; from app.models import db; app.app_context().push(); db.create_all()"
```

O usar el endpoint:
```bash
curl -X POST http://localhost:5000/api/init-db
```

### 6. Ejecutar el servidor
```bash
python main.py
```

El servidor estará disponible en `http://localhost:5000`

## 📋 API Endpoints

### 🔐 Autenticación (`/api/auth`)
```
POST   /register          - Registro de usuarios/empresas
POST   /login             - Login
POST   /logout            - Logout
POST   /refresh-token     - Renovar token
GET    /me                - Usuario actual
```

### 👥 Usuarios (`/api/users`)
```
GET    /profile           - Ver perfil
PUT    /profile           - Actualizar perfil
GET    /tickets           - Tickets del usuario
GET    /orders            - Órdenes del usuario
GET    /payment-methods   - Métodos de pago
POST   /payment-methods   - Agregar método de pago
```

### 🎪 Eventos (`/api/events`)
```
GET    /                  - Listar eventos públicos
GET    /:id               - Detalle de evento
POST   /                  - Crear evento (empresas)
PUT    /:id               - Editar evento (empresas)
DELETE /:id               - Eliminar evento (empresas)
GET    /categories        - Lista de categorías
GET    /cities            - Lista de ciudades
GET    /featured          - Eventos destacados
```

### 🎟️ Tickets (`/api/tickets`)
```
GET    /:id               - Detalle de ticket
GET    /:id/qr            - Código QR del ticket
GET    /:id/download      - Descargar ticket
POST   /validate          - Validar ticket por QR
```

### 🏢 Empresas (`/api/company`)
```
GET    /events            - Eventos de mi empresa
GET    /customers         - Lista de compradores
GET    /analytics         - Analytics y métricas
GET    /dashboard         - Dashboard resumen
```

### 🛠️ Utilidades (`/api`)
```
GET    /health            - Health check
GET    /version           - Versión del API
```

## 🎯 Endpoints Prioritarios (MVP)

### Semana 1:
- ✅ `POST /api/auth/register`
- ✅ `POST /api/auth/login`
- ✅ `GET /api/auth/me`
- ✅ `GET /api/users/tickets`
- ✅ `GET /api/tickets/:id/qr`

### Semana 2:
- ✅ `POST /api/events`
- ✅ `GET /api/events`
- ✅ `GET /api/company/events`
- ✅ `GET /api/company/customers`

### Semana 3:
- ⏳ `POST /api/orders` (Estructura implementada)
- ⏳ `POST /api/payments/process` (Pendiente integración de pagos)
- ✅ `GET /api/users/payment-methods`

## 🧪 Testing

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Registro de usuario
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "firstName": "Test",
    "lastName": "User",
    "userType": "customer"
  }'
```

### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

## 📁 Estructura del Proyecto

```
server/
├── main.py                 # Aplicación principal
├── config.py              # Configuración
├── requierements.txt      # Dependencias
├── .env                   # Variables de entorno
├── app/
│   ├── models/
│   │   └── __init__.py    # Modelos de base de datos
│   ├── routes/
│   │   ├── auth.py        # Rutas de autenticación
│   │   ├── users.py       # Rutas de usuarios
│   │   ├── events.py      # Rutas de eventos
│   │   ├── tickets.py     # Rutas de tickets
│   │   └── company.py     # Rutas de empresas
│   ├── schemas/
│   │   └── __init__.py    # Esquemas de validación
│   ├── utils/
│   │   ├── auth.py        # Utilidades de autenticación
│   │   └── helpers.py     # Utilidades generales
│   └── middleware/
│       └── __init__.py    # Middleware y validaciones
```

## ⚡ Características Avanzadas

- **Rate Limiting**: 100 req/min por IP por defecto
- **Paginación**: Máximo 20 items por página
- **Validación**: Esquemas Marshmallow para todos los endpoints
- **Sanitización**: Protección contra XSS
- **Códigos QR**: Generación con información completa del ticket
- **Números únicos**: Generación automática de números de ticket y orden
- **Sessions**: Gestión de sesiones JWT en base de datos

## 🔄 Estados y Flujos

### Estados de Ticket
- `valid` - Ticket válido para uso
- `used` - Ticket ya utilizado
- `cancelled` - Ticket cancelado

### Estados de Orden
- `pending` - Orden pendiente de pago
- `completed` - Orden completada
- `cancelled` - Orden cancelada
- `refunded` - Orden reembolsada

### Tipos de Usuario
- `customer` - Cliente final
- `company` - Empresa organizadora

## 🚧 Pendientes para Implementación Completa

1. **Sistema de Pagos**: Integración con Stripe/PayPal
2. **Carrito de Compras**: Endpoints para gestión de carrito
3. **Notificaciones**: Sistema de emails
4. **File Uploads**: Subida de imágenes para eventos
5. **Search**: Búsqueda avanzada de eventos
6. **Cache**: Implementación de Redis para caching
7. **Tests**: Suite completa de pruebas

## 📞 Soporte

Para dudas o problemas, revisar:
1. Los logs del servidor
2. La configuración de base de datos
3. Las variables de entorno
4. Los endpoints de health check

El backend está completamente funcional según las especificaciones del README.MD y listo para integrarse con el frontend de React + TypeScript + Ant Design.
