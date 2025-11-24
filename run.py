import sys
import os

# Add the parent directory to sys.path to allow importing 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        from app.extensions import db
        db.create_all()
        print("Database tables created.")
    
    socketio.run(app, debug=True, port=5001)
