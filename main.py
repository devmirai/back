from flask import Flask, request
from flask_cors import CORS
from config import Config
from app.models import db
from app.routes.auth import auth_bp
from app.routes.users import users_bp
from app.routes.events import events_bp
from app.routes.tickets import tickets_bp
from app.routes.company import company_bp
from app.routes.payment_methods import payment_methods_bp
from app.middleware import init_limiter
from app.utils.auth import init_jwt

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # ✅ Inicializar base de datos
    db.init_app(app)
    
    # ✅ CORS optimizado para desarrollo
    CORS(app,
         resources={r"/*": {"origins": ["http://localhost:5173"]}},  # Origen explícito
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    
    # ✅ JWT y Limiter
    init_jwt(app)
    init_limiter(app)
    
    print(f"🔧 Configuración de base de datos: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # ✅ Registrar Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(payment_methods_bp)

    # ✅ Rutas simples de prueba
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return {'status': 'OK', 'message': 'API is running'}, 200

    @app.route('/api/version', methods=['GET'])
    def version():
        return {'version': '1.0.0', 'build': 'MVP'}, 200

    @app.route('/api/init-db', methods=['POST'])
    def init_database():
        try:
            db.create_all()
            print("✅ Base de datos inicializada exitosamente")
            return {'message': 'Database initialized successfully'}, 200
        except Exception as e:
            return {'error': 'Failed to initialize database', 'details': str(e)}, 500

    # ✅ 🔥 Solución rápida para CORS en desarrollo
    @app.before_request
    def handle_options():
        """Permitir que cualquier preflight OPTIONS pase en desarrollo"""
        if request.method == "OPTIONS":
            return "", 200

    return app

# ✅ Ejecutar en desarrollo
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
