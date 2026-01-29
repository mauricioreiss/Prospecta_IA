"""Lead models - Pydantic schemas for leads"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LeadStatus(str, Enum):
    """Pipeline status values"""
    NOVO = "novo"
    CONTATO_SITE = "contato_site"
    CONTATADO = "contatado"
    INTERESSADO = "interessado"
    NEGOCIACAO = "negociacao"
    AGENDADO = "agendado"
    FECHADO = "fechado"
    PERDIDO = "perdido"


class Temperatura(str, Enum):
    """Lead temperature classification"""
    QUENTE = "quente"
    MORNO = "morno"
    FRIO = "frio"


class Interacao(BaseModel):
    """Single interaction record"""
    data: datetime = Field(default_factory=datetime.now)
    tipo: str
    descricao: str


class LeadBase(BaseModel):
    """Base lead fields"""
    nome_empresa: str
    telefone: Optional[str] = None
    site: Optional[str] = None
    endereco: Optional[str] = None
    cidade: str
    nota_google: Optional[float] = None
    nicho: str


class LeadCreate(LeadBase):
    """Fields for creating a new lead"""
    metadata: Optional[Dict[str, Any]] = None


class LeadUpdate(BaseModel):
    """Fields that can be updated"""
    status: Optional[LeadStatus] = None
    score: Optional[float] = None
    observacoes: Optional[str] = None
    diagnostico: Optional[Dict[str, Any]] = None


class LeadInDB(LeadBase):
    """Lead as stored in database"""
    id: int
    status: LeadStatus = LeadStatus.NOVO
    score: float = 0.0
    interacoes: List[Interacao] = []
    diagnostico: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LeadResponse(LeadInDB):
    """Lead response with computed fields"""
    temperatura: Optional[Dict[str, str]] = None
    tavily_icebreaker: Optional[str] = None


class LeadListResponse(BaseModel):
    """Paginated lead list"""
    total: int
    leads: List[LeadResponse]


class LeadFilters(BaseModel):
    """Filters for querying leads"""
    status: Optional[List[LeadStatus]] = None
    nicho: Optional[str] = None
    temperatura: Optional[Temperatura] = None
    cidade: Optional[str] = None
    min_score: Optional[float] = None
