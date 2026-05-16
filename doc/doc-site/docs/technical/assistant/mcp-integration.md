---
sidebar_position: 2
title: MCP Integration
---

# MCP Integration

🔒 **Restricted**: Developer documentation

Model Context Protocol (MCP) integration for AI Assistant tool system.

## Overview

MCP (Model Context Protocol) enables the AI Assistant to interact with live data through a standardized tool interface.

**Key Features**:
- Tool registration and discovery
- Type-safe parameter validation
- Async execution
- Error handling
- Permission-based access control

## Architecture

```
LLM → Tool Call → MCP Router → Tool Handler → Database/Service
                                      ↓
                                Tool Result → LLM
```

## Tool Structure

### Tool Definition

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class QueryAttendanceTool(BaseModel):
    """Query attendance records with filters"""
    
    name: str = "query_attendance"
    description: str = "Query attendance records for events, users, or date ranges"
    
    class Parameters(BaseModel):
        event_id: Optional[int] = Field(None, description="Filter by event ID")
        user_id: Optional[int] = Field(None, description="Filter by user ID")
        date_from: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
        date_to: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
        status: Optional[str] = Field(None, description="Attendance status filter")
        limit: int = Field(100, description="Maximum results to return")
    
    async def execute(self, params: Parameters, context: dict) -> dict:
        """Execute the tool with given parameters"""
        # Implementation
        pass
```

### Tool Registration

```python
# assistant/lib/mcp/registry.py

from typing import Dict, Type
from .tools import QueryAttendanceTool, GetAttendanceStatsTool

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
    
    def register(self, tool: Type[BaseTool]):
        """Register a tool"""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Type[BaseTool]:
        """Get tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[dict]:
        """List all registered tools"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.Parameters.schema()
            }
            for tool in self._tools.values()
        ]

# Global registry
registry = ToolRegistry()

# Register tools
registry.register(QueryAttendanceTool)
registry.register(GetAttendanceStatsTool)
registry.register(ListEventsTool)
registry.register(GetStudentInfoTool)
registry.register(GenerateReportTool)
```

## Available Tools

### 1. query_attendance

Query attendance records with flexible filters.

**Parameters**:
```json
{
  "event_id": 123,
  "user_id": 456,
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "status": "present",
  "limit": 100
}
```

**Returns**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "event_id": 123,
      "user_id": 456,
      "status": "present",
      "check_in_time": "2024-01-15T09:05:00Z",
      "method": "face_scan"
    }
  ],
  "count": 1
}
```

**Implementation**:
```python
async def execute(self, params: Parameters, context: dict) -> dict:
    from app.db.session import get_db
    from app.models import AttendanceRecord
    
    async with get_db() as db:
        query = db.query(AttendanceRecord)
        
        # Apply filters
        if params.event_id:
            query = query.filter(AttendanceRecord.event_id == params.event_id)
        if params.user_id:
            query = query.filter(AttendanceRecord.user_id == params.user_id)
        if params.date_from:
            query = query.filter(AttendanceRecord.check_in_time >= params.date_from)
        if params.date_to:
            query = query.filter(AttendanceRecord.check_in_time <= params.date_to)
        if params.status:
            query = query.filter(AttendanceRecord.status == params.status)
        
        # Apply school scope from context
        school_id = context.get('school_id')
        query = query.join(Event).filter(Event.school_id == school_id)
        
        # Execute query
        records = query.limit(params.limit).all()
        
        return {
            "success": True,
            "data": [record.to_dict() for record in records],
            "count": len(records)
        }
```

### 2. get_attendance_stats

Get aggregated attendance statistics.

**Parameters**:
```json
{
  "school_id": 1,
  "program_id": 5,
  "date_range": "last_30_days"
}
```

**Returns**:
```json
{
  "success": true,
  "stats": {
    "total_events": 25,
    "total_attendees": 1250,
    "average_attendance_rate": 85.5,
    "present_count": 1068,
    "late_count": 182,
    "absent_count": 200,
    "excused_count": 50
  }
}
```

### 3. list_events

List events with filters.

**Parameters**:
```json
{
  "school_id": 1,
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "status": "published",
  "limit": 50
}
```

**Returns**:
```json
{
  "success": true,
  "events": [
    {
      "id": 123,
      "name": "Campus Assembly",
      "start_time": "2024-01-15T09:00:00Z",
      "end_time": "2024-01-15T11:00:00Z",
      "location": "Main Auditorium",
      "attendance_count": 245
    }
  ]
}
```

