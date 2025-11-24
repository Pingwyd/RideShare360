from flask import Flask
from flask_socketio import SocketIO
from .extensions import db, login_manager

socketio = SocketIO(cors_allowed_origins='*', async_mode='eventlet')

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Import config from the same package
    from .config import Config
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)
    
    from .views import main_bp
    from .auth import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Import socketio handlers to register events
    from . import socketio_handlers
    
    return app
