"""Prospecting module - Lead discovery and qualification"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple
from apify_client import ApifyClient

from backend.app.config import settings
from backend.app.models import LeadCreate, LeadStatus
from backend.app.integrations.supabase import lead_repository, cliente_repository
from backend.app.core.scoring import calculate_score, classify_hot_lead
from backend.app.integrations.tavily import check_digital_presence


def normalize_name(name: str) -> str:
    """Normalize company name for comparison (remove accents, lowercase)"""
    if not name:
        return ""
    # Remove accents
    normalized = unicodedata.normalize("NFD", str(name))
    normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    # Lowercase and clean whitespace
    return " ".join(normalized.lower().split())


def clean_phone(phone: str) -> Optional[str]:
    """Clean phone and ensure BR prefix (55)"""
    if not phone:
        return None
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) >= 10 and not digits.startswith("55"):
        digits = "55" + digits
    return digits if len(digits) >= 12 else None


def is_existing_client(nome_empresa: str) -> bool:
    """Check if company is already a client"""
    if not nome_empresa:
        return False

    nome_norm = normalize_name(nome_empresa)
    clientes = cliente_repository.find_all()

    for cliente in clientes:
        cliente_norm = cliente.get("nome_normalizado", "")

        # Exact match
        if nome_norm == cliente_norm:
            return True

        # Partial match (base name)
        nome_base = nome_norm.split(" - ")[0].split(" | ")[0].strip()
        cliente_base = cliente_norm.split(" - ")[0].split(" | ")[0].strip()

        if len(nome_base) > 5 and len(cliente_base) > 5:
            if nome_base in cliente_norm or cliente_base in nome_norm:
                return True

    return False


def determine_initial_status(lead_data: Dict) -> Tuple[Optional[LeadStatus], str]:
    """
    Determine initial status based on contact info.
    Returns (status, reason) or (None, reason) if should skip.
    """
    telefone = lead_data.get("telefone")
    site = lead_data.get("site")
    tem_telefone = telefone and len(re.sub(r"\D", "", str(telefone))) >= 10

    if tem_telefone:
        return LeadStatus.NOVO, "tem telefone"
    elif site:
        return LeadStatus.CONTATO_SITE, "apenas site"
    else:
        return None, "sem contato"


def calculate_need_priority(lead_data: Dict) -> int:
    """
    Calculate priority based on HOW MUCH the lead needs digital help.
    Higher = needs more help = better prospect for marketing services.

    Priority factors (higher = more need):
    - No website: +50 pts (huge need)
    - Low Google rating (<4.0): +20 pts (struggling business)
    - Few reviews (<20): +15 pts (low visibility)
    - Has phone (contactable): +10 pts
    """
    priority = 0

    # No website = highest need
    if not lead_data.get("site"):
        priority += 50

    # Low rating = struggling
    nota = lead_data.get("nota_google", 0) or 0
    if nota < 4.0:
        priority += 20
    elif nota < 4.5:
        priority += 10

    # Few reviews = low visibility
    reviews = lead_data.get("reviews_count", 0) or 0
    if reviews < 20:
        priority += 15
    elif reviews < 50:
        priority += 10

    # Has phone = can contact directly
    if lead_data.get("telefone"):
        priority += 10

    return priority


def prospect_google_maps(
    nicho: str,
    cidade: str,
    limite: int = 20,
    progress_callback=None
) -> Dict:
    """
    Prospect leads from Google Maps via Apify.

    IMPORTANT: Prioritizes leads that NEED digital marketing help the most:
    - No website (highest priority)
    - Low Google rating
    - Few reviews

    Args:
        nicho: Business niche to search
        cidade: City/State
        limite: Max leads to save
        progress_callback: Optional callback(progress_pct, message)

    Returns:
        Dict with statistics
    """
    stats = {
        "encontrados": 0,
        "salvos_telefone": 0,
        "salvos_site": 0,
        "ja_cliente": 0,
        "sem_contato": 0,
        "com_linkedin_ignorados": 0,
        "erros": 0
    }

    # Initialize Apify client
    client = ApifyClient(settings.apify_token)

    # Search for 5x limit to have good pool for prioritization
    run_input = {
        "searchStringsArray": [f"{nicho} em {cidade}"],
        "maxCrawledPlacesPerSearch": limite * 5,
        "language": "pt-BR",
        "onlyDataFromSearchPage": True,
    }

    if progress_callback:
        progress_callback(10, "Buscando no Google Maps...")

    # Run Apify actor
    run = client.actor("compass/crawler-google-places").call(run_input=run_input)
    items = client.dataset(run["defaultDatasetId"]).list_items().items

    stats["encontrados"] = len(items)

    if progress_callback:
        progress_callback(30, f"Encontrados {len(items)} resultados. Analisando necessidade...")

    # STEP 1: Process all items and calculate need priority
    qualified_leads = []

    for item in items:
        nome_empresa = item.get("title")

        # Skip leads without name
        if not nome_empresa or len(nome_empresa.strip()) < 3:
            stats["sem_contato"] += 1
            continue

        # Skip existing clients
        if is_existing_client(nome_empresa):
            stats["ja_cliente"] += 1
            continue

        # Extract lead data
        telefone = clean_phone(item.get("phoneUnformatted"))
        site = item.get("website")
        nota = item.get("totalScore", 0) or 0
        reviews = item.get("reviewsCount", 0) or 0

        lead_data = {
            "nome_empresa": nome_empresa,
            "telefone": telefone,
            "site": site,
            "endereco": item.get("address"),
            "cidade": cidade,
            "nota_google": nota,
            "nicho": nicho,
            "metadata": item,
            "reviews_count": reviews
        }

        # Determine status
        status, reason = determine_initial_status(lead_data)

        if status is None:
            stats["sem_contato"] += 1
            continue

        # Calculate scores
        score_result = calculate_score(
            nota_google=nota,
            tem_telefone=bool(telefone),
            tem_site=bool(site),
            reviews_count=reviews
        )

        # Calculate need priority (higher = needs more help)
        need_priority = calculate_need_priority(lead_data)

        qualified_leads.append({
            "data": lead_data,
            "status": status,
            "score": score_result["score"],
            "need_priority": need_priority
        })

    if progress_callback:
        progress_callback(50, f"{len(qualified_leads)} leads qualificados. Verificando presenca digital...")

    # STEP 2: Sort by need priority (highest first = needs most help)
    qualified_leads.sort(key=lambda x: (-x["need_priority"], -x["score"]))

    # STEP 3: Check digital presence for top candidates (only if Tavily available)
    check_count = min(limite * 2, len(qualified_leads))
    for i, lead_info in enumerate(qualified_leads[:check_count]):
        nome = lead_info["data"].get("nome_empresa", "")
        cidade_lead = lead_info["data"].get("cidade", "")

        try:
            presence = check_digital_presence(nome, cidade_lead)

            # Store presence info
            lead_info["digital_presence"] = presence

            # BONUS for leads with digital presence (they UNDERSTAND digital = likely buyers)
            if presence.get("has_linkedin"):
                lead_info["need_priority"] += 25  # Has LinkedIn = understands digital marketing
            if presence.get("has_instagram"):
                lead_info["need_priority"] += 15  # Has Instagram = active online
            if presence.get("has_facebook"):
                lead_info["need_priority"] += 10  # Has Facebook = online presence

        except Exception:
            pass  # Skip on error, keep original priority

        if progress_callback:
            pct = 50 + int((i / check_count) * 20)
            progress_callback(pct, f"Verificando presenca digital {i+1}/{check_count}...")

    # STEP 4: Re-sort after digital presence penalty
    qualified_leads.sort(key=lambda x: (-x["need_priority"], -x["score"]))

    if progress_callback:
        progress_callback(75, f"Salvando {limite} melhores leads...")

    # STEP 5: Save top 'limite' leads
    saved_count = 0
    for i, lead_info in enumerate(qualified_leads[:limite]):
        lead_data = lead_info["data"]
        status = lead_info["status"]
        score = lead_info["score"]

        try:
            # Remove temporary field
            lead_data.pop("reviews_count", None)

            # Add digital presence info to metadata
            if lead_info.get("digital_presence"):
                metadata = lead_data.get("metadata", {}) or {}
                metadata["digital_presence"] = lead_info["digital_presence"]
                lead_data["metadata"] = metadata

            lead = LeadCreate(**lead_data)
            lead_repository.upsert(lead, score, status)

            if status == LeadStatus.NOVO:
                stats["salvos_telefone"] += 1
            else:
                stats["salvos_site"] += 1

            saved_count += 1
        except Exception:
            stats["erros"] += 1

        # Progress update
        if progress_callback:
            pct = 75 + int((i / min(limite, len(qualified_leads))) * 20)
            progress_callback(pct, f"Salvando {i+1}/{min(limite, len(qualified_leads))} melhores leads")

    if progress_callback:
        no_site_count = sum(1 for l in qualified_leads[:saved_count] if not l["data"].get("site"))
        no_linkedin = sum(1 for l in qualified_leads[:saved_count] if not l.get("digital_presence", {}).get("has_linkedin"))
        progress_callback(100, f"Concluido! {no_site_count} sem site, {no_linkedin} sem LinkedIn")

    return stats
