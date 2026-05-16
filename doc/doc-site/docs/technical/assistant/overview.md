---
sidebar_position: 1
title: Overview
---

# AI Assistant (Aura)

🔒 **Restricted**: Developer documentation

Aura's AI Assistant provides natural language querying of attendance data using LLM integration with MCP tools.

## Overview

The AI Assistant service is a streaming LLM-powered chatbot that can:
- Answer questions about attendance data
- Query live database information
- Generate attendance reports
- Provide system insights
- Assist with data analysis

**Tech Stack**:
- **Framework**: FastAPI (Python 3.11+)
- **LLM Providers**: OpenAI GPT-4, Google Gemini
- **Tool Protocol**: MCP (Model Context Protocol)
- **Streaming**: Server-Sent Events (SSE)
- **Database**: PostgreSQL (via MCP tools)

## Architecture

```
User Query → FastAPI Endpoint → LLM Provider → MCP Tools → Database
                                      ↓
                                 Streaming Response
```

### Components

1. **API Layer** (`assistant/routers/`)
   - Chat endpoints
   - Streaming response handlers
   - Session management

2. **LLM Integration** (`assistant/lib/llm/`)
   - OpenAI client
   - Gemini client
   - Provider abstraction

3. **MCP Tools** (`assistant/lib/mcp/`)
   - Tool registration
   - Database query tools
   - Attendance analytics tools
   - Report generation tools

4. **Streaming** (`assistant/lib/streaming/`)
   - SSE implementation
   - Token streaming
   - Error handling

## Quick Start

### Installation

```bash
cd assistant
pip install -r requirements.txt
```

### Configuration

Create `.env` file:

```bash
# LLM Provider
LLM_PROVIDER=openai  # or gemini
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Database Connection
DATABASE_URL=postgresql://user:pass@localhost:5432/aura

# Server
HOST=0.0.0.0
PORT=8500
```

### Run Server

```bash
# Development
uvicorn main:app --reload --port 8500

# Production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8500
```

## API Endpoints

### POST /api/chat

Send a message to the assistant.

**Request**:
```json
{
  "message": "How many students attended today's assembly?",
  "session_id": "optional-session-id",
  "context": {
    "user_id": 123,
    "school_id": 1
  }
}
```

**Response** (Streaming SSE):
```
data: {"type": "token", "content": "Based"}
data: {"type": "token", "content": " on"}
data: {"type": "token", "content": " the"}
data: {"type": "token", "content": " data"}
data: {"type": "tool_call", "tool": "query_attendance", "args": {...}}
data: {"type": "tool_result", "result": {...}}
data: {"type": "token", "content": ", 245"}
data: {"type": "token", "content": " students"}
data: {"type": "done"}
```

### GET /api/chat/history

Get chat history for a session.

**Query Parameters**:
- `session_id` (required): Session identifier
- `limit` (optional): Number of messages (default: 50)

**Response**:
```json
{
  "session_id": "abc123",
  "messages": [
    {
      "role": "user",
      "content": "How many students attended?",
      "timestamp": "2024-01-15T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "245 students attended today's assembly.",
      "timestamp": "2024-01-15T10:00:05Z"
    }
  ]
}
```

### DELETE /api/chat/session/\{session_id\}

Clear chat history for a session.

**Response**:
```json
{
  "success": true,
  "message": "Session cleared"
}
```

## Usage Examples

### Basic Query

```python
import requests

response = requests.post(
    'http://localhost:8500/api/chat',
    json={
        'message': 'What is the attendance rate for Computer Science students this week?',
        'context': {
            'user_id': 123,
            'school_id': 1
        }
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8').replace('data: ', ''))
        if data['type'] == 'token':
            print(data['content'], end='', flush=True)
```

### Frontend Integration (React)

```javascript
import { useState } from 'react';

function ChatAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    setLoading(true);
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    const response = await fetch('http://localhost:8500/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: input,
        context: { user_id: 123, school_id: 1 }
      })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let assistantMessage = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'token') {
            assistantMessage += data.content;
            setMessages(prev => {
              const newMessages = [...prev];
              const lastMessage = newMessages[newMessages.length - 1];
              if (lastMessage?.role === 'assistant') {
                lastMessage.content = assistantMessage;
              } else {
                newMessages.push({ role: 'assistant', content: assistantMessage });
              }
              return newMessages;
            });
          }
        }
      }
    }

    setLoading(false);
  };

  return (
    <div>
      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role}>
            {msg.content}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
        disabled={loading}
      />
      <button onClick={sendMessage} disabled={loading}>
        Send
      </button>
    </div>
  );
}
```

## Available Queries

### Attendance Queries

- "How many students attended [event name]?"
- "What is the attendance rate for [program/section]?"
- "Who missed the most events this month?"
- "Show me attendance trends for the past week"

### Student Queries

- "How many students are in [program]?"
- "List students with perfect attendance"
- "Who has the lowest attendance rate?"

### Event Queries

- "What events are scheduled for tomorrow?"
- "How many events were held this month?"
- "Which event had the highest attendance?"

### Analytics Queries

- "Generate an attendance report for [date range]"
- "Compare attendance between [program A] and [program B]"
- "What are the peak attendance hours?"

## MCP Tools

The assistant has access to these tools:

### query_attendance
Query attendance records with filters.

