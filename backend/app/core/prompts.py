"""
Senior Consultant Prompts - Business-focused language
Avoid tech jargon, use business terminology
"""
from typing import Dict, Optional

# Business terminology translations
BUSINESS_TERMS = {
    "seo": "visibilidade no mercado",
    "lead": "oportunidade de negocio",
    "landing_page": "pagina de captacao",
    "funil": "jornada do cliente",
    "conversao": "fechamento",
    "churn": "perda de clientes",
    "roi": "retorno sobre investimento",
    "follow_up": "acompanhamento",
    "estoque_ocioso": "patrimonio parado",
    "score": "potencial de conversao"
}


NICHE_CONFIG = {
    "locadora": {
        "nome": "Locadora de Equipamentos",
        "dor_principal": "patrimonio parado gerando custo",
        "dores": [
            "maquinas ociosas sem gerar receita",
            "clientes nao encontram equipamentos disponiveis",
            "controle manual de disponibilidade",
            "perda de oportunidades por resposta lenta"
        ],
        "solucao": "visibilidade de mercado e gestao de disponibilidade",
        "perguntas": [
            "Quantos equipamentos voces tem no parque hoje?",
            "Como controlam a disponibilidade - planilha, sistema?",
            "Qual o tempo medio que uma maquina fica parada entre locacoes?"
        ]
    },
    "autopecas": {
        "nome": "Auto Pecas",
        "dor_principal": "cliente que vai pro concorrente",
        "dores": [
            "cliente nao encontra a peca online",
            "balconista sobrecarregado com consultas",
            "perda de vendas por falta de resposta rapida"
        ],
        "solucao": "catalogo digital com busca inteligente",
        "perguntas": [
            "Quantas consultas de peca voces recebem por dia?",
            "O cliente consegue ver online se a peca tem em estoque?",
            "Qual porcentagem de clientes desiste esperando resposta?"
        ]
    },
    "oficina": {
        "nome": "Oficina Mecanica",
        "dor_principal": "cliente que nao volta",
        "dores": [
            "sem agendamento online",
            "cliente esquece de retornar para manutencao",
            "orcamento demorado espanta cliente"
        ],
        "solucao": "agendamento e acompanhamento automatico",
        "perguntas": [
            "Quantos carros atendem por semana em media?",
            "O cliente consegue agendar online?",
            "Voces fazem lembrete de revisao periodica?"
        ]
    },
    "clinica": {
        "nome": "Clinica/Consultorio",
        "dor_principal": "agenda com buracos",
        "dores": [
            "faltas e cancelamentos de ultima hora",
            "paciente nao retorna para acompanhamento",
            "dificuldade de ser encontrado online"
        ],
        "solucao": "agendamento com lembrete e acompanhamento",
        "perguntas": [
            "Quantas consultas por semana em media?",
            "Qual a taxa de faltas e cancelamentos?",
            "Os pacientes conseguem agendar online?"
        ]
    },
    "restaurante": {
        "nome": "Restaurante",
        "dor_principal": "mesa vazia no horario de pico",
        "dores": [
            "cliente nao encontra cardapio online",
            "pedidos por telefone geram erro",
            "fila espanta cliente"
        ],
        "solucao": "cardapio digital e reserva online",
        "perguntas": [
            "Voces tem cardapio digital ou so impresso?",
            "O cliente consegue fazer pedido online?",
            "Quantas mesas perdem por fila no horario de pico?"
        ]
    },
    "generico": {
        "nome": "Empresa",
        "dor_principal": "falta de presenca digital",
        "dores": [
            "cliente nao encontra a empresa online",
            "sem forma de contato rapida",
            "concorrente mais visivel na internet"
        ],
        "solucao": "presenca digital profissional",
        "perguntas": [
            "Como os clientes encontram voces hoje?",
            "Voces tem site ou usam so redes sociais?",
            "Qual o principal canal de atendimento?"
        ]
    }
}


