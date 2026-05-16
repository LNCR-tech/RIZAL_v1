---
sidebar_position: 4
title: WebSockets
---

# WebSockets API

🔒 **Restricted**: Developer documentation

Real-time communication for live attendance updates and notifications.

## Overview

Aura uses WebSockets for:
- Real-time attendance updates
- Live event monitoring
- Push notifications
- System status updates

**Protocol**: WebSocket (ws:// or wss://)  
**Library**: Socket.IO (backend), Socket.IO Client (frontend)

## Connection

### Endpoint

```
Development: ws://localhost:8001/ws
Production: wss://api.aura.school/ws
```

### Authentication

WebSocket connections require JWT token:

```javascript
import io from 'socket.io-client';

const socket = io('ws://localhost:8001', {
  auth: {
    token: 'YOUR_JWT_TOKEN'
  },
  transports: ['websocket']
});
```

### Connection Events

```javascript
// Connection established
socket.on('connect', () => {
  console.log('Connected:', socket.id);
});

// Connection error
socket.on('connect_error', (error) => {
  console.error('Connection failed:', error);
});

// Disconnected
socket.on('disconnect', (reason) => {
  console.log('Disconnected:', reason);
});

// Reconnection attempt
socket.on('reconnect_attempt', (attemptNumber) => {
  console.log('Reconnecting...', attemptNumber);
});
```

## Events

### Subscribe to Events

#### Attendance Updates

```javascript
// Subscribe to event attendance
socket.emit('subscribe:event', { event_id: 123 });

// Listen for check-ins
socket.on('attendance:checkin', (data) => {
  console.log('New check-in:', data);
  // {
  //   event_id: 123,
  //   user_id: 456,
  //   username: "john.doe",
  //   timestamp: "2024-01-15T10:30:00Z",
  //   status: "present",
  //   method: "face_scan"
  // }
});

// Unsubscribe
socket.emit('unsubscribe:event', { event_id: 123 });
```

#### Notifications

```javascript
// Listen for notifications
socket.on('notification', (data) => {
  console.log('New notification:', data);
  // {
  //   id: 789,
  //   type: "event_reminder",
  //   title: "Event Tomorrow",
  //   message: "Campus Assembly starts at 9 AM",
  //   timestamp: "2024-01-15T10:00:00Z"
  // }
});
```

#### System Status

```javascript
// Listen for system updates
socket.on('system:status', (data) => {
  console.log('System status:', data);
  // {
  //   status: "operational",
  //   message: "All systems running normally"
  // }
});

// Maintenance alerts
socket.on('system:maintenance', (data) => {
  console.log('Maintenance scheduled:', data);
  // {
  //   start_time: "2024-01-20T02:00:00Z",
  //   duration_minutes: 30,
  //   message: "Scheduled maintenance"
  // }
});
```

### Emit Events

#### Join Room

```javascript
// Join event room for updates
socket.emit('join:event', { event_id: 123 });

// Join user room for personal notifications
socket.emit('join:user', { user_id: 456 });

// Leave room
socket.emit('leave:event', { event_id: 123 });
```

#### Send Message

```javascript
// Send custom message (admin only)
socket.emit('broadcast:message', {
  room: 'event:123',
  message: 'Event starting in 5 minutes'
});
```

## Rooms

### Room Naming Convention

- `event:{event_id}` - Event-specific updates
- `user:{user_id}` - User-specific notifications
- `school:{school_id}` - School-wide announcements
- `admin` - Admin-only channel

### Joining Rooms

```javascript
// Automatic room joining based on role
socket.on('connect', () => {
  // User automatically joins their user room
  // Admins automatically join admin room
  // Event managers join their event rooms
});
```

## Error Handling

### Error Events

```javascript
socket.on('error', (error) => {
  console.error('Socket error:', error);
  // {
  //   code: "AUTH_FAILED",
  //   message: "Invalid token"
  // }
});
```

### Common Errors

| Error Code | Description | Solution |
|------------|-------------|----------|
| `AUTH_FAILED` | Invalid or expired token | Refresh JWT token |
| `ROOM_NOT_FOUND` | Room doesn't exist | Check room name |
| `PERMISSION_DENIED` | Insufficient permissions | Check user role |
| `RATE_LIMIT` | Too many messages | Slow down requests |

## Rate Limiting

- **Connection**: 5 connections per minute per user
- **Messages**: 100 messages per minute per connection
- **Subscriptions**: 50 room subscriptions per connection

## Example: Live Attendance Dashboard

```javascript
import { useEffect, useState } from 'react';
import io from 'socket.io-client';

function LiveAttendanceDashboard({ eventId, token }) {
  const [attendees, setAttendees] = useState([]);
  const [socket, setSocket] = useState(null);

  useEffect(() => {
    // Connect to WebSocket
    const newSocket = io('ws://localhost:8001', {
      auth: { token },
      transports: ['websocket']
    });

    newSocket.on('connect', () => {
      console.log('Connected');
      // Subscribe to event updates
      newSocket.emit('subscribe:event', { event_id: eventId });
    });

    newSocket.on('attendance:checkin', (data) => {
      // Add new attendee to list
      setAttendees(prev => [...prev, data]);
    });

    newSocket.on('error', (error) => {
      console.error('Socket error:', error);
    });

    setSocket(newSocket);

    // Cleanup
    return () => {
      newSocket.emit('unsubscribe:event', { event_id: eventId });
      newSocket.disconnect();
    };
  }, [eventId, token]);

  return (
    <div>
      <h2>Live Attendance ({attendees.length})</h2>
      <ul>
        {attendees.map((attendee, index) => (
          <li key={index}>
            {attendee.username} - {attendee.status} at {attendee.timestamp}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

## Example: Real-time Notifications

```javascript
import { useEffect } from 'react';
import io from 'socket.io-client';
import { toast } from 'react-toastify';

function useRealtimeNotifications(userId, token) {
  useEffect(() => {
    const socket = io('ws://localhost:8001', {
      auth: { token },
      transports: ['websocket']
    });

    socket.on('connect', () => {
      socket.emit('join:user', { user_id: userId });
    });

    socket.on('notification', (data) => {
      // Show toast notification
      toast.info(data.message, {
        title: data.title,
        autoClose: 5000
      });
    });

    return () => {
      socket.emit('leave:user', { user_id: userId });
      socket.disconnect();
    };
  }, [userId, token]);
}
```

## Backend Implementation

### Socket.IO Server Setup

```python
from fastapi import FastAPI
from fastapi_socketio import SocketManager

app = FastAPI()
socket_manager = SocketManager(app=app, cors_allowed_origins="*")

@socket_manager.on('connect')
async def handle_connect(sid, environ, auth):
    # Verify JWT token
    token = auth.get('token')
    user = verify_token(token)
    
    if not user:
        return False  # Reject connection
    
    # Store user session
    await socket_manager.save_session(sid, {'user_id': user.id})
    
    # Auto-join user room
    await socket_manager.enter_room(sid, f'user:{user.id}')
    
    return True

@socket_manager.on('subscribe:event')
async def handle_subscribe_event(sid, data):
    event_id = data.get('event_id')
    session = await socket_manager.get_session(sid)
    user_id = session.get('user_id')
    
    # Check permissions
    if can_view_event(user_id, event_id):
        await socket_manager.enter_room(sid, f'event:{event_id}')
        await socket_manager.emit('subscribed', {'event_id': event_id}, room=sid)
```

### Emitting Events

```python
# Emit to specific room
await socket_manager.emit(
    'attendance:checkin',
    {
        'event_id': event_id,
        'user_id': user_id,
        'username': user.username,
        'timestamp': datetime.utcnow().isoformat(),
        'status': 'present'
    },
    room=f'event:{event_id}'
)

# Emit to specific user
await socket_manager.emit(
    'notification',
    {
        'type': 'event_reminder',
        'message': 'Event starts in 1 hour'
    },
    room=f'user:{user_id}'
)

# Broadcast to all
await socket_manager.emit(
    'system:status',
    {'status': 'maintenance', 'message': 'System maintenance in progress'}
)
```

## Security

### Authentication

- All connections require valid JWT token
- Tokens verified on connection
- Invalid tokens rejected immediately

### Authorization

- Room access controlled by user role
- Event rooms require event access permission
- Admin rooms restricted to admin users

### Data Validation

- All incoming messages validated
- Malformed data rejected
- Rate limiting enforced

## Testing

### Manual Testing

```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8001/ws -H "Authorization: Bearer YOUR_TOKEN"

# Send message
> {"event": "subscribe:event", "data": {"event_id": 123}}

# Receive messages
< {"event": "attendance:checkin", "data": {...}}
```

### Automated Testing

```python
import pytest
from socketio import AsyncClient

@pytest.mark.asyncio
async def test_websocket_connection():
    client = AsyncClient()
    
    # Connect
    await client.connect('http://localhost:8001', auth={'token': 'test_token'})
    
    # Subscribe to event
    await client.emit('subscribe:event', {'event_id': 123})
    
    # Wait for response
    response = await client.receive()
    assert response['event'] == 'subscribed'
    
    # Disconnect
    await client.disconnect()
```

## Performance

### Optimization Tips

1. **Connection Pooling**: Reuse connections
2. **Room Management**: Unsubscribe from unused rooms
3. **Message Batching**: Batch multiple updates
4. **Compression**: Enable WebSocket compression

### Monitoring

```python
# Track active connections
active_connections = socket_manager.get_active_connections()

# Track room subscriptions
room_count = socket_manager.get_room_count('event:123')

# Monitor message rate
message_rate = socket_manager.get_message_rate()
```

## Related Documentation

- [API Overview](./overview) - REST API reference
- [Authentication](./authentication) - JWT token management
- [Backend Architecture](../backend/architecture) - System design

## Need Help?

- Check [API Overview](./overview) for general API info
- See [Authentication](./authentication) for token issues
- Contact backend team for WebSocket server issues

---

**Note**: WebSocket connections are stateful and require proper cleanup to avoid memory leaks.
