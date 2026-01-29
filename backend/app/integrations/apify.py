"""
Integracao com Apify - Google Maps Scraper
"""
from apify_client import ApifyClient
from typing import Optional

from app.config import get_settings

settings = get_settings()

_client: Optional[ApifyClient] = None


def get_client() -> ApifyClient:
    """Retorna cliente Apify singleton"""
    global _client
    if _client is None:
        _client = ApifyClient(settings.apify_token)
    return _client


def search_google_maps(
    search_term: str,
    city: str,
    max_results: int = 60
) -> list[dict]:
    """
    Busca empresas no Google Maps via Apify

    Args:
        search_term: Termo de busca (ex: "locadora de maquinas")
        city: Cidade e estado (ex: "Sumare, SP")
        max_results: Numero maximo de resultados (busca 3x para filtrar)

    Returns:
        Lista de empresas com dados do Google Maps
    """
    client = get_client()

    run_input = {
        "searchStringsArray": [f"{search_term} em {city}"],
        "maxCrawledPlacesPerSearch": max_results,
        "language": "pt-BR",
        "onlyDataFromSearchPage": True,
    }

    run = client.actor("compass/crawler-google-places").call(run_input=run_input)
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items

    # Normaliza dados
    results = []
    for item in dataset_items:
        results.append({
            "nome_empresa": item.get("title"),
            "telefone_raw": item.get("phoneUnformatted"),
            "telefone": item.get("phone"),
            "site_url": item.get("website"),
            "endereco": item.get("address"),
            "rating": item.get("totalScore"),
            "reviews_count": item.get("reviewsCount", 0),
            "categoria": item.get("categoryName"),
            "google_url": item.get("url"),
            "latitude": item.get("location", {}).get("lat"),
            "longitude": item.get("location", {}).get("lng"),
        })

    return results


async def search_google_maps_async(
    search_term: str,
    city: str,
    max_results: int = 60
) -> list[dict]:
    """Versao async (executa em thread pool)"""
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: search_google_maps(search_term, city, max_results)
    )
