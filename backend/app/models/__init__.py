"""Pydantic Models"""
from .lead import (
    LeadStatus, Temperatura, Interacao,
    LeadBase, LeadCreate, LeadUpdate, LeadInDB, LeadResponse,
    LeadListResponse, LeadFilters
)
from .campaign import (
    CampaignStatus, CampaignCreate, CampaignProgress, CampaignResult
)
from .webhook import (
    UazapMessage, VapiCallEvent, N8nTrigger
)

__all__ = [
    "LeadStatus", "Temperatura", "Interacao",
    "LeadBase", "LeadCreate", "LeadUpdate", "LeadInDB", "LeadResponse",
    "LeadListResponse", "LeadFilters",
    "CampaignStatus", "CampaignCreate", "CampaignProgress", "CampaignResult",
    "UazapMessage", "VapiCallEvent", "N8nTrigger",
]
