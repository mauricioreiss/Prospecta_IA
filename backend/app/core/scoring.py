"""Lead Scoring - Calculate and classify lead potential"""
from typing import Dict, Tuple
from backend.app.models import Temperatura


def calculate_score(
    nota_google: float = 0,
    tem_telefone: bool = False,
    tem_site: bool = False,
    reviews_count: int = 0,
    nicho_peso: int = 0
) -> Dict:
    """
    Calculate lead prospecting score (0-100).

    LOGIC: Higher score = NEEDS MORE HELP = HOTTER LEAD

    Scoring breakdown:
    - No website: +50 pts (huge need for digital presence)
    - Low rating (<4.5): +50 pts (can improve reputation)
    - Few reviews (<20): +15 pts (low visibility)
    - Few reviews (<50): +10 pts (medium visibility)
    - Has phone: +10 pts (direct contact possible)

    Returns dict with score, temperatura, breakdown
    """
    breakdown = {}

    # Ensure values are not None
    nota_google = nota_google or 0
    reviews_count = reviews_count or 0

    # NO WEBSITE = +50 pts (highest need - no digital presence)
    if not tem_site:
        pts_site = 50
        breakdown["sem_site"] = "+50 (precisa de presenca digital)"
    else:
        pts_site = 0
        breakdown["tem_site"] = "0 (ja tem site)"

    # LOW RATING = +50 pts (can improve reputation)
    if nota_google == 0:
        pts_rating = 30  # No rating yet
        breakdown["sem_nota"] = "+30 (sem avaliacao ainda)"
    elif nota_google < 4.0:
        pts_rating = 50  # Bad rating - urgent need
        breakdown["nota_baixa"] = f"+50 (nota {nota_google} - pode melhorar)"
    elif nota_google < 4.5:
        pts_rating = 30  # Medium rating - room to improve
        breakdown["nota_media"] = f"+30 (nota {nota_google} - margem para melhorar)"
    else:
        pts_rating = 0  # Good rating
        breakdown["nota_boa"] = f"0 (nota {nota_google} - ja esta boa)"

    # FEW REVIEWS = needs visibility
    if reviews_count < 20:
        pts_reviews = 15
        breakdown["poucos_reviews"] = f"+15 ({reviews_count} reviews - baixa visibilidade)"
    elif reviews_count < 50:
        pts_reviews = 10
        breakdown["reviews_medio"] = f"+10 ({reviews_count} reviews - visibilidade media)"
    else:
        pts_reviews = 0
        breakdown["reviews_ok"] = f"0 ({reviews_count} reviews - boa visibilidade)"

    # HAS PHONE = +10 pts (can contact directly)
    if tem_telefone:
        pts_phone = 10
        breakdown["tem_telefone"] = "+10 (contato direto)"
    else:
        pts_phone = 0
        breakdown["sem_telefone"] = "0 (sem telefone)"

    # Total score (max ~125, normalize to 100)
    raw_score = pts_site + pts_rating + pts_reviews + pts_phone
    score = min(raw_score, 100)

    # Temperature classification (based on NEED)
    # Higher score = hotter (needs more help)
    if score >= 70:
        temp = {"nivel": "quente", "label": "Quente", "cor": "#e53e3e"}  # Red - hot!
    elif score >= 40:
        temp = {"nivel": "morno", "label": "Morno", "cor": "#d69e2e"}  # Yellow/orange
    else:
        temp = {"nivel": "frio", "label": "Frio", "cor": "#4299e1"}  # Blue - cold

    return {
        "score": round(score, 1),
        "temperatura": temp,
        "breakdown": breakdown
    }


def classify_hot_lead(
    has_website: bool,
    rating: float,
    reviews_count: int = 0
) -> Tuple[str, str, int]:
    """
    Classify lead for marketing priority.

    Key rule: No website + rating < 4.0 = Hot Marketing Lead
    (Company needs digital presence urgently)

    Returns (status, reason, bonus_score)
    """
    if not has_website and rating < 4.0:
        return (
            "lead_quente_marketing",
            "Empresa sem site e nota abaixo de 4.0 - alta necessidade de presenca digital",
            25
        )

    if not has_website and rating >= 4.0:
        return (
            "novo",
            "Empresa sem site mas bem avaliada - potencial de crescimento",
            15
        )

    if has_website and rating < 3.5:
        return (
            "novo",
            "Empresa com site mas mal avaliada - pode precisar de suporte",
            10
        )

    if has_website and rating >= 4.0:
        return (
            "novo",
            "Empresa estabelecida com boa presenca",
            5
        )

    return ("novo", "Lead padrao", 0)


def prioritize_leads(leads: list) -> list:
    """
    Sort leads by contact priority.

    Priority order:
    1. Hot marketing leads (no site + low rating)
    2. High score (>=80)
    3. Has phone + medium score (60-79)
    4. Medium score (60-79)
    5. Has phone
    6. Rest
    """
    def get_priority(lead):
        if lead.get("status") == "lead_quente_marketing":
            return (0, -lead.get("score", 0))

        score = lead.get("score", 0)
        has_phone = bool(lead.get("telefone"))

        if score >= 80:
            return (1, -score)
        if has_phone and score >= 60:
            return (2, -score)
        if score >= 60:
            return (3, -score)
        if has_phone:
            return (4, -score)
        return (5, -score)

    return sorted(leads, key=get_priority)
