-- Datos de ejemplo para tickets_db

USE tickets_db;

-- Usuarios
INSERT INTO users (id, email, password_hash, user_type, first_name, last_name, company_name, phone, avatar_url, is_active, email_verified, created_at, updated_at)
VALUES
  (1, 'cliente1@example.com', 'hash1', 'customer', 'Carlos', 'Ramírez', NULL, '+573001234567', NULL, 1, 1, NOW(), NOW()),
  (2, 'empresa1@example.com', 'hash2', 'company', 'Empresa', 'Ejemplo', 'Eventos S.A.', '+573002345678', NULL, 1, 1, NOW(), NOW());

-- Eventos
INSERT INTO events (id, company_id, title, description, event_date, venue, address, city, country, category, image_url, total_tickets, available_tickets, base_price, is_active, created_at, updated_at)
VALUES
  (1, 2, 'Concierto Rock', 'Concierto de rock nacional', '2025-09-15 20:00:00', 'Estadio Nacional', 'Av. Principal 123', 'Bogotá', 'Colombia', 'Concierto', 'https://example.com/rock.jpg', 5000, 5000, 50000, 1, NOW(), NOW()),
  (2, 2, 'Feria de Tecnología', 'Exposición de tecnología e innovación', '2025-10-10 10:00:00', 'Centro de Convenciones', 'Calle 45 #10-20', 'Medellín', 'Colombia', 'Feria', 'https://example.com/tech.jpg', 2000, 2000, 30000, 1, NOW(), NOW());

-- Tipos de Ticket
INSERT INTO ticket_types (id, event_id, name, description, price, quantity_available, quantity_sold, benefits, created_at)
VALUES
  (1, 1, 'General', 'Entrada general', 50000, 4000, 0, NULL, NOW()),
  (2, 1, 'VIP', 'Entr ada VIP', 120000, 1000, 0, NULL, NOW()),
  (3, 2, 'Entrada', 'Entrada estándar', 30000, 2000, 0, NULL, NOW());

-- Órdenes
INSERT INTO orders (id, user_id, order_number, total_amount, status, payment_method, payment_id, billing_address, created_at, updated_at)
VALUES
  (1, 1, 'ORD-0001', 50000, 'completed', 'credit-card', NULL, NULL, '2025-07-01 12:00:00', '2025-07-01 12:00:00'),
  (2, 1, 'ORD-0002', 120000, 'completed', 'paypal', NULL, NULL, '2025-07-02 15:00:00', '2025-07-02 15:00:00');

-- Tickets
INSERT INTO tickets (id, order_id, event_id, ticket_type_id, ticket_number, qr_code, event_name, event_location, event_date, holder_name, holder_email, seat_number, section, status, used_at, created_at)
VALUES
  (1, 1, 1, 1, 'TCK-0001', 'QR1', 'Concierto Rock', 'Estadio Nacional', '2025-09-15 20:00:00', 'Carlos Ramírez', 'cliente1@example.com', NULL, NULL, 'valid', NULL, '2025-07-01 12:01:00'),
  (2, 2, 1, 2, 'TCK-0002', 'QR2', 'Concierto Rock', 'Estadio Nacional', '2025-09-15 20:00:00', 'Carlos Ramírez', 'cliente1@example.com', NULL, NULL, 'valid', NULL, '2025-07-02 15:01:00');

-- Métodos de pago
INSERT INTO payment_methods (id, user_id, type, provider, card_type, last_four_digits, cardholder_name, expiry_month, expiry_year, is_default, is_active, created_at)
VALUES
  (1, 1, 'credit-card', 'Visa', 'Débito', '1234', 'Carlos Ramírez', 12, 2026, 1, 1, NOW()),
  (2, 1, 'paypal', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 1, NOW());
