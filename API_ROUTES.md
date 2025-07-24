# 🎫 Sistema de Tickets - API Routes Documentation

Este documento describe todas las rutas disponibles en el backend del sistema de tickets.

## Base URL
```
http://localhost:5000
```

## 📋 Tabla de Contenidos
- [Autenticación](#autenticación)
- [Usuarios](#usuarios)
- [Eventos](#eventos)
- [Tickets](#tickets)
- [Empresa/Compañía](#empresacompañía)
- [Sistema](#sistema)

---

## 🔐 Autenticación
**Base URL:** `/api/auth`

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `POST` | `/register` | Registrar nuevo usuario o empresa | ❌ |
| `POST` | `/login` | Iniciar sesión | ❌ |
| `POST` | `/logout` | Cerrar sesión | ✅ JWT |
| `POST` | `/refresh-token` | Renovar token de acceso | ❌ |
| `GET` | `/me` | Obtener información del usuario actual | ✅ JWT |
| `POST` | `/verify-email` | Verificar correo electrónico | ❌ |
| `POST` | `/change-password` | Cambiar contraseña | ✅ JWT |

### 📝 Detalles de Autenticación

#### POST `/api/auth/register`
Registra un nuevo usuario o empresa.

**Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "firstName": "Juan",
  "lastName": "Pérez",
  "phone": "+1234567890",
  "userType": "customer", // "customer" o "company"
  "companyName": "Mi Empresa" // Solo si userType es "company"
}
```

#### POST `/api/auth/login`
Inicia sesión y devuelve tokens de acceso.

**Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

---

## 👤 Usuarios
**Base URL:** `/api/users`

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/profile` | Obtener perfil del usuario | ✅ JWT |
| `PUT` | `/profile` | Actualizar perfil del usuario | ✅ JWT |
| `GET` | `/tickets` | Obtener tickets del usuario | ✅ JWT |
| `GET` | `/orders` | Obtener órdenes del usuario | ✅ JWT |
| `GET` | `/payment-methods` | Obtener métodos de pago | ✅ JWT |
| `POST` | `/payment-methods` | Agregar método de pago | ✅ JWT |
| `PUT` | `/payment-methods/{id}` | Actualizar método de pago | ✅ JWT |
| `DELETE` | `/payment-methods/{id}` | Eliminar método de pago | ✅ JWT |
| `POST` | `/upload-avatar` | Subir avatar del usuario | ✅ JWT |

### 📝 Detalles de Usuarios

#### PUT `/api/users/profile`
Actualiza el perfil del usuario.

**Body:**
```json
{
  "firstName": "Juan",
  "lastName": "Pérez",
  "phone": "+1234567890",
  "companyName": "Mi Empresa" // Solo para usuarios tipo empresa
}
```

#### GET `/api/users/orders`
Obtiene las órdenes del usuario con paginación.

**Query Parameters:**
- `page`: Número de página (default: 1)
- `per_page`: Elementos por página (max: 20, default: 20)

---

## 🎪 Eventos
**Base URL:** `/api/events`

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/` | Listar eventos públicos con filtros | ❌ |
| `GET` | `/{id}` | Obtener detalles de un evento | ❌ |
| `POST` | `/` | Crear nuevo evento | ✅ JWT + Company |
| `PUT` | `/{id}` | Actualizar evento | ✅ JWT + Company |
| `DELETE` | `/{id}` | Eliminar evento | ✅ JWT + Company |
| `PATCH` | `/{id}/status` | Cambiar estado del evento | ✅ JWT + Company |
| `POST` | `/{id}/ticket-types` | Agregar tipo de ticket | ✅ JWT + Company |
| `GET` | `/categories` | Obtener categorías disponibles | ❌ |
| `GET` | `/cities` | Obtener ciudades disponibles | ❌ |
| `GET` | `/featured` | Obtener eventos destacados | ❌ |

### 📝 Detalles de Eventos

#### GET `/api/events`
Lista eventos públicos con filtros opcionales.

**Query Parameters:**
- `page`: Número de página (default: 1)
- `per_page`: Elementos por página (max: 20, default: 20)
- `category`: Filtrar por categoría
- `city`: Filtrar por ciudad
- `search`: Búsqueda de texto
- `date_from`: Fecha desde (YYYY-MM-DD)
- `date_to`: Fecha hasta (YYYY-MM-DD)

#### POST `/api/events`
Crea un nuevo evento (solo empresas).

**Body:**
```json
{
  "title": "Mi Evento",
  "description": "Descripción del evento",
  "date": "2024-12-31T20:00:00Z",
  "location": "Centro de Convenciones",
  "address": "Calle 123, Ciudad",
  "city": "Bogotá",
  "category": "Concierto",
  "capacity": 1000,
  "imageUrl": "https://example.com/image.jpg"
}
```

---

## 🎫 Tickets
**Base URL:** `/api/tickets`

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/{id}` | Obtener detalles de un ticket | ✅ JWT |
| `GET` | `/{id}/qr` | Obtener código QR del ticket | ✅ JWT |
| `GET` | `/{id}/download` | Descargar ticket en PDF | ✅ JWT |
| `POST` | `/validate` | Validar ticket por QR | ✅ JWT + Company |
| `POST` | `/batch-validate` | Validar múltiples tickets | ✅ JWT + Company |

### 📝 Detalles de Tickets

#### POST `/api/tickets/validate`
Valida un ticket escaneando su código QR (solo empresas).

**Body:**
```json
{
  "qrCode": "ticket_qr_code_data",
  "location": "Entrada Principal",
  "validationMethod": "qr_scan" // "qr_scan", "manual", "app"
}
```

#### POST `/api/tickets/batch-validate`
Valida múltiples tickets de una vez (solo empresas).

**Body:**
```json
{
  "qrCodes": ["qr1", "qr2", "qr3"],
  "location": "Entrada Principal"
}
```

---

## 🏢 Empresa/Compañía
**Base URL:** `/api/company`

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/events` | Obtener eventos de la empresa | ✅ JWT + Company |
| `GET` | `/customers` | Obtener clientes de la empresa | ✅ JWT + Company |
| `GET` | `/analytics` | Obtener analíticas de la empresa | ✅ JWT + Company |
| `GET` | `/events/{id}/attendees` | Obtener asistentes de un evento | ✅ JWT + Company |
| `GET` | `/dashboard` | Obtener datos del dashboard | ✅ JWT + Company |

### 📝 Detalles de Empresa

#### GET `/api/company/events`
Obtiene todos los eventos de la empresa actual.

**Query Parameters:**
- `page`: Número de página (default: 1)
- `per_page`: Elementos por página (max: 20, default: 20)
- `status`: Filtrar por estado ("active", "inactive", "all")

#### GET `/api/company/analytics`
Obtiene analíticas detalladas de la empresa.

**Query Parameters:**
- `date_from`: Fecha desde (YYYY-MM-DD)
- `date_to`: Fecha hasta (YYYY-MM-DD)

**Respuesta incluye:**
- Ventas totales
- Número de eventos
- Tickets vendidos
- Ingresos por evento
- Estadísticas de asistencia

---

## ⚙️ Sistema
**Base URL:** `/api`

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| `GET` | `/health` | Verificar estado del API | ❌ |
| `GET` | `/version` | Obtener versión del API | ❌ |
| `POST` | `/init-db` | Inicializar base de datos | ❌ |

### 📝 Detalles del Sistema

#### GET `/api/health`
Verifica que el API esté funcionando correctamente.

**Respuesta:**
```json
{
  "status": "OK",
  "message": "API is running"
}
```

#### GET `/api/version`
Obtiene información de la versión del API.

**Respuesta:**
```json
{
  "version": "1.0.0",
  "build": "MVP"
}
```

#### POST `/api/init-db`
Inicializa las tablas de la base de datos (solo para desarrollo).

---

## 🔒 Autenticación y Autorización

### JWT Token
La mayoría de endpoints requieren un token JWT válido en el header:
```
Authorization: Bearer <jwt_token>
```

### Tipos de Usuario
- **Customer**: Usuarios regulares que pueden comprar tickets
- **Company**: Empresas que pueden crear y gestionar eventos

### Rate Limiting
El API tiene límites de velocidad configurados:
- **Default**: 100 peticiones por minuto, 1000 por hora
- **Algunos endpoints específicos**: Límites más restrictivos

---

## 📝 Esquemas de Respuesta

### Respuesta Exitosa
```json
{
  "data": { /* contenido de la respuesta */ },
  "message": "Operación exitosa"
}
```

### Respuesta de Error
```json
{
  "error": "Mensaje de error",
  "details": "Detalles adicionales del error"
}
```

### Paginación
```json
{
  "data": [/* elementos */],
  "pagination": {
    "page": 1,
    "pages": 10,
    "perPage": 20,
    "total": 200,
    "hasNext": true,
    "hasPrev": false
  }
}
```

---

## 🗄️ Base de Datos

### Configuración Actual
- **Motor**: MySQL
- **Host**: localhost:3306
- **Base de datos**: tickets_db
- **Usuario**: root (sin contraseña)

### Estado de Conexión
El sistema está configurado para conectarse automáticamente a MySQL y muestra mensajes de conexión en la consola:
```
🔧 Configuración de base de datos: mysql+pymysql://root:@localhost:3306/tickets_db
🔧 Base de datos configurada: tickets_db
```

---

## 🚀 Notas de Desarrollo

1. **Servidor de Desarrollo**: Corre en `http://localhost:5000`
2. **Debug Mode**: Habilitado por defecto
3. **CORS**: Configurado para permitir `localhost:3000` y `localhost:3001`
4. **Rate Limiting**: Usando memoria en lugar de Redis para desarrollo
5. **File Uploads**: Limitado a 5MB, formatos: PNG, JPG, JPEG, GIF, PDF

---

*Documentación generada automáticamente - Sistema de Tickets v1.0.0*
