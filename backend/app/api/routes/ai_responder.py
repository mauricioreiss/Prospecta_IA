"""AI Responder - Automatic WhatsApp responses using OpenAI with lead context
Supports: Reactivation, SPIN Cold, Filtro Hibrido (Landing Page Inbound)"""
import json
import re
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.config import settings
from backend.app.integrations.supabase import get_supabase_client
from backend.app.integrations.n8n import send_whatsapp_single
from backend.app.core.prompts import (
    FILTRO_HIBRIDO_PROMPT,
    EMPRESA_KEYWORDS,
    DOR_KEYWORDS,
    URGENCIA_KEYWORDS,
    FATURAMENTO_KEYWORDS,
    SOCIO_KEYWORDS
)

# OpenAI import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

router = APIRouter(prefix="/ai-responder", tags=["ai-responder"])

# Google Calendar link
CALENDAR_LINK = "https://calendar.app.google/pAYRqssNvDxde6K28"


# ===========================================
# INTENT DETECTION - Keywords
# ===========================================

INTEREST_KEYWORDS = [
    'sim', 'quero', 'bora', 'vamos', 'interessado', 'interesse',
    'faz sentido', 'gostaria', 'pode ser', 'topo', 'fechado',
    'show', 'perfeito', 'massa', 'combinado', 'ok', 'beleza',
    'manda', 'envia', 'passa', 'me conta', 'como funciona',
    'quanto custa', 'valor', 'preco', 'investimento',
    'quero participar', 'quero ver', 'me inscreve',
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


# ===========================================
# MODELS
# ===========================================

class IncomingMessage(BaseModel):
    """Incoming message from Chatwoot webhook"""
    phone: str
    message: str
    conversation_id: Optional[int] = None
    contact_id: Optional[int] = None
    inbox_id: Optional[int] = None
    sender_name: Optional[str] = None
    auto_send: bool = True


class AIResponse(BaseModel):
    """AI generated response"""
    response: str
    intent: str
    should_send_link: bool
    lead_context: Optional[Dict] = None


class QualifyRequest(BaseModel):
    """Post-response qualification request from n8n"""
    phone: str
    incoming_message: str
    ai_response: str
    intent: str
    conversation_id: Optional[int] = None


# ===========================================
# PHONE NORMALIZATION
# ===========================================

def normalize_phone(phone: str) -> str:
    """Normalize phone to digits with 55 prefix"""
    phone_clean = ''.join(c for c in phone if c.isdigit())
    if not phone_clean.startswith('55'):
        phone_clean = '55' + phone_clean
    return phone_clean


# ===========================================
# LEAD CONTEXT STORAGE
# ===========================================

async def save_lead_context(phone: str, name: str, notes: str, company: str, campaign_id: str = None):
    """Save lead context for future AI responses."""
    try:
        client = get_supabase_client()
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


async def create_inbound_lead(phone: str, sender_name: str = None):
    """Auto-create an inbound lead from landing page (first contact)."""
    try:
        client = get_supabase_client()
        phone_clean = normalize_phone(phone)
        name = sender_name or 'Lead'

        client.table('reactivation_leads').upsert({
            'phone': phone_clean,
            'name': name,
            'notes': 'Lead inbound - veio da landing page',
            'company': '',
            'campaign_id': 'inbound_landing',
            'last_contact': datetime.now().isoformat(),
            'status': 'novo',
            'conversation_history': [],
            'qualification_data': {},
            'qualification_progress': 0,
            'phase': 'rapport'
        }, on_conflict='phone').execute()

        return {
            'name': name,
            'notes': 'Lead inbound - veio da landing page',
            'company': '',
            'campaign_id': 'inbound_landing',
            'status': 'novo',
            'conversation_history': [],
            'qualification_data': {},
            'qualification_progress': 0,
            'phase': 'rapport'
        }
    except Exception as e:
        print(f"Error creating inbound lead {phone}: {e}")
        return None


async def get_lead_context(phone: str) -> Optional[Dict]:
    """Get lead context by phone number."""
    try:
        client = get_supabase_client()
        phone_clean = normalize_phone(phone)

        result = client.table('reactivation_leads').select(
            "*"
        ).eq('phone', phone_clean).execute()

        if result.data and len(result.data) > 0:
            lead = result.data[0]
            return {
                'name': lead.get('name', 'Amigo'),
                'notes': lead.get('notes', ''),
                'company': lead.get('company', ''),
                'campaign_id': lead.get('campaign_id', ''),
                'status': lead.get('status', 'unknown'),
                'last_contact': lead.get('last_contact'),
                'conversation_history': lead.get('conversation_history', []),
                'qualification_data': lead.get('qualification_data', {}),
                'qualification_progress': lead.get('qualification_progress', 0),
                'phase': lead.get('phase', 'rapport')
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
                    'campaign_id': lead.get('campaign_id', ''),
                    'status': lead.get('status', 'unknown'),
                    'last_contact': lead.get('last_contact'),
                    'conversation_history': lead.get('conversation_history', []),
                    'qualification_data': lead.get('qualification_data', {}),
                    'qualification_progress': lead.get('qualification_progress', 0),
                    'phase': lead.get('phase', 'rapport')
                }

        return None

    except Exception as e:
        print(f"Error getting lead context for {phone}: {e}")
        return None


async def update_lead_status(phone: str, status: str):
    """Update lead status"""
    try:
        client = get_supabase_client()
        phone_clean = normalize_phone(phone)
        client.table('reactivation_leads').update({
            'status': status,
            'updated_at': datetime.now().isoformat()
        }).eq('phone', phone_clean).execute()
    except Exception as e:
        print(f"Error updating lead status for {phone}: {e}")


async def save_conversation_exchange(phone: str, lead_message: str, ai_response: str):
    """Save a conversation exchange to history."""
    try:
        client = get_supabase_client()
        phone_clean = normalize_phone(phone)

        result = client.table('reactivation_leads').select(
            'conversation_history'
        ).eq('phone', phone_clean).execute()

        history = []
        if result.data and len(result.data) > 0:
            raw = result.data[0].get('conversation_history')
            if raw:
                history = json.loads(raw) if isinstance(raw, str) else raw

        now = datetime.now().isoformat()
        history.append({"role": "lead", "content": lead_message, "timestamp": now})
        history.append({"role": "bot", "content": ai_response, "timestamp": now})
        history = history[-20:]

        client.table('reactivation_leads').update({
            'conversation_history': history,
            'updated_at': now
        }).eq('phone', phone_clean).execute()

        return True
    except Exception as e:
        print(f"Error saving conversation exchange for {phone}: {e}")
        return False


async def update_qualification(phone: str, qual_data: dict, progress: int, phase: str, insights: str = ""):
    """Update qualification data, progress, phase and insights."""
    try:
        client = get_supabase_client()
        phone_clean = normalize_phone(phone)

        update = {
            'qualification_data': qual_data,
            'qualification_progress': progress,
            'phase': phase,
            'updated_at': datetime.now().isoformat()
        }
        if insights:
            update['salesperson_insights'] = insights

        client.table('reactivation_leads').update(update).eq('phone', phone_clean).execute()
    except Exception as e:
        print(f"Error updating qualification for {phone}: {e}")


# ===========================================
# QUALIFICATION DATA EXTRACTION
# ===========================================

def extract_cnpj(text: str) -> Optional[str]:
    """Extract CNPJ from text (XX.XXX.XXX/XXXX-XX or 14 digits)."""
    # Format: XX.XXX.XXX/XXXX-XX
    match = re.search(r'\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}', text)
    if match:
        return match.group(0)
    # 14 consecutive digits
    match = re.search(r'\b\d{14}\b', text)
    if match:
        return match.group(0)
    return None


def extract_empresa(text: str) -> Optional[str]:
    """Extract company name or segment from text."""
    text_lower = text.lower()
    for keyword in EMPRESA_KEYWORDS:
        if keyword in text_lower:
            return keyword
    # Check for proper noun patterns
    name_patterns = [
        r'(?:sou\s+d[ao]|minha\s+empresa|empresa\s+e|chamo?\s+)\s+([A-Z][a-zA-Z\s&]+)',
        r'(?:locadora|empresa|loja)\s+([A-Z][a-zA-Z\s&]+)',
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def extract_dor(text: str) -> Optional[str]:
    """Extract pain point / problem from text."""
    text_lower = text.lower()
    for kw in DOR_KEYWORDS:
        if kw in text_lower:
            return kw
    return None


def extract_faturamento(text: str) -> Optional[str]:
    """Extract revenue bracket from text."""
    text_lower = text.lower()

    if any(kw in text_lower for kw in ['acima de 50', 'acima 50', 'mais de 50', 'acima_50k']):
        return 'acima_50k'
    if any(kw in text_lower for kw in ['20-50', '20 a 50', '20_50k', 'entre 20', '20 e 50']):
        return '20_50k'
    if any(kw in text_lower for kw in ['ate 20', 'menos de 20', 'ate_20k', 'abaixo de 20']):
        return 'ate_20k'

    for kw in FATURAMENTO_KEYWORDS:
        if kw in text_lower:
            return kw
    return None


def extract_socio(text: str) -> Optional[str]:
    """Extract partner/owner info from text."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ['sou dono', 'sou o dono', 'eu que decido', 'sozinho', 'so eu', 'sou eu mesmo', 'proprietario']):
        return 'dono_unico'
    if any(kw in text_lower for kw in ['tenho socio', 'tem socio', 'meu socio', 'meu parceiro', 'socio']):
        return 'tem_socio'
    return None


def extract_cidade(text: str) -> Optional[str]:
    """Extract city mention from text."""
    # Common patterns for city mentions
    city_patterns = [
        r'(?:de|em|aqui\s+em|moro\s+em|fico\s+em|cidade\s+de|sou\s+de)\s+([A-Z][a-zA-Zà-úÀ-Ú\s]+)',
        r'([A-Z][a-zA-Zà-úÀ-Ú]+(?:\s+[A-Z][a-zA-Zà-úÀ-Ú]+)?)\s*[-/]\s*[A-Z]{2}',  # "Cidade - SP"
    ]
    for pattern in city_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None


def extract_qualification_from_history(history: list, existing_data: dict) -> dict:
    """
    Extract qualification data from conversation history.
    Merges with existing data (never removes already collected data).
    4 points: empresa, dor, faturamento, socio
    """
    qual_data = dict(existing_data) if existing_data else {}

    for msg in history:
        if msg.get('role') != 'lead':
            continue
        content = msg.get('content', '')

        if not qual_data.get('empresa'):
            emp = extract_empresa(content)
            if emp:
                qual_data['empresa'] = emp

        if not qual_data.get('dor'):
            dor = extract_dor(content)
            if dor:
                qual_data['dor'] = dor

        if not qual_data.get('faturamento'):
            fat = extract_faturamento(content)
            if fat:
                qual_data['faturamento'] = fat

        if not qual_data.get('socio'):
            soc = extract_socio(content)
            if soc:
                qual_data['socio'] = soc

        # Also extract optional data (cidade, nome)
        if not qual_data.get('cidade'):
            cidade = extract_cidade(content)
            if cidade:
                qual_data['cidade'] = cidade

    return qual_data


def calculate_progress(qual_data: dict) -> int:
    """Calculate qualification progress 0-4.
    4 points: empresa, dor, faturamento, socio"""
    count = 0
    if qual_data.get('empresa'):
        count += 1
    if qual_data.get('dor'):
        count += 1
    if qual_data.get('faturamento'):
        count += 1
    if qual_data.get('socio'):
        count += 1
    return count


def get_missing_data(qual_data: dict) -> list:
    """Get list of missing qualification data."""
    missing = []
    if not qual_data.get('empresa'):
        missing.append('locadora/empresa')
    if not qual_data.get('dor'):
        missing.append('dor/problema identificado')
    if not qual_data.get('faturamento'):
        missing.append('faturamento')
    if not qual_data.get('socio'):
        missing.append('dono ou tem socio')
    return missing


def determine_phase(history: list, qual_data: dict, intent: str) -> str:
    """Determine current SPIN phase."""
    progress = calculate_progress(qual_data)

    if progress == 4:
        return 'ouro'

    if intent == 'negative':
        exchanges = len(history) // 2
        if exchanges >= 3 and progress < 2:
            return 'curioso'
        return 'curioso' if progress < 1 else 'qualificacao'

    exchanges = len(history) // 2
    if exchanges <= 1:
        return 'situacao'  # S - Situacao
    elif not qual_data.get('dor'):
        return 'problema'  # P - Problema
    elif progress < 3:
        return 'implicacao'  # I - Implicacao
    else:
        return 'necessidade'  # N - Necessidade/Qualificacao


def get_etapa_spin(phase: str, qual_data: dict) -> str:
    """Get SPIN stage description for prompt."""
    if phase == 'ouro':
        return "[OURO] Lead qualificado! Pode propor reuniao - MAS QUALIFIQUE SOCIO ANTES!"
    elif phase == 'situacao':
        return "[S] SITUACAO - Pergunte nome, locadora, cidade, como ta o movimento"
    elif phase == 'problema':
        return "[P] PROBLEMA - Encontre a DOR! Pergunte sobre dificuldades em conseguir clientes"
    elif phase == 'implicacao':
        return "[I] IMPLICACAO - FACA DOER! Mostre o prejuizo de nao resolver AGORA"
    elif phase == 'necessidade':
        return "[N] NECESSIDADE - Pode propor reuniao - MAS QUALIFIQUE FATURAMENTO/SOCIO ANTES!"
    elif phase == 'curioso':
        return "[CURIOSO] Lead sem interesse real. Encerre educadamente."
    return "[S/P] Precisa identificar situacao e problema antes de avancar"


def generate_salesperson_insights(lead_context: dict, qual_data: dict, history: list) -> str:
    """Generate insights for the salesperson based on collected data."""
    lines = []
    name = lead_context.get('name', 'Lead')

    if qual_data.get('empresa'):
        lines.append(f"Locadora/Empresa: {qual_data['empresa']}")

    if qual_data.get('cidade'):
        lines.append(f"Cidade: {qual_data['cidade']}")

    if qual_data.get('dor'):
        lines.append(f"Dor identificada: {qual_data['dor']}")

    if qual_data.get('faturamento'):
        faixa_map = {
            'ate_20k': 'Pequeno porte (ate R$20k) - foco em comecar a crescer',
            '20_50k': 'Medio porte (R$20-50k) - foco em proximo nivel',
            'acima_50k': 'Grande porte (acima R$50k) - foco em escala e automacao'
        }
        lines.append(f"Faturamento: {faixa_map.get(qual_data['faturamento'], qual_data['faturamento'])}")

    if qual_data.get('socio'):
        socio_map = {
            'dono_unico': 'Dono unico - pode decidir sozinho',
            'tem_socio': 'TEM SOCIO - garantir presenca na call!'
        }
        lines.append(f"Decisor: {socio_map.get(qual_data['socio'], qual_data['socio'])}")

    # Conversation tone analysis
    lead_msgs = [m.get('content', '') for m in history if m.get('role') == 'lead']
    if lead_msgs:
        total_chars = sum(len(m) for m in lead_msgs)
        avg_length = total_chars / len(lead_msgs)

        if avg_length > 50:
            lines.append("Perfil: Comunicativo, gosta de detalhar")
        elif avg_length < 15:
            lines.append("Perfil: Direto, prefere objetividade")

        all_text = ' '.join(lead_msgs).lower()
        if any(kw in all_text for kw in ['urgente', 'pra ontem', 'rapido', 'hoje', 'amanha', 'prioridade']):
            lines.append("ALERTA: Lead com urgencia alta!")
        if any(kw in all_text for kw in ['parado', 'fraco', 'caindo', 'perdendo', 'prejuizo']):
            lines.append("ALERTA: Dor ativa detectada - potencial alto!")
        if qual_data.get('socio') == 'tem_socio':
            lines.append("IMPORTANTE: Confirmar presenca do socio na reuniao!")

    progress = calculate_progress(qual_data)
    if progress == 4:
        lines.append("Acao: Lead OURO - ligar imediatamente, tem todos os dados")
    elif progress >= 2:
        lines.append("Acao: Lead quente - falta pouco, ser direto na qualificacao")
    else:
        lines.append("Acao: Lead morno - seguir SPIN, identificar dor e fazer doer")

    return "\n".join(lines) if lines else "Sem dados suficientes para insights"


# ===========================================
# INTENT DETECTION
# ===========================================

def detect_intent(message: str) -> str:
    """Detect message intent: 'interest', 'negative', 'question', 'neutral'"""
    message_lower = message.lower().strip()

    for keyword in NEGATIVE_KEYWORDS:
        if keyword in message_lower:
            return 'negative'

    interest_score = 0
    for keyword in INTEREST_KEYWORDS:
        if keyword in message_lower:
            interest_score += 1
    if interest_score >= 1:
        return 'interest'

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

SPIN_SYSTEM_PROMPT = """Voce e Joao, consultor comercial da Oduo Assessoria especializada em marketing digital para locadoras.

CONTEXTO DO LEAD:
- Nome: {name}
- Empresa: {company}
- Voce encontrou a empresa no Google e mandou mensagem perguntando sobre a frota deles.

METODOLOGIA SPIN (siga essa ordem conforme a conversa avanca):
1. SITUACAO: Entenda como funciona a operacao hoje. Pergunte sobre a frota, como conseguem clientes, se usam marketing digital.
2. PROBLEMA: Identifique dificuldades. Dependem de indicacao? Frota parada? Dificuldade em conseguir novos clientes?
3. IMPLICACAO: Mostre o impacto do problema. "Entao quando nao tem indicacao, a frota fica parada e voce perde dinheiro?"
4. NECESSIDADE: Guie para a solucao. "E se voce pudesse ter um fluxo constante de clientes sem depender de indicacao?"

REGRAS IMPORTANTES:
1. Seja BREVE - maximo 2-3 frases por resposta
2. Use o nome da pessoa quando possivel
3. Seja informal mas profissional (como um amigo que entende do assunto)
4. NUNCA invente dados - use apenas o que o lead te disser
5. Faca UMA pergunta por vez (nao bombardeie)
6. Se perguntarem como achou a empresa, diga "Vi a {company} no Google e achei interessante o negocio de voces"
7. Quando o lead demonstrar interesse na solucao, convide para uma reuniao rapida

LINK DE AGENDAMENTO: {booking_link}
(Envie APENAS quando o lead demonstrar interesse claro na solucao)

OBJETIVO: Entender as dores do lead usando SPIN e fechar uma reuniao de diagnostico gratuito.

TIPO DE MENSAGEM RECEBIDA: {intent}
{intent_instruction}
"""

INTENT_INSTRUCTIONS = {
    'interest': "O lead mostrou INTERESSE! Responda positivamente e envie o link de agendamento.",
    'negative': "O lead NAO tem interesse. Agradeca educadamente e se despeca. NAO insista.",
    'question': "O lead fez uma PERGUNTA. Responda usando o contexto disponivel.",
    'neutral': "Mensagem neutra. Faca uma pergunta para entender melhor o interesse."
}

SPIN_INTENT_INSTRUCTIONS = {
    'interest': "O lead mostrou INTERESSE! Convide para uma reuniao rapida de diagnostico e envie o link.",
    'negative': "O lead NAO tem interesse. Agradeca e se despeca. NAO insista.",
    'question': "O lead fez uma PERGUNTA. Responda e aproveite para avancar no SPIN.",
    'neutral': "Mensagem neutra. Avance no SPIN: se ainda nao perguntou sobre problemas, pergunte."
}

HIBRIDO_INTENT_INSTRUCTIONS = {
    'interest': "O lead mostrou INTERESSE! Se ja tem 4/4 dados, proponha reuniao. Senao, avance no SPIN e colete o que falta.",
    'negative': "O lead NAO tem interesse. Se ja tentou 2-3x, classifique como CURIOSO e encerre.",
    'question': "O lead fez uma PERGUNTA. Responda de forma CONSULTIVA e use a resposta pra avancar no SPIN.",
    'neutral': "Mensagem neutra. Avance no SPIN: identifique a DOR e faca ele SENTIR o prejuizo."
}


async def generate_ai_response(
    message: str,
    lead_context: Dict,
    intent: str,
    booking_link: str = None
) -> str:
    """Generate AI response. Selects prompt based on campaign_id."""
    if not booking_link:
        booking_link = CALENDAR_LINK

    client = get_openai_client()
    if not client:
        return generate_fallback_response(message, lead_context, intent, booking_link)

    campaign_id = lead_context.get('campaign_id', '')
    is_spin = campaign_id.startswith('cold_spin_') if campaign_id else False
    is_inbound = campaign_id.startswith('inbound_') if campaign_id else False

    if is_inbound:
        # Murilo SDR SPIN Selling for inbound leads
        qual_data = lead_context.get('qualification_data', {})
        if isinstance(qual_data, str):
            qual_data = json.loads(qual_data) if qual_data else {}
        progress = calculate_progress(qual_data)
        missing = get_missing_data(qual_data)
        phase = lead_context.get('phase', 'situacao')
        etapa = get_etapa_spin(phase, qual_data)

        missing_display = ", ".join(missing) if missing else "TODOS COLETADOS"

        system_prompt = FILTRO_HIBRIDO_PROMPT.format(
            nome_lead=lead_context.get('name', 'Nao perguntado ainda'),
            nome_locadora=qual_data.get('empresa', 'Nao perguntada ainda'),
            cidade=qual_data.get('cidade', 'Nao perguntada ainda'),
            dor_identificada=qual_data.get('dor', 'USE [I] IMPLICACAO - FACA DOER!'),
            faturamento=qual_data.get('faturamento', 'Nao qualificado ainda!'),
            tem_socio=qual_data.get('socio', 'Nao perguntado'),
            temperatura='quente' if progress >= 3 else ('morno' if progress >= 1 else 'frio'),
            qualification_progress=progress,
            missing_data=missing_display,
            etapa_spin=etapa,
            calendar_link=booking_link
        )
        intent_instruction = HIBRIDO_INTENT_INSTRUCTIONS.get(intent, '')
        system_prompt += f"\nTIPO DE MENSAGEM RECEBIDA: {intent}\n{intent_instruction}"

    elif is_spin:
        system_prompt = SPIN_SYSTEM_PROMPT.format(
            name=lead_context.get('name', 'Amigo'),
            company=lead_context.get('company', 'sua empresa'),
            booking_link=booking_link,
            intent=intent,
            intent_instruction=SPIN_INTENT_INSTRUCTIONS.get(intent, '')
        )
    else:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            name=lead_context.get('name', 'Amigo'),
            company=lead_context.get('company', 'sua empresa'),
            notes=lead_context.get('notes', 'crescer o negocio'),
            booking_link=booking_link,
            intent=intent,
            intent_instruction=INTENT_INSTRUCTIONS.get(intent, '')
        )

    try:
        messages = [{"role": "system", "content": system_prompt}]

        history = lead_context.get('conversation_history', [])
        if isinstance(history, str):
            history = json.loads(history)
        for msg in history[-10:]:
            role = "assistant" if msg.get('role') == 'bot' else "user"
            messages.append({"role": role, "content": msg.get('content', '')})

        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
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
    """Fallback response when OpenAI is not available."""
    name = lead_context.get('name', 'Amigo')
    campaign_id = lead_context.get('campaign_id', '')
    is_inbound = campaign_id.startswith('inbound_') if campaign_id else False

    if is_inbound:
        if intent == 'interest':
            return f"Show! Vou te passar o link pra agendar: {booking_link}\nEscolhe o melhor horario!"
        elif intent == 'negative':
            return "Entendi! Quando precisar, e so chamar. Sucesso!"
        else:
            return "E ai! Sou o Murilo da ODuo! Qual seu nome e qual locadora voce tem?"
    else:
        notes = lead_context.get('notes', 'crescer o negocio')
        if intent == 'interest':
            return f"Show {name}! Segue o link pra gente conversar: {booking_link}\nEscolhe o melhor horario!"
        elif intent == 'negative':
            return f"Entendo {name}, sem problemas! Sucesso ai!"
        elif intent == 'question':
            if any(word in message.lower() for word in ['numero', 'contato', 'conseguiu']):
                return f"Conversamos antes sobre {notes}, {name}. Voltei pra ver se faz sentido!"
            return f"Boa pergunta {name}! A gente ajuda empresarios a {notes}. Quer saber mais?"
        else:
            return f"E ai {name}, faz sentido pra sua situacao?"


# ===========================================
# API ENDPOINTS
# ===========================================

@router.post("/webhook")
async def receive_chatwoot_message(payload: dict):
    """Webhook endpoint to receive incoming messages from Chatwoot."""
    if payload.get('message_type') != 'incoming':
        return {"status": "ignored", "reason": "not incoming message"}
    if payload.get('event') != 'message_created':
        return {"status": "ignored", "reason": "not message_created event"}

    try:
        conversation = payload.get('conversation', {})
        contact_inbox = conversation.get('contact_inbox', {})
        phone = contact_inbox.get('source_id', '')
        message = payload.get('content', '')
        conversation_id = conversation.get('id')
        sender = payload.get('sender', {})
        sender_name = sender.get('name', '')

        if not phone or not message:
            return {"status": "error", "reason": "missing phone or message"}

    except Exception as e:
        return {"status": "error", "reason": f"payload parsing error: {e}"}

    result = await process_incoming_message(
        phone=phone,
        message=message,
        conversation_id=conversation_id,
        sender_name=sender_name
    )
    return result


@router.post("/process")
async def process_message_manual(incoming: IncomingMessage):
    """Process a message and generate AI response.
    Set auto_send=false when n8n handles sending."""
    return await process_incoming_message(
        phone=incoming.phone,
        message=incoming.message,
        conversation_id=incoming.conversation_id,
        auto_send=incoming.auto_send,
        sender_name=incoming.sender_name
    )


async def process_incoming_message(
    phone: str,
    message: str,
    conversation_id: Optional[int] = None,
    auto_send: bool = True,
    sender_name: Optional[str] = None
) -> Dict:
    """Process an incoming message and generate/send AI response."""
    # 1. Get lead context
    lead_context = await get_lead_context(phone)

    if not lead_context:
        # Auto-create inbound lead
        lead_context = await create_inbound_lead(phone, sender_name)
        if not lead_context:
            return {
                "status": "no_context",
                "phone": phone,
                "message": "Lead nao encontrado e nao foi possivel criar"
            }

    # 2. Detect intent
    intent = detect_intent(message)

    # 3. Determine if we should send link
    campaign_id = lead_context.get('campaign_id', '')
    is_inbound = campaign_id.startswith('inbound_') if campaign_id else False

    should_send_link = False
    if is_inbound:
        qual_data = lead_context.get('qualification_data', {})
        if isinstance(qual_data, str):
            qual_data = json.loads(qual_data) if qual_data else {}
        should_send_link = calculate_progress(qual_data) == 4
    else:
        should_send_link = intent == 'interest'

    # 4. Generate AI response
    ai_response = await generate_ai_response(
        message=message,
        lead_context=lead_context,
        intent=intent,
        booking_link=CALENDAR_LINK
    )

    # 5. Update lead status
    if is_inbound:
        status_map = {
            'interest': 'interessado',
            'negative': 'curioso',
            'question': 'em_conversa',
            'neutral': 'em_conversa'
        }
    else:
        status_map = {
            'interest': 'interessado',
            'negative': 'perdido',
            'question': 'em_conversa',
            'neutral': 'em_conversa'
        }
    await update_lead_status(phone, status_map.get(intent, 'em_conversa'))

    # 6. Send response if auto_send
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
            "notes": lead_context.get('notes'),
            "campaign_id": lead_context.get('campaign_id'),
            "phase": lead_context.get('phase', 'rapport'),
            "qualification_progress": lead_context.get('qualification_progress', 0)
        },
        "send_result": send_result
    }


@router.get("/test/{phone}")
async def test_lead_context(phone: str):
    """Test endpoint to check if we have context for a phone number"""
    context = await get_lead_context(phone)
    if context:
        return {"found": True, "context": context}
    return {"found": False, "message": f"No context found for {phone}"}


@router.post("/test-response")
async def test_ai_response(incoming: IncomingMessage):
    """Test AI response without sending."""
    return await process_incoming_message(
        phone=incoming.phone,
        message=incoming.message,
        auto_send=False,
        sender_name=incoming.sender_name
    )


# ===========================================
# QUALIFICATION ENDPOINT
# ===========================================

@router.post("/qualify")
async def qualify_lead_exchange(req: QualifyRequest):
    """
    Post-response qualification callback.
    Called by n8n AFTER sending the AI response.
    Extracts qualification data, calculates progress, generates insights.
    """
    # Save conversation exchange
    await save_conversation_exchange(req.phone, req.incoming_message, req.ai_response)

    # Get updated context
    context = await get_lead_context(req.phone)
    if not context:
        return {"status": "no_context", "phone": req.phone}

    history = context.get('conversation_history', [])
    if isinstance(history, str):
        history = json.loads(history)

    # Extract qualification data from full history
    existing_data = context.get('qualification_data', {})
    if isinstance(existing_data, str):
        existing_data = json.loads(existing_data) if existing_data else {}

    qual_data = extract_qualification_from_history(history, existing_data)
    progress = calculate_progress(qual_data)
    phase = determine_phase(history, qual_data, req.intent)

    # Generate insights for salesperson
    insights = generate_salesperson_insights(context, qual_data, history)

    # Update in database
    await update_qualification(req.phone, qual_data, progress, phase, insights)

    # Update status based on phase
    if phase == 'ouro':
        await update_lead_status(req.phone, 'qualificado')
    elif phase == 'curioso':
        await update_lead_status(req.phone, 'curioso')

    return {
        "status": "qualified",
        "phone": req.phone,
        "lead_name": context.get('name'),
        "company": context.get('company'),
        "campaign_id": context.get('campaign_id'),
        "intent": req.intent,
        "phase": phase,
        "qualification_progress": progress,
        "qualification_data": qual_data,
        "missing_data": get_missing_data(qual_data),
        "total_exchanges": len(history) // 2,
        "is_ouro": progress == 4,
        "should_send_calendar": progress == 4 and phase == 'ouro',
        "salesperson_insights": insights
    }


# ===========================================
# KANBAN ENDPOINT
# ===========================================

@router.get("/kanban")
async def get_kanban_data():
    """
    Get all leads organized for Kanban board.
    Returns leads grouped by pipeline status.
    """
    try:
        client = get_supabase_client()

        result = client.table('reactivation_leads').select(
            "phone, name, company, campaign_id, status, phase, "
            "qualification_data, qualification_progress, salesperson_insights, "
            "conversation_history, last_contact, created_at, updated_at"
        ).order('updated_at', desc=True).execute()

        if not result.data:
            return {"leads": [], "columns": _empty_kanban()}

        # Group leads by status/phase
        columns = {
            'novo': [],
            'em_conversa': [],
            'qualificado': [],
            'reuniao_agendada': [],
            'curioso': [],
            'perdido': []
        }

        all_leads = []
        for lead in result.data:
            # Parse JSON fields
            qual_data = lead.get('qualification_data', {})
            if isinstance(qual_data, str):
                qual_data = json.loads(qual_data) if qual_data else {}

            history = lead.get('conversation_history', [])
            if isinstance(history, str):
                history = json.loads(history) if history else []

            # Get last message
            last_msg = ''
            last_msg_time = ''
            if history:
                last_lead_msg = [m for m in history if m.get('role') == 'lead']
                if last_lead_msg:
                    last_msg = last_lead_msg[-1].get('content', '')[:100]
                    last_msg_time = last_lead_msg[-1].get('timestamp', '')

            lead_card = {
                'phone': lead.get('phone'),
                'name': lead.get('name', 'Lead'),
                'company': lead.get('company', ''),
                'campaign_id': lead.get('campaign_id', ''),
                'status': lead.get('status', 'novo'),
                'phase': lead.get('phase', 'rapport'),
                'qualification_progress': lead.get('qualification_progress', 0),
                'qualification_data': qual_data,
                'salesperson_insights': lead.get('salesperson_insights', ''),
                'total_exchanges': len(history) // 2,
                'last_message': last_msg,
                'last_message_time': last_msg_time,
                'last_contact': lead.get('last_contact'),
                'created_at': lead.get('created_at'),
                'updated_at': lead.get('updated_at')
            }

            all_leads.append(lead_card)

            # Map to column
            status = lead.get('status', 'novo')
            phase = lead.get('phase', '')

            if status == 'qualificado' or phase == 'ouro':
                columns['qualificado'].append(lead_card)
            elif status == 'reuniao_agendada':
                columns['reuniao_agendada'].append(lead_card)
            elif status == 'curioso' or phase == 'curioso':
                columns['curioso'].append(lead_card)
            elif status == 'perdido':
                columns['perdido'].append(lead_card)
            elif status in ('em_conversa', 'interessado'):
                columns['em_conversa'].append(lead_card)
            else:
                columns['novo'].append(lead_card)

        # Summary counts
        summary = {col: len(leads) for col, leads in columns.items()}
        summary['total'] = len(all_leads)

        return {
            "leads": all_leads,
            "columns": columns,
            "summary": summary
        }

    except Exception as e:
        print(f"Kanban error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _empty_kanban():
    return {
        'novo': [],
        'em_conversa': [],
        'qualificado': [],
        'reuniao_agendada': [],
        'curioso': [],
        'perdido': []
    }


@router.post("/kanban/move")
async def move_lead_status(phone: str, new_status: str):
    """Manually move a lead to a different Kanban column."""
    valid = ['novo', 'em_conversa', 'qualificado', 'reuniao_agendada', 'curioso', 'perdido']
    if new_status not in valid:
        raise HTTPException(status_code=400, detail=f"Status invalido. Use: {valid}")

    await update_lead_status(phone, new_status)
    return {"status": "updated", "phone": phone, "new_status": new_status}
