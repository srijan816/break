from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app(config_name='default'):
    """Application factory pattern"""
    from config import get_config
    
    app = Flask(__name__)
    app.config.from_object(get_config())
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # Configure CORS
    CORS(app, 
         origins=app.config['CORS_ORIGINS'],
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'])
    
    # Register blueprints
    from app.auth import auth_bp
    from app.breaks import breaks_bp
    from app.calendar import calendar_bp
    from app.users import users_bp
    from app.recommendations import recommendations_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(breaks_bp, url_prefix='/api/v1/breaks')
    app.register_blueprint(calendar_bp, url_prefix='/api/v1/calendar')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(recommendations_bp, url_prefix='/api/v1/recommendations')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'takeabreak-api'}, 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app