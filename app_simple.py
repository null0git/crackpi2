import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    
    # Database configuration
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///crackpi.db")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register blueprints (simplified)
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    
    # Create tables
    with app.app_context():
        import models
        db.create_all()
        
        # Create default admin user if none exists
        from models import User
        from werkzeug.security import generate_password_hash
        if not User.query.filter_by(username='admin').first():
            admin_user = User()
            admin_user.username = 'admin'
            admin_user.email = 'admin@crackpi.local'
            admin_user.password_hash = generate_password_hash('admin123')
            admin_user.is_admin = True
            db.session.add(admin_user)
            db.session.commit()
            app.logger.info("Created default admin user: admin/admin123")
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))
    
    return app

app = create_app()