### 4. get_student_info

Get detailed student information.

**Parameters**:
```json
{
  "user_id": 456
}
```

**Returns**:
```json
{
  "success": true,
  "student": {
    "id": 456,
    "username": "john.doe",
    "full_name": "John Doe",
    "student_id": "2024-12345",
    "program": "Computer Science",
    "section": "CS-3A",
    "attendance_rate": 92.5,
    "total_events_attended": 37,
    "total_events_missed": 3
  }
}
```

### 5. generate_report

Generate attendance reports.

**Parameters**:
```json
{
  "report_type": "attendance_summary",
  "filters": {
    "program_id": 5,
    "date_from": "2024-01-01",
    "date_to": "2024-01-31"
  },
  "format": "json"
}
```

**Returns**:
```json
{
  "success": true,
  "report": {
    "title": "Attendance Summary Report",
    "period": "January 2024",
    "program": "Computer Science",
    "summary": {
      "total_students": 150,
      "average_attendance": 88.5,
      "perfect_attendance": 45,
      "at_risk_students": 12
    },
    "details": [...]
  }
}
```

## Creating Custom Tools

### Step 1: Define Tool Class

```python
# assistant/lib/mcp/tools/custom_tool.py

from pydantic import BaseModel, Field
from typing import Optional
from .base import BaseTool

class MyCustomTool(BaseTool):
    """Description of what this tool does"""
    
    name: str = "my_custom_tool"
    description: str = "Detailed description for the LLM"
    
    class Parameters(BaseModel):
        param1: str = Field(..., description="Required parameter")
        param2: Optional[int] = Field(None, description="Optional parameter")
    
    async def execute(self, params: Parameters, context: dict) -> dict:
        """
        Execute the tool logic
        
        Args:
            params: Validated parameters
            context: User context (user_id, school_id, role, etc.)
        
        Returns:
            dict: Tool result
        """
        # Your implementation here
        result = await some_async_operation(params.param1, params.param2)
        
        return {
            "success": True,
            "data": result
        }
```

### Step 2: Register Tool

```python
# assistant/lib/mcp/registry.py

from .tools.custom_tool import MyCustomTool

registry.register(MyCustomTool)
```

### Step 3: Test Tool

```python
# tests/test_custom_tool.py

import pytest
from assistant.lib.mcp.tools.custom_tool import MyCustomTool

@pytest.mark.asyncio
async def test_custom_tool():
    tool = MyCustomTool()
    params = MyCustomTool.Parameters(param1="test", param2=42)
    context = {"user_id": 123, "school_id": 1}
    
    result = await tool.execute(params, context)
    
    assert result["success"] is True
    assert "data" in result
```

## Tool Execution Flow

### 1. LLM Requests Tool

```json
{
  "tool_call": {
    "name": "query_attendance",
    "arguments": {
      "event_id": 123,
      "status": "present"
    }
  }
}
```

### 2. MCP Router Validates

```python
# assistant/lib/mcp/router.py

async def execute_tool(tool_name: str, arguments: dict, context: dict) -> dict:
    # Get tool from registry
    tool_class = registry.get(tool_name)
    if not tool_class:
        return {"error": f"Tool {tool_name} not found"}
    
    # Validate parameters
    try:
        params = tool_class.Parameters(**arguments)
    except ValidationError as e:
        return {"error": f"Invalid parameters: {e}"}
    
    # Check permissions
    if not has_permission(context['role'], tool_name):
        return {"error": "Permission denied"}
    
    # Execute tool
    tool = tool_class()
    result = await tool.execute(params, context)
    
    return result
```

### 3. Tool Executes

```python
async def execute(self, params: Parameters, context: dict) -> dict:
    # Access database
    # Perform calculations
    # Return results
    return {"success": True, "data": ...}
```

### 4. Result Returned to LLM

```json
{
  "tool_result": {
    "success": true,
    "data": [...]
  }
}
```

## Permission System

### Role-Based Access

```python
# assistant/lib/mcp/permissions.py

TOOL_PERMISSIONS = {
    "query_attendance": ["admin", "campus_admin", "school_it", "ssg", "sg", "org"],
    "get_attendance_stats": ["admin", "campus_admin", "school_it", "ssg", "sg", "org"],
    "list_events": ["admin", "campus_admin", "school_it", "ssg", "sg", "org", "student"],
    "get_student_info": ["admin", "campus_admin", "school_it"],
    "generate_report": ["admin", "campus_admin", "school_it", "ssg", "sg", "org"],
}

def has_permission(role: str, tool_name: str) -> bool:
    """Check if role has permission to use tool"""
    allowed_roles = TOOL_PERMISSIONS.get(tool_name, [])
    return role in allowed_roles
```

