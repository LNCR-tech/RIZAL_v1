import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from openai import AsyncOpenAI

import sys
from pathlib import Path

# Ensure lib/ is in path
LIB_DIR = str(Path(__file__).resolve().parent / "lib")
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from database import engine, SessionLocal, get_db
from auth import get_current_identity, get_roles_from_identity, get_primary_role
from mcp_client import MultiMCPClient
from policy import get_effective_policy

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("assistant-v2")

app = FastAPI(title="Aura Assistant v2 (MCP-Native)")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI Setup
client = AsyncOpenAI(api_key=os.getenv("AI_API_KEY"))
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

# MCP Client
mcp_client = MultiMCPClient()

@app.get("/health")
async def health():
    return {"status": "ok", "version": "v2-mcp"}

@app.post("/chat")
async def chat(
    request: Request,
    db: Session = Depends(get_db),
    identity: Dict[str, Any] = Depends(get_current_identity)
):
    body = await request.json()
    user_message = body.get("message")
    user_id = identity.get("user_id") or identity.get("sub")
    school_id = body.get("user_school_id")
    
    roles = get_roles_from_identity(identity)
    primary_role = get_primary_role(roles)
    
    # 1. Get available MCP tools
    mcp_tools = await mcp_client.get_all_tools()
    
    # 2. Build AI Tool definitions
    ai_tools = []
    for t in mcp_tools:
        ai_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["inputSchema"]
            }
        })

    messages = [
        {"role": "system", "content": f"You are Aura, an AI assistant. Your role is {primary_role}. You have access to tools via MCP."},
        {"role": "user", "content": user_message}
    ]

    async def event_generator():
        try:
            # Initial AI Call
            response = await client.chat.completions.create(
                model=AI_MODEL,
                messages=messages,
                tools=ai_tools if ai_tools else None,
                stream=True
            )

            full_content = ""
            tool_calls = []

            async for chunk in response:
                delta = chunk.choices[0].delta
                
                # Handle Content
                if delta.content:
                    full_content += delta.content
                    yield f"data: {json.dumps({'content': delta.content})}\n\n"
                
                # Handle Tool Calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if len(tool_calls) <= tc.index:
                            tool_calls.append({"id": "", "name": "", "args": ""})
                        
                        curr = tool_calls[tc.index]
                        if tc.id: curr["id"] = tc.id
                        if tc.function.name: curr["name"] = tc.function.name
                        if tc.function.arguments: curr["args"] += tc.function.arguments

            # Process Tool Calls if any
            if tool_calls:
                for tc in tool_calls:
                    yield f"data: {json.dumps({'status': f'Calling tool: {tc['name']}...'})}\n\n"
                    
                    # Find which server owns this tool
                    tool_meta = next((t for t in mcp_tools if t["name"] == tc["name"]), None)
                    if tool_meta:
                        server = tool_meta["server"]
                        args = json.loads(tc["args"])
                        
                        # Injection of auth context into MCP tools
                        args["roles"] = roles
                        args["user_id"] = str(user_id)
                        args["school_id"] = school_id
                        
                        tool_result = await mcp_client.call_tool(server, tc["name"], args)
                        
                        # Logic to feed result back to AI would go here for multi-turn...
                        # For now, we return the data to the user as a "Report"
                        yield f"data: {json.dumps({'tool_result': tool_result.content})}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("ASSISTANT_PORT", 8500))
    uvicorn.run(app, host="127.0.0.1", port=port)