**Parameters**:
- `event_id` (optional): Filter by event
- `user_id` (optional): Filter by user
- `date_from` (optional): Start date
- `date_to` (optional): End date
- `status` (optional): Attendance status

### get_attendance_stats
Get attendance statistics.

**Parameters**:
- `school_id`: School identifier
- `program_id` (optional): Filter by program
- `date_range`: Time period

### list_events
List events with filters.

**Parameters**:
- `school_id`: School identifier
- `date_from` (optional): Start date
- `date_to` (optional): End date
- `status` (optional): Event status

### get_student_info
Get student information.

**Parameters**:
- `user_id`: Student identifier

### generate_report
Generate attendance report.

**Parameters**:
- `report_type`: Type of report
- `filters`: Report filters
- `format`: Output format (json, csv, pdf)

See [MCP Integration](./mcp-integration) for detailed tool documentation.

## Configuration

### Environment Variables

```bash
# [BEHAVIOR] LLM Provider
LLM_PROVIDER=openai  # openai or gemini

# [IDENTITY] API Keys
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# [BEHAVIOR] Model Selection
OPENAI_MODEL=gpt-4-turbo-preview
GEMINI_MODEL=gemini-pro

# [BEHAVIOR] Streaming
STREAM_ENABLED=true
STREAM_CHUNK_SIZE=1024

# [NEIGHBOR] Database
DATABASE_URL=postgresql://user:pass@localhost:5432/aura

# [ENDPOINT] Server
HOST=0.0.0.0
PORT=8500

# [BEHAVIOR] Rate Limiting
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=100

# [BEHAVIOR] Session
SESSION_TIMEOUT_MINUTES=30
MAX_HISTORY_MESSAGES=50
```

### Model Configuration

```python
# assistant/lib/app_settings.py

class Settings:
    # LLM Settings
    llm_provider: str = "openai"
    openai_model: str = "gpt-4-turbo-preview"
    gemini_model: str = "gemini-pro"
    
    # Streaming
    stream_enabled: bool = True
    stream_chunk_size: int = 1024
    
    # Context
    max_context_tokens: int = 8000
    max_response_tokens: int = 2000
    
    # Tools
    enable_mcp_tools: bool = True
    tool_timeout_seconds: int = 30
```

## Security

### Authentication

All requests require valid JWT token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  -X POST http://localhost:8500/api/chat \
  -d '{"message": "How many students attended?"}'
```

### Authorization

- Users can only query data for their school
- Students see only their own data
- Admins see all data
- Tool access controlled by user role

### Data Privacy

- Chat history stored per session
- Sessions expire after 30 minutes of inactivity
- No PII logged in assistant responses
- Database queries scoped to user permissions

## Monitoring

### Metrics

```python
# Track assistant usage
from prometheus_client import Counter, Histogram

chat_requests = Counter('assistant_chat_requests_total', 'Total chat requests')
chat_duration = Histogram('assistant_chat_duration_seconds', 'Chat response time')
tool_calls = Counter('assistant_tool_calls_total', 'Total MCP tool calls', ['tool_name'])
```

### Logging

```python
import logging

logger = logging.getLogger('assistant')
logger.info(f"Chat request from user {user_id}: {message}")
logger.info(f"Tool call: {tool_name} with args {args}")
logger.info(f"Response generated in {duration}s")
```

## Testing

### Unit Tests

```python
import pytest
from assistant.lib.llm import OpenAIClient

@pytest.mark.asyncio
async def test_chat_completion():
    client = OpenAIClient(api_key="test-key")
    response = await client.chat_completion(
        messages=[{"role": "user", "content": "Hello"}],
        stream=False
    )
    assert response.content
    assert response.role == "assistant"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_mcp_tool_execution():
    from assistant.lib.mcp import query_attendance
    
    result = await query_attendance(
        event_id=123,
        date_from="2024-01-01",
        date_to="2024-01-31"
    )
    assert isinstance(result, list)
    assert len(result) > 0
```

## Troubleshooting

### Common Issues

**Issue**: Slow responses
**Solution**: 
- Check LLM API latency
- Optimize MCP tool queries
- Enable response caching

**Issue**: Tool execution fails
**Solution**:
- Verify database connection
- Check tool permissions
- Review tool parameters

**Issue**: Streaming breaks
**Solution**:
- Check network stability
- Verify SSE client implementation
- Review server logs

## Performance

### Optimization Tips

1. **Caching**: Cache frequent queries
2. **Connection Pooling**: Reuse database connections
3. **Async Operations**: Use async/await for I/O
4. **Rate Limiting**: Prevent abuse
5. **Token Management**: Optimize context window usage

### Benchmarks

- Average response time: 2-5 seconds
- Streaming latency: < 100ms per token
- Tool execution: 100-500ms
- Concurrent users: 100+

## Related Documentation

- [MCP Integration](./mcp-integration) - Tool development guide
- [API Reference](../api/overview) - REST API docs
- [Backend Architecture](../backend/architecture) - System design

## Need Help?

- Check [MCP Integration](./mcp-integration) for tool issues
- See [API Reference](../api/overview) for endpoint details
- Contact AI team for LLM provider issues

---

**Note**: The AI Assistant is powered by external LLM providers. Ensure API keys are properly configured and rate limits are monitored.
