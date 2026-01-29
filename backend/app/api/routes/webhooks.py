"""Webhooks API Routes - n8n, Uazap, Vapi"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

from backend.app.models import UazapMessage, VapiCallEvent, N8nTrigger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/uazap")
async def uazap_webhook(request: Request):
    """
    Handle incoming WhatsApp messages from Uazap.
    Multimodal: detect text vs audio and respond accordingly.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Parse Uazap payload (adapt to actual format)
    message_type = payload.get("type", "text")
    from_number = payload.get("from", "")
    content = payload.get("body", "")

    # TODO: Implement multimodal logic
    # If audio: transcribe with Whisper, respond with ElevenLabs
    # If text: respond with text

    return {
        "status": "received",
        "type": message_type,
        "from": from_number,
        "action": "text_response" if message_type == "text" else "audio_response"
    }


@router.post("/vapi")
async def vapi_webhook(request: Request):
    """
    Handle Vapi call events.
    Events: call.started, call.ended, transcript.update, status.update
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = payload.get("type", "")
    call_id = payload.get("call_id", "")

    # Log call event for real-time UI updates
    # In production, push to WebSocket or Redis pub/sub

    if event_type == "call.ended":
        # Save call summary to lead interactions
        duration = payload.get("duration_seconds", 0)
        transcript = payload.get("transcript", "")

        # TODO: Extract lead_id and save interaction
        return {
            "status": "processed",
            "event": event_type,
            "duration": duration
        }

    return {"status": "received", "event": event_type}


@router.post("/n8n")
async def n8n_webhook(request: Request):
    """
    Generic n8n webhook handler.
    Actions: enrich_lead, send_whatsapp, update_status
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    action = payload.get("action", "")
    data = payload.get("payload", {})

    if action == "enrich_lead":
        # Trigger Tavily enrichment
        lead_id = data.get("lead_id")
        # TODO: Enrich lead with Tavily
        return {"status": "enriched", "lead_id": lead_id}

    elif action == "send_whatsapp":
        # Queue WhatsApp message via Uazap
        phone = data.get("phone")
        message = data.get("message")
        # TODO: Send via Uazap
        return {"status": "queued", "phone": phone}

    elif action == "update_status":
        # Update lead status
        lead_id = data.get("lead_id")
        new_status = data.get("status")
        # TODO: Update status
        return {"status": "updated", "lead_id": lead_id}

    return {"status": "unknown_action", "action": action}
