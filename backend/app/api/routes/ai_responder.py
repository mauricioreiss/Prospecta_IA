"""AI Responder - Automatic WhatsApp responses using OpenAI with lead context"""
import json
from datetime import datetime
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.integrations.supabase import get_supabase_client
from backend.app.integrations.n8n import send_whatsapp_single

# OpenAI import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

router = APIRouter(prefix="/ai-responder", tags=["ai-responder"])


# ===========================================
# INTENT DETECTION - Keywords
# ===========================================

INTEREST_KEYWORDS = [
    # Positive interest
    'sim', 'quero', 'bora', 'vamos', 'interessado', 'interesse',
    'faz sentido', 'gostaria', 'pode ser', 'topo', 'fechado',
    'show', 'perfeito', 'massa', 'combinado', 'ok', 'beleza',
    'manda', 'envia', 'passa', 'me conta', 'como funciona',
    'quanto custa', 'valor', 'preco', 'investimento',
    'quero participar', 'quero ver', 'me inscreve',
    # Scheduling
    'agenda', 'agendar', 'marcar', 'horario', 'disponivel',
    'quando', 'amanha', 'hoje', 'semana que vem'
]

NEGATIVE_KEYWORDS = [
    'nao', 'nao quero', 'nao tenho interesse', 'sem interesse',
    'nao preciso', 'nao obrigado', 'para de', 'sai fora',
    'remove', 'descadastrar', 'bloquear', 'spam',
    'nao me manda', 'nao quero receber', 'para'
]

QUESTION_KEYWORDS = [
    'quem', 'como', 'onde', 'quando', 'porque', 'por que',
    'qual', 'o que', 'quanto', '?',
    'conseguiu', 'pegou', 'achou', 'descobriu',
    'numero', 'contato', 'conhece', 'lembra'
]


class IncomingMessage(BaseModel):
    """Incoming message from Chatwoot webhook"""
    phone: str
    message: str
    conversation_id: Optional[int] = None
    contact_id: Optional[int] = None
    inbox_id: Optional[int] = None


class AIResponse(BaseModel):
    """AI generated response"""
    response: str
    intent: str  # interest, negative, question, neutral
    should_send_link: bool
    lead_context: Optional[Dict] = None


# ===========================================
# LEAD CONTEXT STORAGE
# ===========================================

async def save_lead_context(phone: str, name: str, notes: str, company: str, campaign_id: str = None):
    """
    Save lead context for future AI responses.
    Called when sending reactivation messages.
    """
    try:
        client = get_supabase_client()

        # Upsert - update if exists, insert if not
        client.table('reactivation_leads').upsert({
            'phone': phone,
            'name': name,
            'notes': notes,
            'company': company,
            'campaign_id': campaign_id,
            'last_contact': datetime.now().isoformat(),
            'status': 'contacted'
        }, on_conflict='phone').execute()

        return True
    except Exception as e:
        print(f"Warning: Could not save lead context for {phone}: {e}")
        return False


async def get_lead_context(phone: str) -> Optional[Dict]:
    """
    Get lead context by phone number.
    Returns name, notes, company, conversation history.
    """
    try:
        client = get_supabase_client()

        # Normalize phone
        phone_clean = ''.join(c for c in phone if c.isdigit())
        if not phone_clean.startswith('55'):
            phone_clean = '55' + phone_clean

        # Try exact match first
        result = client.table('reactivation_leads').select(
            "*"
        ).eq('phone', phone_clean).execute()

        if result.data and len(result.data) > 0:
            lead = result.data[0]
            return {
                'name': lead.get('name', 'Amigo'),
                'notes': lead.get('notes', ''),
                'company': lead.get('company', ''),
                'status': lead.get('status', 'unknown'),
                'last_contact': lead.get('last_contact'),
                'conversation_history': lead.get('conversation_history', [])
            }

        # Try without country code
        if phone_clean.startswith('55'):
            phone_without_55 = phone_clean[2:]
            result = client.table('reactivation_leads').select(
                "*"
            ).eq('phone', phone_without_55).execute()

            if result.data and len(result.data) > 0:
                lead = result.data[0]
                return {
                    'name': lead.get('name', 'Amigo'),
                    'notes': lead.get('notes', ''),
                    'company': lead.get('company', ''),
                    'status': lead.get('status', 'unknown'),
                    'last_contact': lead.get('last_contact'),
                    'conversation_history': lead.get('conversation_history', [])
                }

        return None

    except Exception as e:
        print(f"Error getting lead context for {phone}: {e}")
        return None


