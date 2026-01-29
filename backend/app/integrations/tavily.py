"""Tavily integration - Real-time company research for icebreakers"""
from typing import Optional, Dict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from backend.app.config import settings

# Tavily import with fallback
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    TavilyClient = None


def _get_client() -> Optional['TavilyClient']:
    """Get Tavily client if configured"""
    if not TAVILY_AVAILABLE or not settings.tavily_api_key:
        return None
    return TavilyClient(api_key=settings.tavily_api_key)


def search_company(
    nome_empresa: str,
    cidade: Optional[str] = None,
    timeout_seconds: float = 2.0
) -> Dict:
    """
    Search for recent news/info about company.
    Returns icebreaker hook if found.

    Args:
        nome_empresa: Company name
        cidade: City for context (optional)
        timeout_seconds: Max wait time (default 2s for fast UX)

    Returns:
        Dict with:
        - found: bool
        - icebreaker: str - ready-to-use opening line
        - news: list - recent news items
        - search_time_ms: int
    """
    result = {
        "found": False,
        "icebreaker": None,
        "news": [],
        "search_time_ms": 0,
        "error": None
    }

    client = _get_client()
    if not client:
        result["error"] = "Tavily not configured"
        return result

    # Build query
    query = f'"{nome_empresa}"'
    if cidade:
        query += f" {cidade}"

    start = datetime.now()

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                client.search,
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=False,
                include_raw_content=False
            )

            try:
                response = future.result(timeout=timeout_seconds)
            except FuturesTimeoutError:
                result["error"] = f"Timeout ({timeout_seconds}s)"
                result["search_time_ms"] = int(timeout_seconds * 1000)
                return result

    except Exception as e:
        result["error"] = str(e)
        result["search_time_ms"] = int((datetime.now() - start).total_seconds() * 1000)
        return result

    result["search_time_ms"] = int((datetime.now() - start).total_seconds() * 1000)

    if not response or "results" not in response:
        return result

    # Filter recent news (last 30 days)
    cutoff = datetime.now() - timedelta(days=30)
    nome_lower = nome_empresa.lower()

    for item in response.get("results", []):
        title = item.get("title", "")
        content = item.get("content", "")

        # Check if mentions company
        if nome_lower not in title.lower() and nome_lower not in content.lower():
            continue

        result["news"].append({
            "title": title[:100],
            "summary": content[:200] if content else "",
            "url": item.get("url", "")
        })

    result["found"] = len(result["news"]) > 0

    # Generate icebreaker if found news
    if result["news"]:
        result["icebreaker"] = _generate_icebreaker(nome_empresa, result["news"][0])

    return result


def _generate_icebreaker(nome_empresa: str, news: Dict) -> str:
    """Generate natural opening line from news"""
    title = news.get("title", "").lower()
    summary = news.get("summary", "").lower()
    text = title + " " + summary

    # Expansion/Growth
    if any(w in text for w in ["expans", "inaugur", "novo", "cresc", "amplia"]):
        return f"Vi que a {nome_empresa} esta em expansao - parabens pelo crescimento!"

    # Award/Recognition
    if any(w in text for w in ["premi", "reconhec", "award", "melhor", "destaque"]):
        return f"Vi que a {nome_empresa} recebeu um reconhecimento recentemente - muito bom!"

    # Event/Fair
    if any(w in text for w in ["feira", "evento", "particip", "exposic"]):
        return f"Vi que a {nome_empresa} participou de um evento recentemente - como foi?"

    # Hiring
    if any(w in text for w in ["contrat", "equipe", "vagas", "emprego"]):
        return f"Vi que a {nome_empresa} esta crescendo a equipe - momento bom!"

    # Launch/Product
    if any(w in text for w in ["lanc", "produto", "servic", "novidade"]):
        return f"Vi que a {nome_empresa} lancou uma novidade recentemente - interessante!"

    # Generic fallback
    return f"Estava pesquisando sobre a {nome_empresa} e vi que voces estao ativos no mercado"


def check_digital_presence(
    nome_empresa: str,
    cidade: Optional[str] = None,
    timeout_seconds: float = 1.5
) -> Dict:
    """
    Quick check for digital presence (LinkedIn, Instagram, Facebook).

    Returns:
        Dict with:
        - has_linkedin: bool
        - has_instagram: bool
        - has_facebook: bool
        - presence_score: int (0-100, higher = stronger presence)
        - details: list of found profiles
    """
    result = {
        "has_linkedin": False,
        "has_instagram": False,
        "has_facebook": False,
        "presence_score": 0,
        "details": [],
        "error": None
    }

    client = _get_client()
    if not client:
        result["error"] = "Tavily not configured"
        return result

    # Search for company + social media
    query = f'"{nome_empresa}" linkedin OR instagram OR facebook'
    if cidade:
        query += f" {cidade}"

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                client.search,
                query=query,
                search_depth="basic",
                max_results=5,
                include_answer=False,
                include_raw_content=False
            )

            try:
                response = future.result(timeout=timeout_seconds)
            except FuturesTimeoutError:
                result["error"] = f"Timeout ({timeout_seconds}s)"
                return result

    except Exception as e:
        result["error"] = str(e)
        return result

    if not response or "results" not in response:
        return result

    nome_lower = nome_empresa.lower()

    for item in response.get("results", []):
        url = item.get("url", "").lower()
        title = item.get("title", "").lower()

        # Check if mentions the company
        if nome_lower not in title and nome_lower not in url:
            continue

        if "linkedin.com" in url:
            result["has_linkedin"] = True
            result["details"].append(f"LinkedIn: {item.get('url', '')[:80]}")
            result["presence_score"] += 40

        elif "instagram.com" in url:
            result["has_instagram"] = True
            result["details"].append(f"Instagram: {item.get('url', '')[:80]}")
            result["presence_score"] += 30

        elif "facebook.com" in url:
            result["has_facebook"] = True
            result["details"].append(f"Facebook: {item.get('url', '')[:80]}")
            result["presence_score"] += 20

    result["presence_score"] = min(result["presence_score"], 100)
    return result


def get_icebreaker_for_lead(lead: Dict) -> Optional[str]:
    """
    Get icebreaker for a lead, with fallback messages.
    Returns ready-to-use opening line.
    """
    nome = lead.get("nome_empresa")
    cidade = lead.get("cidade")
    site = lead.get("site")
    nota = lead.get("nota_google", 0)

    if not nome:
        return None

    # Try Tavily first
    result = search_company(nome, cidade)
    if result["found"] and result["icebreaker"]:
        return result["icebreaker"]

    # Fallback: No website
    if not site:
        return f"Notei que a {nome} tem boas avaliacoes, mas nao encontrei um site proprio. Isso e intencional?"

    # Fallback: Low rating
    if nota and nota < 4.0:
        return f"Vi que a {nome} tem {nota} estrelas no Google. Voces tem trabalhado na reputacao online?"

    # Generic fallback
    return f"Estou entrando em contato com empresas do segmento na regiao de {cidade}."
