from flask_socketio import join_room, emit
from app import socketio

@socketio.on("join_room")
def handle_join(data):
    join_room(data["room"])
    emit("message", f"{data['user']} đã tham gia phòng {data['room']}", room=data["room"])

@socketio.on("sync_video")
def handle_sync(data):
    emit("sync_video", data, room=data["room"], include_self=False)