SENIOR_CONSULTANT_PERSONA = """Voce e Alex, um Consultor Senior de Desenvolvimento de Negocios com 15 anos de experiencia.

POSTURA:
- Profissional e respeitoso, nunca informal demais
- Consultor, nao vendedor - identifica problemas antes de propor solucoes
- Direto e objetivo - respeita o tempo do empresario
- Empatico com os desafios de quem administra um negocio

LINGUAGEM:
- Use "senhor/senhora" ate ser convidado a ser informal
- Evite jargoes tecnicos - traduza para termos de negocio
- Frases curtas e claras
- Perguntas abertas para entender a situacao

ESTRUTURA DA CONVERSA:
1. Apresentacao breve (quem voce e, por que esta ligando)
2. Gancho personalizado (noticia recente ou observacao especifica)
3. Pergunta de diagnostico (identificar dor)
4. Escuta ativa (deixe o empresario falar)
5. Proposta de valor conectada a dor identificada
6. Proximo passo claro (agendamento)

NUNCA:
- Pressione por decisao imediata
- Use termos como "promocao imperdivel" ou "ultima chance"
- Interrompa o cliente
- Fale mal de concorrentes"""


def get_niche_config(nicho: str) -> Dict:
    """Get configuration for a niche"""
    return NICHE_CONFIG.get(nicho.lower(), NICHE_CONFIG["generico"])


def build_system_prompt(nicho: str, lead_info: Optional[Dict] = None) -> str:
    """
    Build complete system prompt for AI calls.

    Args:
        nicho: Business niche
        lead_info: Optional lead details for personalization
    """
    config = get_niche_config(nicho)

    prompt = f"""{SENIOR_CONSULTANT_PERSONA}

CONTEXTO DO NICHO - {config['nome']}:
- Principal dor do mercado: {config['dor_principal']}
- Problemas comuns: {', '.join(config['dores'][:3])}
- Nossa solucao: {config['solucao']}

PERGUNTAS DE QUALIFICACAO:
{chr(10).join([f'- {p}' for p in config['perguntas']])}

LINGUAGEM DE NEGOCIOS (use estes termos):
{chr(10).join([f'- Em vez de "{k}", diga "{v}"' for k, v in BUSINESS_TERMS.items()])}
"""

    if lead_info:
        empresa = lead_info.get("nome_empresa", "a empresa")
        prompt += f"""
INFORMACOES DO LEAD:
- Empresa: {empresa}
- Cidade: {lead_info.get('cidade', 'N/A')}
- Nota Google: {lead_info.get('nota_google', 'N/A')}
- Tem site: {'Sim' if lead_info.get('site') else 'Nao'}
"""

    return prompt


def build_opening_script(
    nicho: str,
    lead_info: Dict,
    icebreaker: Optional[str] = None
) -> str:
    """
    Build opening script for call.

    Args:
        nicho: Business niche
        lead_info: Lead details
        icebreaker: Optional personalized hook from Tavily
    """
    config = get_niche_config(nicho)
    empresa = lead_info.get("nome_empresa", "sua empresa")

    if icebreaker:
        gancho = icebreaker
    else:
        # Fallback based on lead data
        if not lead_info.get("site"):
            gancho = f"Vi que a {empresa} tem boas avaliacoes mas nao tem site proprio"
        else:
            gancho = f"Estou conversando com empresas de {config['nome']} na regiao"

    script = f"""ABERTURA:

"Bom dia/tarde! Meu nome e Alex, sou consultor da Oduo Assessoria.
Estou falando com o responsavel da {empresa}?"

[AGUARDAR RESPOSTA - pausa de 2 segundos]

"Perfeito! {gancho}.

Posso tomar 2 minutinhos do seu tempo para uma pergunta rapida?"

[SE SIM - fazer primeira pergunta de qualificacao]
"{config['perguntas'][0]}"

[SE NAO - encerrar educadamente]
"Entendo, sem problemas. Qual seria um melhor horario para conversarmos?"
"""

    return script


def translate_term(tech_term: str) -> str:
    """Translate tech term to business language"""
    return BUSINESS_TERMS.get(tech_term.lower(), tech_term)
