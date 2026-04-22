import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Generator, AsyncGenerator
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from lib.app_settings import APP_SETTINGS, get_cors_allowed_origins
from lib.database import get_db, init_db, Conversation, Message, DailyUsage, SessionLocal
from lib.auth import get_current_identity, get_token_user_id, resolve_runtime_governance_access, get_roles_from_identity
from lib.mcp_client import MultiMCPClient
from lib.policy import get_effective_policy, summarize_scope_rules, normalize_permission, normalize_role
from lib.llm import call_openai, call_llm_stream, _extract_text_content, _suggest_retry_max_tokens
from lib.tools_logic import parse_tool_arguments, sanitize_tool_args, looks_like_tool_markup, extract_function_markup, recover_tool_call_from_message

logger = logging.getLogger("uvicorn.error")

# --- Configuration (Verbatim from v1) ---
ASSISTANT_DIR = os.path.dirname(__file__)

class AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1)
    user_id: Optional[str] = Field(default=None, min_length=1)
    user_role: Optional[str] = Field(default=None, min_length=1)
    user_name: Optional[str] = None
    user_school: Optional[str] = None
    user_school_id: Optional[int] = None
    user_timezone: Optional[str] = None
    conversation_id: Optional[str] = None

class ConversationSummary(BaseModel):
    conversation_id: str
    title: Optional[str]
    last_message: Optional[str]
    updated_at: datetime

class ConversationDetail(BaseModel):
    conversation_id: str
    title: Optional[str]
    messages: List[Dict[str, Any]]

class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)

app = FastAPI(title="Aura Assistant v2 (MCP-Native)")

# CORS setup
cors_allowed = get_cors_allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MCP Client
mcp_client = MultiMCPClient()

@app.on_event("startup")
async def startup_event():
    init_db()
    # Pre-warm MCP sessions if needed
    # await mcp_client.get_all_tools()

@app.get("/health")
def health():
    return {"status": "ok", "version": "v2-mcp"}

# --- Utility Logic (Verbatim from v1) ---

