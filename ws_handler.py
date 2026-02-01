from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
from datetime import datetime

router = APIRouter()

# Active connections
active_connections: Dict[int, WebSocket] = {}
online_users: Set[int] = set()


async def notify_user_status(user_id: int, is_online: bool):
    """Notify all connections about user status change."""
    message = json.dumps({
        "type": "status_change",
        "user_id": user_id,
        "is_online": is_online
    })
    
    for connection in active_connections.values():
        try:
            await connection.send_text(message)
        except Exception:
            pass


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    """WebSocket endpoint for real-time messaging."""
    await websocket.accept()
    active_connections[user_id] = websocket
    online_users.add(user_id)
    
    # Notify others that user is online
    await notify_user_status(user_id, True)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            msg_type = message.get("type")
            
            if msg_type == "message":
                # Forward message to recipient
                recipient_id = message.get("recipient_id")
                if recipient_id in active_connections:
                    await active_connections[recipient_id].send_text(json.dumps({
                        "type": "new_message",
                        "chat_id": message.get("chat_id"),
                        "sender_id": user_id,
                        "content": message.get("content"),
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
            elif msg_type == "typing":
                # Send typing indicator
                recipient_id = message.get("recipient_id")
                if recipient_id in active_connections:
                    await active_connections[recipient_id].send_text(json.dumps({
                        "type": "typing",
                        "user_id": user_id
                    }))
            
            elif msg_type == "read":
                # Mark messages as read
                chat_id = message.get("chat_id")
                # In a real app, update database here
                await websocket.send_text(json.dumps({
                    "type": "read_receipt",
                    "chat_id": chat_id,
                    "user_id": user_id
                }))
    
    except WebSocketDisconnect:
        # Remove connection
        if user_id in active_connections:
            del active_connections[user_id]
        online_users.discard(user_id)
        
        # Notify others that user is offline
        await notify_user_status(user_id, False)


@router.get("/online")
async def get_online_users():
    """Get list of online users."""
    return {"online_users": list(online_users)}
