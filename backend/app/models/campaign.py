"""Campaign models - Prospecting job schemas"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class CampaignStatus(str, Enum):
    """Campaign job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CampaignCreate(BaseModel):
    """Start a new prospecting campaign"""
    nicho: str
    cidade: str
    limite: int = Field(default=20, ge=5, le=100)
    analisar_sites: bool = True


class CampaignProgress(BaseModel):
    """Campaign progress update"""
    job_id: int
    status: CampaignStatus
    progresso: int = 0  # 0-100
    leads_encontrados: int = 0
    leads_qualificados: int = 0
    mensagem: Optional[str] = None


class CampaignResult(BaseModel):
    """Campaign completion result"""
    job_id: int
    status: CampaignStatus
    estatisticas: Dict[str, Any]
    duracao_segundos: float
    created_at: datetime