def _load_system_prompt() -> str:
    prompt_path = os.path.join(ASSISTANT_DIR, "system_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "You are Aura, a professional assistant for the VALID8 system."

def _render_system_prompt(template: str, **kwargs) -> str:
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", str(value if value is not None else "Unknown"))
    
    # Handle datetime separately to match v1 behavior
    utc_now = datetime.now(timezone.utc)
    try:
        user_tz = kwargs.get("user_timezone", "UTC")
        local_now = utc_now.astimezone(ZoneInfo(user_tz))
    except (ZoneInfoNotFoundError, ValueError):
        local_now = utc_now
    
    return template.replace("{datetime}", local_now.isoformat())

def _render_role_capabilities(roles: List[str], permissions: List[str]) -> tuple[str, str, str, str, str]:
    def _summarize(values: List[str], limit: int) -> str:
        items = sorted([v for v in values if v])
        if not items: return "none"
        res = ", ".join(items[:limit])
        if len(items) > limit: res += f", ... (+{len(items)-limit} more)"
        return res

    policy = get_effective_policy(roles, permissions)
    readable = _summarize(list(policy.allowed_tables), 18)
    writable = _summarize(list(policy.allowed_write_tables), 14)
    scope = "; ".join(summarize_scope_rules(policy)[:10]) or "none"
    cap = "; ".join(list(policy.capability_notes)[:6]) or "none"
    non_cap = "; ".join(list(policy.non_capability_notes)[:6]) or "none"
    return readable, writable, scope, cap, non_cap

def _sse_event(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"

async def _summarize_title(messages: List[Dict[str, Any]]) -> Optional[str]:
    prompt = [
        {"role": "system", "content": "Summarize this conversation in 3-6 words. Return only the title."},
        {"role": "user", "content": json.dumps(messages[-4:], ensure_ascii=False)},
    ]
    result = await call_openai(prompt)
    title = _extract_text_content(result.get("content")).strip().strip('"')
    return title[:80] if title else None

async def _update_conversation_title(db: Session, conversation_id: str, messages: List[Dict[str, Any]]):
    title = await _summarize_title(messages)
    if title:
        convo = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if convo:
            convo.title = title
            db.commit()

# --- Quota Implementation (Ported from v1) ---

def _get_daily_limit(roles: List[str]) -> int:
    role_set = set(roles)
    if "admin" in role_set: return 500
    if "campus_admin" in role_set: return 200
    if role_set.intersection({"ssg", "sg"}): return 120
    return 50

def _enforce_daily_limit(db: Session, user_id: str, user_role: str, effective_roles: List[str]):
    today = datetime.now(timezone.utc).date()
    row = db.query(DailyUsage).filter(
        DailyUsage.user_id == user_id,
        DailyUsage.user_role == user_role,
        DailyUsage.usage_date == today
    ).first()
    
    if row is None:
        row = DailyUsage(user_id=user_id, user_role=user_role, usage_date=today, message_count=0)
        db.add(row)
        db.commit()
        db.refresh(row)

    limit = _get_daily_limit(effective_roles)
    if row.message_count >= limit:
        raise HTTPException(status_code=429, detail=f"Daily limit reached ({limit} messages).")

    row.message_count += 1
    db.commit()

# --- Core Streaming Endpoint ---

@app.post("/assistant/stream")
async def assistant_stream(
    request: Request,
    body: AssistantRequest,
    identity: Dict[str, Any] = Depends(get_current_identity),
    db: Session = Depends(get_db),
):
    authorization = request.headers.get("authorization")
    token_user_id = get_token_user_id(identity)
    
    # 1. Resolve Identity & Roles (v1 Parity)
    governance = await resolve_runtime_governance_access(authorization, token_user_id, body.user_school_id)
    primary_role, effective_roles = get_roles_from_identity(identity, body.user_role, governance.get("roles"))
    effective_permissions = governance.get("permission_codes") or []
    effective_school_id = body.user_school_id or governance.get("school_id") or identity.get("school_id")

    # Enforce Daily Quota (Restored from v1)
    _enforce_daily_limit(db, token_user_id, primary_role, effective_roles)

    # 2. Conversation Management
    conversation_id = body.conversation_id
    if not conversation_id:
        convo = Conversation(user_id=token_user_id, user_role=primary_role)
        db.add(convo)
        db.commit()
        db.refresh(convo)
        conversation_id = convo.id
    else:
        convo = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == token_user_id).first()
        if not convo:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # 3. History Loading
    max_msgs = APP_SETTINGS.context_max_messages
    db_history = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(max_msgs).all()
    history = [{"role": m.role, "content": m.content} for m in reversed(db_history)]
    
    # Save user message
    user_msg = Message(conversation_id=conversation_id, role="user", content=body.message)
    db.add(user_msg)
    db.commit()

    # 4. Prompt Rendering
    readable, writable, scope, cap, non_cap = _render_role_capabilities(effective_roles, effective_permissions)
    system_prompt = _render_system_prompt(
        _load_system_prompt(),
        user_id=token_user_id,
        user_role=primary_role,
        effective_roles=", ".join(effective_roles),
        effective_permissions=", ".join(effective_permissions),
        user_name=body.user_name or identity.get("name") or "User",
        user_school=body.user_school or identity.get("school_name") or "Unknown",
        user_school_id=effective_school_id,
        user_timezone=body.user_timezone or identity.get("timezone") or "UTC",
        readable_tables=readable,
        writable_tables=writable,
        scope_rules=scope,
        capability_notes=cap,
        non_capability_notes=non_cap
    )

    messages = [{"role": "system", "content": system_prompt}] + history + [{"role": "user", "content": body.message}]

    # 5. Background Worker & Queue (The Complex Multi-Turn logic)
    queue = asyncio.Queue()

    async def _worker():
        nonlocal messages
        bg_db = SessionLocal()
        try:
            tools = await mcp_client.get_all_tools()
            final_text = ""
            final_visual = None
            
            for turn in range(10): # Recursive Loop
                async for chunk in call_llm_stream(messages, tools=tools):
                    # If it's an intermediate text chunk, stream it immediately
                    if chunk.get("type") == "chunk":
                        content = chunk.get("content", "")
                        if content:
                            final_text += content
                            await queue.put(_sse_event("message", {"conversation_id": conversation_id, "content": content}))
                        continue
                    
                    # Otherwise, it's the final message for this turn
                    response = chunk
                
                messages.append(response)

                if not response.get("tool_calls"):
                    # Check for recovered markup in text (only if not already streamed)
                    if not final_text:
                        content = _extract_text_content(response.get("content"))
                        if looks_like_tool_markup(content):
                            recovered = extract_function_markup(content)
                            if recovered:
                                messages[-1] = recovered
                                continue
                        
                        final_text = content
                    break
                
                # Execute Tools via MCP
                for tool_call in response["tool_calls"]:
                    fname = tool_call["function"]["name"]
                    fargs = parse_tool_arguments(tool_call["function"].get("arguments", "{}"))
                    # Context Injection (Trust Headers)
                    fargs["roles"] = effective_roles
                    fargs["permissions"] = effective_permissions
                    fargs["user_id"] = token_user_id
                    fargs["school_id"] = effective_school_id
                    fargs["authorization"] = authorization

                    # Tool Execution dispatcher
                    await queue.put(_sse_event("tool_call", {"conversation_id": conversation_id, "tool": fname}))
                    result_json = await mcp_client.call_tool(fname, fargs)
                    await queue.put(_sse_event("tool_done", {"conversation_id": conversation_id, "tool": fname}))
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": fname,
                        "content": result_json
                    })

                    # Intercept Visualization: send SSE and capture for persistence
                    if "visualize" in fname:
                        try:
                            res = json.loads(result_json)
                            if res.get("__aura_visual__"):
                                final_visual = res
                                await queue.put(_sse_event("visualization", {"conversation_id": conversation_id, "visual": res}))
                        except: pass

            # Save Completion (with optional visualization data)
            msg_visual_data = json.dumps({"visual": final_visual}, default=str) if final_visual else None
            assistant_msg = Message(conversation_id=conversation_id, role="assistant", content=final_text, visual_data=msg_visual_data)
            bg_db.add(assistant_msg)
            
            # Auto-title logic
            if len(history) < 2:
                await _update_conversation_title(bg_db, conversation_id, messages)
            
            bg_db.commit()

            await queue.put(_sse_event("done", {"conversation_id": conversation_id, "message_id": str(uuid.uuid4()), "finish_reason": "stop"}))

        except Exception as e:
            logger.error(f"Worker Error: {e}", exc_info=True)
            await queue.put(_sse_event("message", {"conversation_id": conversation_id, "content": f"\n\n[System Error: {str(e)}]\n"}))
            await queue.put(_sse_event("done", {"conversation_id": conversation_id, "message_id": str(uuid.uuid4()), "finish_reason": "error"}))
        finally:
            bg_db.close()
            await queue.put(None)

    asyncio.create_task(_worker())

    async def _stream_generator():
        while True:
            item = await queue.get()
            if item is None: break
            yield item

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(_stream_generator(), media_type="text/event-stream", headers=headers)

