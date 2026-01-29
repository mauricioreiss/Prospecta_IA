"""API Dependencies - Shared dependency injection"""
from typing import Generator
from backend.app.integrations.supabase import (
    LeadRepository, ClienteExistenteRepository,
    lead_repository, cliente_repository
)


def get_lead_repo() -> LeadRepository:
    """Dependency for lead repository"""
    return lead_repository


def get_cliente_repo() -> ClienteExistenteRepository:
    """Dependency for cliente repository"""
    return cliente_repository
