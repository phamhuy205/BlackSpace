import os, json
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_login import LoginManager
from dotenv import load_dotenv
from app.logging import setup_logging
# removed top-level import to avoid circular import

            

db = SQLAlchemy()
bcrypt = Bcrypt()
socketio = SocketIO(async_mode="threading")
login_manager = LoginManager()

client = None

def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///users.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Load secret key from env
    secret = os.getenv("SECRET_KEY")
    if not secret:
        # keep a fallback but warn loudly
        app.secret_key = os.urandom(24)
    else:
        app.secret_key = secret

    # Setup logging early
    setup_logging(app)

    db.init_app(app)
    bcrypt.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # nếu người dùng chưa đăng nhập, chuyển hướng đến trang đăng nhập

    # Load models (do NOT create_all on startup; use migrations in production)
    from app.models import User, Comment

    # Load routes
    from app.routes.main import bp as main_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.profile import bp as profile_bp
    from app.routes.ai import bp as ai_bp
    from app.routes.admin import bp as admin_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(admin_bp)

    # Basic error handlers
    @app.errorhandler(404)
    def not_found(e):
        app.logger.info('404 Not Found: %s', request.path)
        return "404 Not Found", 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception('Server Error')
        return "500 Internal Server Error", 500

    return app


