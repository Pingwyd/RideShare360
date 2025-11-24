from . import socketio
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from .extensions import db
from .models.models import Message, User

@socketio.on('join')
def on_join(data):
    room = data.get('room')
    join_room(room)
    emit('status', {'msg': f'{current_user.name} has joined the chat.'}, room=room)

@socketio.on('message')
def on_message(data):
    room = data.get('room')
    msg_content = data.get('msg')
    
    if current_user.is_authenticated:
        # Save message to DB
        new_message = Message(
            ride_id=int(room),
            sender_id=current_user.id,
            message=msg_content
        )
        db.session.add(new_message)
        db.session.commit()
        
        emit('message', {
            'msg': msg_content, 
            'sender': current_user.name,
            'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }, room=room)