### Data Scoping

```python
async def execute(self, params: Parameters, context: dict) -> dict:
    # Students can only see their own data
    if context['role'] == 'student':
        params.user_id = context['user_id']
    
    # Scope to user's school
    school_id = context['school_id']
    
    # Execute query with scope
    results = await query_with_scope(params, school_id)
    
    return {"success": True, "data": results}
```

## Error Handling

### Tool Errors

```python
class ToolExecutionError(Exception):
    """Raised when tool execution fails"""
    pass

async def execute(self, params: Parameters, context: dict) -> dict:
    try:
        result = await perform_operation(params)
        return {"success": True, "data": result}
    except DatabaseError as e:
        logger.error(f"Database error in tool: {e}")
        return {"success": False, "error": "Database query failed"}
    except PermissionError as e:
        logger.warning(f"Permission denied: {e}")
        return {"success": False, "error": "Permission denied"}
    except Exception as e:
        logger.exception(f"Unexpected error in tool: {e}")
        return {"success": False, "error": "Internal error"}
```

### Timeout Handling

```python
import asyncio

async def execute_with_timeout(tool, params, context, timeout=30):
    """Execute tool with timeout"""
    try:
        result = await asyncio.wait_for(
            tool.execute(params, context),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        return {"success": False, "error": "Tool execution timeout"}
```

## Testing

### Unit Tests

```python
@pytest.mark.asyncio
async def test_query_attendance_tool():
    tool = QueryAttendanceTool()
    params = QueryAttendanceTool.Parameters(
        event_id=123,
        status="present"
    )
    context = {"user_id": 1, "school_id": 1, "role": "admin"}
    
    result = await tool.execute(params, context)
    
    assert result["success"] is True
    assert isinstance(result["data"], list)
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_tool_execution_flow():
    from assistant.lib.mcp.router import execute_tool
    
    result = await execute_tool(
        tool_name="query_attendance",
        arguments={"event_id": 123},
        context={"user_id": 1, "school_id": 1, "role": "admin"}
    )
    
    assert result["success"] is True
```

## Best Practices

### 1. Clear Descriptions

```python
class MyTool(BaseTool):
    description: str = """
    Query attendance records for specific events or users.
    Use this tool when the user asks about attendance data,
    check-in records, or event participation.
    """
```

### 2. Validate Inputs

```python
class Parameters(BaseModel):
    date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    limit: int = Field(100, ge=1, le=1000)
```

### 3. Handle Errors Gracefully

```python
async def execute(self, params, context):
    try:
        result = await operation()
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return {"success": False, "error": str(e)}
```

### 4. Scope Data Properly

```python
# Always scope to user's school
query = query.filter(Event.school_id == context['school_id'])

# Restrict student data access
if context['role'] == 'student':
    query = query.filter(User.id == context['user_id'])
```

### 5. Log Tool Usage

```python
logger.info(f"Tool {self.name} called by user {context['user_id']}")
logger.debug(f"Parameters: {params.dict()}")
```

## Monitoring

### Metrics

```python
from prometheus_client import Counter, Histogram

tool_calls = Counter('mcp_tool_calls_total', 'Total tool calls', ['tool_name', 'status'])
tool_duration = Histogram('mcp_tool_duration_seconds', 'Tool execution time', ['tool_name'])

async def execute(self, params, context):
    with tool_duration.labels(tool_name=self.name).time():
        try:
            result = await operation()
            tool_calls.labels(tool_name=self.name, status='success').inc()
            return result
        except Exception as e:
            tool_calls.labels(tool_name=self.name, status='error').inc()
            raise
```

## Related Documentation

- [AI Assistant Overview](./overview) - Assistant architecture
- [API Reference](../api/overview) - REST API docs
- [Backend Services](../backend/services) - Service layer

## Need Help?

- Check [AI Assistant Overview](./overview) for general info
- See [Backend Architecture](../backend/architecture) for database access
- Contact AI team for tool development support

---

**Note**: MCP tools have direct database access. Always validate inputs and scope queries properly to prevent data leaks.
