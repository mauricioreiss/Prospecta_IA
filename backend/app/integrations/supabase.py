"""Supabase integration - Database operations"""
from typing import Optional, List, Dict, Any
from functools import lru_cache
from supabase import create_client, Client

from backend.app.config import settings
from backend.app.models import (
    LeadInDB, LeadCreate, LeadUpdate, LeadFilters, LeadStatus
)


@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client"""
    return create_client(settings.supabase_url, settings.supabase_key)


class LeadRepository:
    """Lead data access layer"""

    def __init__(self):
        self.client = get_supabase_client()
        self.table = settings.table_leads

    def find_all(
        self,
        filters: Optional[LeadFilters] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Find leads with optional filters"""
        query = self.client.table(self.table).select("*")

        if filters:
            if filters.status:
                query = query.in_("status", [s.value for s in filters.status])
            if filters.nicho:
                query = query.eq("nicho", filters.nicho)
            if filters.cidade:
                query = query.ilike("cidade", f"%{filters.cidade}%")
            if filters.min_score:
                query = query.gte("score", filters.min_score)

        query = query.order("score", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        return result.data or []

    def find_by_id(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """Find single lead by ID"""
        result = self.client.table(self.table).select("*").eq("id", lead_id).single().execute()
        return result.data

    def create(self, lead: LeadCreate, score: float = 0.0, status: LeadStatus = LeadStatus.NOVO) -> Dict[str, Any]:
        """Create new lead"""
        data = lead.model_dump()
        data["score"] = score
        data["status"] = status.value
        data["interacoes"] = []

        result = self.client.table(self.table).insert(data).execute()
        return result.data[0] if result.data else None

    def upsert(self, lead: LeadCreate, score: float, status: LeadStatus) -> Dict[str, Any]:
        """Upsert lead (update if exists by nome_empresa+cidade)"""
        data = lead.model_dump()
        data["score"] = score
        data["status"] = status.value
        data["interacoes"] = []

        result = self.client.table(self.table).upsert(
            data,
            on_conflict="nome_empresa,cidade"
        ).execute()
        return result.data[0] if result.data else None

    def update(self, lead_id: int, updates: LeadUpdate) -> bool:
        """Update lead fields"""
        data = {k: v for k, v in updates.model_dump().items() if v is not None}
        if "status" in data and isinstance(data["status"], LeadStatus):
            data["status"] = data["status"].value

        result = self.client.table(self.table).update(data).eq("id", lead_id).execute()
        return len(result.data) > 0

    def update_status(self, lead_id: int, status: LeadStatus) -> bool:
        """Update lead status"""
        result = self.client.table(self.table).update(
            {"status": status.value}
        ).eq("id", lead_id).execute()
        return len(result.data) > 0

    def add_interaction(self, lead_id: int, tipo: str, descricao: str) -> bool:
        """Add interaction to lead history"""
        from datetime import datetime

        lead = self.find_by_id(lead_id)
        if not lead:
            return False

        interacoes = lead.get("interacoes", []) or []
        interacoes.append({
            "data": datetime.now().isoformat(),
            "tipo": tipo,
            "descricao": descricao
        })

        result = self.client.table(self.table).update(
            {"interacoes": interacoes}
        ).eq("id", lead_id).execute()
        return len(result.data) > 0

    def count_by_status(self) -> Dict[str, int]:
        """Count leads grouped by status"""
        counts = {}
        for status in LeadStatus:
            try:
                result = self.client.table(self.table).select("id", count="exact").eq("status", status.value).execute()
                counts[status.value] = result.count or 0
            except Exception:
                counts[status.value] = 0
        return counts

    def delete_by_status(self, status: LeadStatus) -> int:
        """Delete all leads with given status"""
        try:
            result = self.client.table(self.table).delete().eq("status", status.value).execute()
            return len(result.data) if result.data else 0
        except Exception:
            return 0

    def delete_all(self) -> int:
        """Delete all leads"""
        try:
            result = self.client.table(self.table).delete().neq("id", 0).execute()
            return len(result.data) if result.data else 0
        except Exception:
            return 0


class ClienteExistenteRepository:
    """Existing clients (blacklist) data access"""

    def __init__(self):
        self.client = get_supabase_client()
        self.table = settings.table_clientes
        self._table_exists = None

    def _check_table_exists(self) -> bool:
        """Check if table exists (cached)"""
        if self._table_exists is not None:
            return self._table_exists
        try:
            self.client.table(self.table).select("id").limit(1).execute()
            self._table_exists = True
        except Exception:
            self._table_exists = False
        return self._table_exists

    def find_all(self) -> List[Dict[str, Any]]:
        """Get all existing clients"""
        if not self._check_table_exists():
            return []
        try:
            result = self.client.table(self.table).select("nome_empresa, nome_normalizado").execute()
            return result.data or []
        except Exception:
            return []

    def exists(self, nome_normalizado: str) -> bool:
        """Check if client exists by normalized name"""
        if not self._check_table_exists():
            return False
        try:
            result = self.client.table(self.table).select("id").eq("nome_normalizado", nome_normalizado).execute()
            return len(result.data) > 0
        except Exception:
            return False


# Singleton instances
lead_repository = LeadRepository()
cliente_repository = ClienteExistenteRepository()
