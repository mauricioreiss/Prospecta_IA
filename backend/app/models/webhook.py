"""Webhook models - n8n, Uazap, Vapi payloads"""
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel


class UazapMessage(BaseModel):
    """Incoming WhatsApp message from Uazap"""
    from_number: str
    to_number: str
    message_type: Literal["text", "audio", "image"]
    content: str
    timestamp: datetime
    raw: Optional[Dict[str, Any]] = None


class VapiCallEvent(BaseModel):
    """Vapi call status event"""
    call_id: str
    event_type: Literal["call.started", "call.ended", "transcript.update", "status.update"]
    lead_id: Optional[str] = None
    lead_name: Optional[str] = None
    phone_number: Optional[str] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[str] = None
    status_message: Optional[str] = None
    timestamp: datetime


class N8nTrigger(BaseModel):
    """Generic n8n webhook trigger"""
    action: str
    payload: Dict[str, Any]
    source: str = "n8n"
