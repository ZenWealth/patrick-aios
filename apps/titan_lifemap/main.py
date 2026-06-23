"""
Titan LifeMap - FastAPI Application

API endpoints for the Titan LifeMap discovery engine.

Routes:
    POST /session/start              -> create session, return session_id + opening message
    POST /session/{id}/message       -> send user message, return assistant response
    GET  /session/{id}/status        -> return current session state

Internal AI Profile has NO endpoint here. It is generated on session completion
via the analysis pass and stored in titan_internal_profiles only.
"""

import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from apps.titan_lifemap.config_loader import validate_all
from apps.titan_lifemap.db import get_connection, create_session, get_session
from apps.titan_lifemap import conversation

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail loudly at startup if any config file is missing/malformed
    validate_all()
    logger.info("Titan LifeMap config validated successfully")
    yield


app = FastAPI(
    title="Titan LifeMap API",
    description="AI-powered financial discovery engine for Sustain Momentum",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sustain-momentum.com", "https://www.sustain-momentum.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# --- Request / Response models ---

class StartResponse(BaseModel):
    session_id: str
    message: str
    stage: str


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    message: str
    stage: str
    stage_complete: bool
    session_complete: bool
    requests_contact: bool


class SessionStatus(BaseModel):
    session_id: str
    stage: str
    completed: bool
    has_contact: bool
    route: str | None


# --- Endpoints ---

@app.post("/session/start", response_model=StartResponse)
async def start_session():
    """Create a new discovery session and return the opening message."""
    session_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        create_session(conn, session_id)
    finally:
        conn.close()

    opening_message = conversation.start_session(session_id)
    return StartResponse(
        session_id=session_id,
        message=opening_message,
        stage="visionary",
    )


@app.post("/session/{session_id}/message", response_model=MessageResponse)
async def send_message(session_id: str, request: MessageRequest):
    """Send a user message and receive the next assistant response."""
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
    finally:
        conn.close()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    response = conversation.send_message(session_id, request.message)
    return MessageResponse(
        message=response.message,
        stage=response.stage,
        stage_complete=response.stage_complete,
        session_complete=response.session_complete,
        requests_contact=response.requests_contact,
    )


@app.get("/session/{session_id}/status", response_model=SessionStatus)
async def session_status(session_id: str):
    """Return the current state of a session."""
    conn = get_connection()
    try:
        session = get_session(conn, session_id)
    finally:
        conn.close()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionStatus(
        session_id=session_id,
        stage=session["current_stage"],
        completed=bool(session["completed"]),
        has_contact=bool(session.get("email")),
        route=session.get("route"),
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "titan-lifemap"}