# --- Conversation Endpoints (Verbatim from v1) ---

@app.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(identity: Dict[str, Any] = Depends(get_current_identity), db: Session = Depends(get_db)):
    user_id = get_token_user_id(identity)
    rows = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()).all()
    results = []
    for convo in rows:
        last = db.query(Message).filter(Message.conversation_id == convo.id).order_by(Message.created_at.desc()).first()
        results.append(ConversationSummary(
            conversation_id=convo.id,
            title=convo.title,
            last_message=last.content if last else None,
            updated_at=convo.updated_at.replace(tzinfo=timezone.utc) if convo.updated_at else datetime.now(timezone.utc)
        ))
    return results

@app.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, identity: Dict[str, Any] = Depends(get_current_identity), db: Session = Depends(get_db)):
    user_id = get_token_user_id(identity)
    convo = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()
    if not convo: raise HTTPException(status_code=404, detail="Not found")
    msgs = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()
    
    def _parse_msg(m):
        entry = {"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at}
        if m.visual_data:
            try:
                entry["visual_data"] = json.loads(m.visual_data)
            except Exception:
                pass
        return entry
    
    return ConversationDetail(
        conversation_id=convo.id,
        title=convo.title,
        messages=[_parse_msg(m) for m in msgs]
    )

@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, identity: Dict[str, Any] = Depends(get_current_identity), db: Session = Depends(get_db)):
    user_id = get_token_user_id(identity)
    convo = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()
    if not convo: raise HTTPException(status_code=404, detail="Not found")
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    db.delete(convo)
    db.commit()
    return {"status": "deleted"}

@app.patch("/conversations/{conversation_id}")
def update_conversation(conversation_id: str, body: ConversationUpdate, identity: Dict[str, Any] = Depends(get_current_identity), db: Session = Depends(get_db)):
    user_id = get_token_user_id(identity)
    convo = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()
    if not convo: raise HTTPException(status_code=404, detail="Not found")
    
    convo.title = body.title.strip()
    convo.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "updated", "conversation_id": conversation_id, "title": convo.title}