async def update_lead_status(phone: str, status: str, add_to_history: str = None):
    """Update lead status and optionally add to conversation history"""
    try:
        client = get_supabase_client()

        phone_clean = ''.join(c for c in phone if c.isdigit())
        if not phone_clean.startswith('55'):
            phone_clean = '55' + phone_clean

        update_data = {
            'status': status,
            'updated_at': datetime.now().isoformat()
        }

        client.table('reactivation_leads').update(update_data).eq('phone', phone_clean).execute()

    except Exception as e:
        print(f"Error updating lead status for {phone}: {e}")


# ===========================================
# INTENT DETECTION
# ===========================================

def detect_intent(message: str) -> str:
    """
    Detect the intent of a message.
    Returns: 'interest', 'negative', 'question', 'neutral'
    """
    message_lower = message.lower().strip()

    # Check for negative first (highest priority)
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in message_lower:
            return 'negative'

    # Check for interest keywords
    interest_score = 0
    for keyword in INTEREST_KEYWORDS:
        if keyword in message_lower:
            interest_score += 1

    if interest_score >= 1:
        return 'interest'

    # Check for questions
    for keyword in QUESTION_KEYWORDS:
        if keyword in message_lower:
            return 'question'

    return 'neutral'


# ===========================================
# AI RESPONSE GENERATION
# ===========================================

def get_openai_client() -> Optional[OpenAI]:
    """Get OpenAI client if available"""
    if not OPENAI_AVAILABLE:
        return None
    if not settings.openai_api_key:
        return None
    return OpenAI(api_key=settings.openai_api_key)


SYSTEM_PROMPT_TEMPLATE = """Voce e Joao, consultor comercial da Oduo Assessoria.

CONTEXTO DO LEAD:
- Nome: {name}
- Empresa: {company}
- Resumo/Dificuldade anterior: {notes}

SITUACAO: Voce enviou uma mensagem de reativacao para este lead que ja conversou com a empresa antes.
Agora ele respondeu e voce precisa continuar a conversa de forma natural.

REGRAS IMPORTANTES:
1. Seja BREVE - maximo 2-3 frases por resposta
2. Use o nome da pessoa quando possivel
3. Seja informal mas profissional (nada de "prezado" ou "caro")
4. NUNCA invente informacoes - use apenas o que esta no contexto
5. Se perguntarem como conseguiu o numero, diga que conversaram anteriormente sobre {notes}
6. Se mostrarem interesse, convide para o evento/aula gratuita

LINK DE AGENDAMENTO: {booking_link}
(Envie este link APENAS quando o lead demonstrar interesse claro)

OBJETIVO: Qualificar o lead e convidar para evento/chamada se houver interesse.

TIPO DE MENSAGEM RECEBIDA: {intent}
{intent_instruction}
"""

INTENT_INSTRUCTIONS = {
    'interest': "O lead mostrou INTERESSE! Responda positivamente e envie o link de agendamento.",
    'negative': "O lead NAO tem interesse. Agradeca educadamente e se despeca. NAO insista.",
    'question': "O lead fez uma PERGUNTA. Responda usando o contexto disponivel.",
    'neutral': "Mensagem neutra. Faca uma pergunta para entender melhor o interesse."
}


async def generate_ai_response(
    message: str,
    lead_context: Dict,
    intent: str,
    booking_link: str = "https://calendly.com/oduo"
) -> str:
    """
    Generate AI response using OpenAI GPT.

    Args:
        message: The incoming message from lead
        lead_context: Dict with name, notes, company
        intent: Detected intent (interest, negative, question, neutral)
        booking_link: Link to send when lead shows interest

    Returns:
        Generated response text
    """
    client = get_openai_client()

    if not client:
        # Fallback responses when OpenAI is not available
        return generate_fallback_response(message, lead_context, intent, booking_link)

    # Build system prompt with context
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        name=lead_context.get('name', 'Amigo'),
        company=lead_context.get('company', 'sua empresa'),
        notes=lead_context.get('notes', 'crescer o negocio'),
        booking_link=booking_link,
        intent=intent,
        intent_instruction=INTENT_INSTRUCTIONS.get(intent, '')
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper and faster for chat
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"OpenAI error: {e}")
        return generate_fallback_response(message, lead_context, intent, booking_link)


def generate_fallback_response(
    message: str,
    lead_context: Dict,
    intent: str,
    booking_link: str
) -> str:
    """
    Generate fallback response when OpenAI is not available.
    Uses templates based on intent.
    """
    name = lead_context.get('name', 'Amigo')
    notes = lead_context.get('notes', 'crescer o negocio')

    if intent == 'interest':
        return f"Show {name}! Fico feliz que faca sentido pra voce.\n\nSegue o link pra gente conversar: {booking_link}\n\nEscolhe o melhor horario ai!"

    elif intent == 'negative':
        return f"Entendo {name}, sem problemas! Se mudar de ideia no futuro, estou por aqui. Sucesso ai!"

    elif intent == 'question':
        # Check if it's about how we got the number
        if any(word in message.lower() for word in ['numero', 'contato', 'conseguiu', 'achou']):
            return f"Conversamos ha um tempo atras sobre {notes}, {name}. Voltei pra ver se ainda faz sentido pra voce!"
        else:
            return f"Boa pergunta {name}! Basicamente, a gente ajuda empresarios a {notes}. Quer que eu te explique melhor como funciona?"

    else:  # neutral
        return f"E ai {name}, o que achou? Faz sentido pra sua situacao?"


