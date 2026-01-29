"""
Integracao com OpenAI - Analise e Geracao de Conteudo
Preparado para OpenAI Realtime API (futuro)
"""
from typing import Optional
from openai import OpenAI

from backend.app.config import get_settings
from backend.app.core.prompts import build_system_prompt

settings = get_settings()

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """Retorna cliente OpenAI singleton"""
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


async def generate_response(
    lead: dict,
    message: str,
    history: list[dict] = None,
    icebreaker: str = None,
    nicho: str = None
) -> str:
    """
    Gera resposta usando GPT-4 com contexto do lead

    Args:
        lead: Dados do lead
        message: Mensagem recebida
        history: Historico de interacoes
        icebreaker: Gancho personalizado do Tavily
        nicho: Nicho do negocio

    Returns:
        Resposta gerada
    """
    client = get_client()

    # Constroi contexto
    lead_context = {
        "nome_empresa": lead.get("nome_empresa"),
        "cidade": lead.get("cidade"),
        "rating": lead.get("rating"),
        "reviews_count": lead.get("reviews_count"),
        "site_url": lead.get("site_url"),
    }

    system_prompt = build_system_prompt(
        nicho=nicho or settings.nicho_padrao,
        lead_context=lead_context
    )

    if icebreaker:
        system_prompt += f"\n\nGANCHO PERSONALIZADO (use na abertura): {icebreaker}"

    # Monta mensagens
    messages = [{"role": "system", "content": system_prompt}]

    # Adiciona historico
    if history:
        for interaction in history[-10:]:  # Ultimas 10 interacoes
            role = "assistant" if interaction.get("tipo", "").endswith("_out") else "user"
            messages.append({
                "role": role,
                "content": interaction.get("resumo_conversa", "")
            })

    # Adiciona mensagem atual
    messages.append({"role": "user", "content": message})

    # Gera resposta
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
        max_tokens=500
    )

    return response.choices[0].message.content


def _clean_notes_regex(raw_notes: str) -> str:
    """
    Limpeza básica com regex - remove instruções internas do CRM.
    Fallback quando a IA não funciona.
    """
    import re

    text = raw_notes.strip()

    # Padrões a remover (instruções internas)
    patterns_to_remove = [
        r',?\s*chamar\s+daqui\s+\d+\s*(meses?|dias?|semanas?)',
        r',?\s*ligar\s+(em|daqui)\s+\w+',
        r',?\s*retornar\s+(em|Q\d|daqui)\s*\w*',
        r',?\s*voltar\s+a\s+ligar',
        r',?\s*agendar\s+para\s+\w+',
        r',?\s*lembrar\s+de\s+\w+',
        r'\s*-\s*$',  # traço no final
    ]

    for pattern in patterns_to_remove:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    text = text.strip(' ,.-')

    # Se ficou muito curto ou vazio, usa fallback
    if len(text) < 5:
        return "queria crescer o negócio"

    # Deixa primeira letra minúscula para encaixar depois de "Vi que você"
    if text and text[0].isupper():
        text = text[0].lower() + text[1:]

    return text


def clean_notes_for_message(raw_notes: str) -> str:
    """
    Limpa anotações de CRM para usar em mensagem.

    Usa IA para transformar em frase conversacional.
    Se IA falhar, usa limpeza com regex.

    Exemplo:
    - Input: "Fechou com outra empresa, chamar daqui 6 meses"
    - Output: "fechou com outra empresa na época"
    """
    if not raw_notes or len(raw_notes.strip()) < 3:
        return "queria crescer o negócio"

    # Primeiro tenta limpeza com regex (rápido e confiável)
    cleaned_basic = _clean_notes_regex(raw_notes)

    # Tenta IA para resultado mais natural
    try:
        client = get_client()

        prompt = f"""Resuma esta anotação de CRM em UMA frase curta (máx 6 palavras).
REMOVA completamente: datas, prazos, "chamar daqui X meses", "ligar em", instruções internas.
Mantenha APENAS o que aconteceu com o cliente.

ANOTAÇÃO: "{raw_notes}"

EXEMPLOS:
- "Fechou com outra empresa, chamar daqui 6 meses" → fechou com outra empresa
- "Sem budget agora, retornar Q1 2025" → estava sem orçamento
- "Precisa de mais clientes" → precisava de mais clientes
- "Nao tinha interesse" → não tinha interesse na época
- "Site ruim" → queria melhorar o site

Responda APENAS a frase, sem explicações."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você resume anotações de CRM em frases curtas. Nunca inclua datas ou instruções como 'chamar daqui X meses'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=30
        )

        result = response.choices[0].message.content.strip()
        result = result.strip('"\'')

        # Valida resultado da IA
        if len(result) < 3 or len(result) > 60:
            print(f"[clean_notes] IA retornou inválido, usando regex: {result}")
            return cleaned_basic

        # Verifica se a IA não deixou instruções internas
        bad_words = ['chamar', 'ligar', 'retornar', 'daqui', 'meses', 'semana']
        if any(word in result.lower() for word in bad_words):
            print(f"[clean_notes] IA deixou instrução, usando regex: {result}")
            return cleaned_basic

        # Deixa primeira letra minúscula
        if result and result[0].isupper():
            result = result[0].lower() + result[1:]

        print(f"[clean_notes] '{raw_notes[:30]}...' → '{result}'")
        return result

    except Exception as e:
        print(f"[clean_notes] Erro IA, usando regex: {e}")
        return cleaned_basic


async def clean_notes_batch(notes_list: list[str]) -> list[str]:
    """
    Limpa várias notas de uma vez (para preview/bulk).
    Usa processamento em batch para eficiência.
    """
    cleaned = []
    for notes in notes_list:
        cleaned.append(clean_notes_for_message(notes))
    return cleaned


def analyze_website(url: str, company_name: str) -> dict:
    """
    Analisa site e extrai informacoes relevantes

    Returns:
        Dict com segmento, pontos falhos, score ajustado
    """
    client = get_client()

    prompt = f"""
Analise o site {url} da empresa "{company_name}" e retorne um JSON com:

1. segmento: categoria do negocio (ex: locadora, autopecas, oficina)
2. pontos_falhos: lista de oportunidades de melhoria no site
3. maquinas_detectadas: lista de produtos/equipamentos encontrados
4. resumo: descricao em 2-3 frases do negocio
5. score_ajustado: nota de 0-100 baseado na qualidade do site

Retorne APENAS o JSON, sem markdown.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Voce e um analista de marketing digital."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )

    import json
    try:
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {
            "segmento": "nao_identificado",
            "pontos_falhos": [],
            "maquinas_detectadas": [],
            "resumo": "Analise nao disponivel",
            "score_ajustado": 50
        }


# ===========================================
# PREPARACAO PARA OPENAI REALTIME API
# ===========================================

class RealtimeSession:
    """
    Placeholder para futura integracao com OpenAI Realtime API
    Sera usado para chamadas de voz em tempo real
    """

    def __init__(self, lead_id: str, nicho: str):
        self.lead_id = lead_id
        self.nicho = nicho
        self.session_id = None
        self.is_active = False

    async def start(self):
        """Inicia sessao de voz em tempo real (futuro)"""
        # TODO: Implementar quando OpenAI Realtime API estiver disponivel
        raise NotImplementedError("OpenAI Realtime API ainda nao implementado")

    async def stop(self):
        """Encerra sessao"""
        self.is_active = False

    async def send_audio(self, audio_chunk: bytes):
        """Envia chunk de audio para processamento (futuro)"""
        raise NotImplementedError("OpenAI Realtime API ainda nao implementado")
