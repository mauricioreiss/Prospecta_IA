"""n8n Integration - Trigger workflows via webhooks with Chatwoot"""
import httpx
import re
from typing import Dict, Optional, Any
from enum import Enum

from backend.app.config import settings


class N8nAction(str, Enum):
    """Available n8n workflow actions"""
    SEND_WHATSAPP = "send_whatsapp"
    ENRICH_LEAD = "enrich_lead"
    UPDATE_STATUS = "update_status"
    NOTIFY_NEW_LEAD = "notify_new_lead"


def sanitize_message_for_json(message: str) -> str:
    """
    Sanitize message text for safe JSON transmission.
    Keeps newlines as-is - httpx json= handles proper encoding.

    Args:
        message: Raw message text

    Returns:
        Sanitized message
    """
    if not message:
        return ""

    sanitized = message

    # Normalize Windows/Mac newlines to Unix
    sanitized = sanitized.replace('\r\n', '\n')
    sanitized = sanitized.replace('\r', '\n')

    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')

    return sanitized.strip()


async def trigger_n8n(
    action: N8nAction,
    payload: Dict[str, Any],
    timeout: float = 10.0
) -> Dict:
    """
    Trigger an n8n workflow via webhook.

    Args:
        action: The action/workflow to trigger
        payload: Data to send to n8n
        timeout: Request timeout in seconds

    Returns:
        Dict with status and response
    """
    result = {
        "success": False,
        "action": action.value,
        "error": None,
        "response": None
    }

    webhook_url = settings.n8n_webhook_url
    if not webhook_url:
        result["error"] = "N8N_WEBHOOK_URL not configured"
        return result

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(webhook_url, json=payload)
            response.raise_for_status()

            result["success"] = True
            result["response"] = response.json() if response.text else {}

    except httpx.TimeoutException:
        result["error"] = f"Timeout ({timeout}s)"
    except httpx.HTTPStatusError as e:
        result["error"] = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
    except Exception as e:
        result["error"] = str(e)

    return result


async def send_whatsapp_message(
    phone: str,
    message: str,
    tag_campanha: str = "prospeccao_oduo",
    lead_id: Optional[int] = None,
    lead_name: Optional[str] = None
) -> Dict:
    """
    Send WhatsApp message via n8n -> Chatwoot.

    Payload format for n8n 'Info Base' node:
    {
        "url_chatwoot": "https://chat.byduo.com.br",
        "token_chatwoot": "xxx",
        "account_id": 1,
        "phone_number": "5511999999999",
        "mensagem": "Texto da mensagem",
        "tag_campanha": "prospeccao_oduo"
    }

    Args:
        phone: Phone number (with country code, e.g., 5511999999999)
        message: Message text to send
        tag_campanha: Campaign tag for tracking in Chatwoot
        lead_id: Optional lead ID for internal tracking
        lead_name: Optional lead name for context

    Returns:
        Dict with status and any error
    """
    # Sanitize message for JSON safety
    safe_message = sanitize_message_for_json(message)

    # Build Chatwoot-compatible payload for n8n Info Base node
    payload = {
        "url_chatwoot": settings.chatwoot_url,
        "token_chatwoot": settings.chatwoot_token,
        "account_id": settings.chatwoot_account_id,
        "inbox_id": settings.chatwoot_inbox_id,
        "phone_number": phone,
        "mensagem": safe_message,
        "tag_campanha": tag_campanha
    }

    # Add optional metadata for internal tracking (n8n can use or ignore)
    if lead_id:
        payload["_lead_id"] = lead_id
    if lead_name:
        payload["_lead_name"] = lead_name

    return await trigger_n8n(N8nAction.SEND_WHATSAPP, payload)


async def send_whatsapp_single(
    phone: str,
    message: str,
    tag_campanha: str = "reativacao_oduo",
    inbox_id: Optional[int] = None
) -> Dict:
    """
    Send a single WhatsApp message via n8n -> Chatwoot.

    This is the preferred method for bulk sending - call this in a loop
    with delays between each call for maximum reliability.

    Args:
        phone: Phone number with country code (e.g., 5511999999999)
        message: Message text to send
        tag_campanha: Campaign tag for tracking in Chatwoot
        inbox_id: Optional inbox ID override

    Returns:
        Dict with success status and any error
    """
    safe_message = sanitize_message_for_json(message)

    payload = {
        "url_chatwoot": settings.chatwoot_url,
        "token_chatwoot": settings.chatwoot_token,
        "account_id": settings.chatwoot_account_id,
        "inbox_id": inbox_id or settings.chatwoot_inbox_id,
        "phone_number": phone,
        "mensagem": safe_message,
        "tag_campanha": tag_campanha
    }

    return await trigger_n8n(N8nAction.SEND_WHATSAPP, payload)


async def send_whatsapp_duas_mensagens(
    phone: str,
    msg1: str,
    msg2: str,
    tag_campanha: str = "reativacao_oduo",
    inbox_id: Optional[int] = None
) -> Dict:
    """
    Send TWO WhatsApp messages in ONE conversation via n8n -> Chatwoot.

    This creates ONE conversation and sends both messages in it,
    avoiding duplicate conversations.

    Args:
        phone: Phone number with country code (e.g., 5511999999999)
        msg1: First message (opening)
        msg2: Second message (CTA + link)
        tag_campanha: Campaign tag for tracking in Chatwoot
        inbox_id: Optional inbox ID override

    Returns:
        Dict with success status and any error
    """
    safe_msg1 = sanitize_message_for_json(msg1)
    safe_msg2 = sanitize_message_for_json(msg2)

    payload = {
        "url_chatwoot": settings.chatwoot_url,
        "token_chatwoot": settings.chatwoot_token,
        "account_id": settings.chatwoot_account_id,
        "inbox_id": inbox_id or settings.chatwoot_inbox_id,
        "phone_number": phone,
        "mensagem": safe_msg1,
        "mensagem2": safe_msg2,
        "tag_campanha": tag_campanha
    }

    return await trigger_n8n(N8nAction.SEND_WHATSAPP, payload)


async def notify_new_lead(lead_data: Dict) -> Dict:
    """
    Notify n8n about a new hot lead (for immediate action).

    Args:
        lead_data: Lead information

    Returns:
        Dict with status
    """
    return await trigger_n8n(N8nAction.NOTIFY_NEW_LEAD, lead_data)