# ===========================================
# API ENDPOINTS
# ===========================================

@router.post("/webhook")
async def receive_chatwoot_message(payload: dict):
    """
    Webhook endpoint to receive incoming messages from Chatwoot.

    Expected payload from Chatwoot:
    {
        "event": "message_created",
        "message_type": "incoming",
        "conversation": {
            "id": 123,
            "contact_inbox": {
                "source_id": "5511999999999"  # Phone number
            }
        },
        "content": "Message text here"
    }
    """
    # Validate it's an incoming message
    if payload.get('message_type') != 'incoming':
        return {"status": "ignored", "reason": "not incoming message"}

    if payload.get('event') != 'message_created':
        return {"status": "ignored", "reason": "not message_created event"}

    # Extract data
    try:
        conversation = payload.get('conversation', {})
        contact_inbox = conversation.get('contact_inbox', {})
        phone = contact_inbox.get('source_id', '')
        message = payload.get('content', '')
        conversation_id = conversation.get('id')

        if not phone or not message:
            return {"status": "error", "reason": "missing phone or message"}

    except Exception as e:
        return {"status": "error", "reason": f"payload parsing error: {e}"}

    # Process the message
    result = await process_incoming_message(
        phone=phone,
        message=message,
        conversation_id=conversation_id
    )

    return result


@router.post("/process")
async def process_message_manual(incoming: IncomingMessage):
    """
    Manual endpoint to process a message (for testing or direct integration).
    """
    return await process_incoming_message(
        phone=incoming.phone,
        message=incoming.message,
        conversation_id=incoming.conversation_id
    )


async def process_incoming_message(
    phone: str,
    message: str,
    conversation_id: Optional[int] = None,
    auto_send: bool = True
) -> Dict:
    """
    Process an incoming message and generate/send AI response.

    Args:
        phone: Phone number of the sender
        message: Message content
        conversation_id: Optional Chatwoot conversation ID
        auto_send: If True, automatically send response via WhatsApp

    Returns:
        Dict with response details
    """
    # 1. Get lead context
    lead_context = await get_lead_context(phone)

    if not lead_context:
        # Unknown lead - we don't have context
        return {
            "status": "no_context",
            "phone": phone,
            "message": "Lead nao encontrado na base de reativacao"
        }

    # 2. Detect intent
    intent = detect_intent(message)

    # 3. Determine if we should send link
    should_send_link = intent == 'interest'

    # 4. Generate AI response
    booking_link = settings.booking_link if hasattr(settings, 'booking_link') else "https://calendly.com/oduo"

    ai_response = await generate_ai_response(
        message=message,
        lead_context=lead_context,
        intent=intent,
        booking_link=booking_link
    )

    # 5. Update lead status based on intent
    status_map = {
        'interest': 'interessado',
        'negative': 'perdido',
        'question': 'em_conversa',
        'neutral': 'em_conversa'
    }
    await update_lead_status(phone, status_map.get(intent, 'em_conversa'))

    # 6. Send response if auto_send is enabled
    send_result = None
    if auto_send and ai_response:
        send_result = await send_whatsapp_single(
            phone=phone,
            message=ai_response,
            tag_campanha="ai_responder"
        )

    return {
        "status": "processed",
        "phone": phone,
        "incoming_message": message,
        "intent": intent,
        "should_send_link": should_send_link,
        "ai_response": ai_response,
        "lead_context": {
            "name": lead_context.get('name'),
            "company": lead_context.get('company'),
            "notes": lead_context.get('notes')
        },
        "send_result": send_result
    }


@router.get("/test/{phone}")
async def test_lead_context(phone: str):
    """Test endpoint to check if we have context for a phone number"""
    context = await get_lead_context(phone)

    if context:
        return {
            "found": True,
            "context": context
        }
    else:
        return {
            "found": False,
            "message": f"No context found for {phone}"
        }


@router.post("/test-response")
async def test_ai_response(incoming: IncomingMessage):
    """
    Test AI response without sending the message.
    Good for testing the AI behavior.
    """
    return await process_incoming_message(
        phone=incoming.phone,
        message=incoming.message,
        auto_send=False  # Don't actually send
    )
