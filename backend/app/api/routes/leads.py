"""Leads API Routes"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.api.dependencies import get_lead_repo
from backend.app.integrations.supabase import LeadRepository
from backend.app.integrations.tavily import get_icebreaker_for_lead
from backend.app.integrations.n8n import send_whatsapp_message
from backend.app.core.scoring import calculate_score
from backend.app.models import (
    LeadResponse, LeadListResponse, LeadUpdate, LeadFilters, LeadStatus
)

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=LeadListResponse)
def list_leads(
    status: Optional[List[LeadStatus]] = Query(None),
    nicho: Optional[str] = None,
    cidade: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    repo: LeadRepository = Depends(get_lead_repo)
):
    """List leads with optional filters"""
    filters = LeadFilters(
        status=status,
        nicho=nicho,
        cidade=cidade,
        min_score=min_score
    )

    leads = repo.find_all(filters, limit, offset)

    # Add computed fields
    for lead in leads:
        metadata = lead.get("metadata") or {}
        score_result = calculate_score(
            nota_google=lead.get("nota_google") or 0,
            tem_telefone=bool(lead.get("telefone")),
            tem_site=bool(lead.get("site")),
            reviews_count=metadata.get("reviewsCount") or 0
        )
        lead["temperatura"] = score_result["temperatura"]

    return LeadListResponse(total=len(leads), leads=leads)


@router.get("/counts")
def get_lead_counts(repo: LeadRepository = Depends(get_lead_repo)):
    """Get lead counts by status for pipeline cards"""
    counts = repo.count_by_status()

    # Map to 4 UI cards
    return {
        "novos": counts.get("novo", 0) + counts.get("contato_site", 0),
        "contatado": counts.get("contatado", 0),
        "interesse": counts.get("interessado", 0) + counts.get("negociacao", 0),
        "agendado": counts.get("agendado", 0) + counts.get("fechado", 0),
        "total": sum(counts.values())
    }


@router.get("/{lead_id}")
def get_lead(
    lead_id: int,
    repo: LeadRepository = Depends(get_lead_repo)
):
    """Get single lead by ID"""
    lead = repo.find_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nao encontrado")

    # Add computed fields
    metadata = lead.get("metadata") or {}
    score_result = calculate_score(
        nota_google=lead.get("nota_google") or 0,
        tem_telefone=bool(lead.get("telefone")),
        tem_site=bool(lead.get("site")),
        reviews_count=metadata.get("reviewsCount") or 0
    )
    lead["temperatura"] = score_result["temperatura"]

    return lead


@router.patch("/{lead_id}")
def update_lead(
    lead_id: int,
    updates: LeadUpdate,
    repo: LeadRepository = Depends(get_lead_repo)
):
    """Update lead fields"""
    if not repo.update(lead_id, updates):
        raise HTTPException(status_code=500, detail="Erro ao atualizar lead")
    return {"status": "updated"}


@router.post("/{lead_id}/status")
def update_status(
    lead_id: int,
    status: LeadStatus,
    repo: LeadRepository = Depends(get_lead_repo)
):
    """Update lead status and log interaction"""
    if not repo.update_status(lead_id, status):
        raise HTTPException(status_code=500, detail="Erro ao atualizar status")

    repo.add_interaction(lead_id, "mudanca_status", f"Status alterado para: {status.value}")
    return {"status": "updated", "new_status": status.value}


@router.post("/{lead_id}/interaction")
def add_interaction(
    lead_id: int,
    tipo: str,
    descricao: str,
    repo: LeadRepository = Depends(get_lead_repo)
):
    """Add interaction to lead history"""
    if not repo.add_interaction(lead_id, tipo, descricao):
        raise HTTPException(status_code=500, detail="Erro ao adicionar interacao")
    return {"status": "added"}


@router.get("/{lead_id}/icebreaker")
def get_icebreaker(
    lead_id: int,
    repo: LeadRepository = Depends(get_lead_repo)
):
    """Get Tavily icebreaker for lead"""
    lead = repo.find_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nao encontrado")

    icebreaker = get_icebreaker_for_lead(lead)
    return {"icebreaker": icebreaker}


@router.delete("/bulk")
def delete_leads_bulk(
    status: Optional[str] = Query(None, description="Status to delete (or 'all' for all leads)"),
    repo: LeadRepository = Depends(get_lead_repo)
):
    """Delete leads by status or all leads"""
    if status == "all":
        deleted = repo.delete_all()
        return {"deleted": deleted, "message": f"{deleted} leads deletados"}

    if status:
        try:
            lead_status = LeadStatus(status)
            deleted = repo.delete_by_status(lead_status)
            return {"deleted": deleted, "message": f"{deleted} leads com status '{status}' deletados"}
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status invalido: {status}")

    raise HTTPException(status_code=400, detail="Informe o status ou 'all' para deletar")


@router.post("/{lead_id}/whatsapp")
async def send_lead_whatsapp(
    lead_id: int,
    message: str,
    repo: LeadRepository = Depends(get_lead_repo)
):
    """Send WhatsApp message to lead via n8n -> Chatwoot"""
    lead = repo.find_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nao encontrado")

    phone = lead.get("telefone")
    if not phone:
        raise HTTPException(status_code=400, detail="Lead nao tem telefone")

    # Normalize phone (add 55 if needed)
    phone_clean = ''.join(c for c in str(phone) if c.isdigit())
    if not phone_clean.startswith('55'):
        phone_clean = '55' + phone_clean

    # Send via n8n -> Chatwoot
    result = await send_whatsapp_message(
        phone=phone_clean,
        message=message,
        tag_campanha="prospeccao_oduo",
        lead_id=lead_id,
        lead_name=lead.get("nome_empresa")
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Erro ao enviar"))

    # Log interaction
    repo.add_interaction(lead_id, "whatsapp", f"Mensagem enviada: {message[:100]}...")

    # Update status if still 'novo'
    if lead.get("status") == "novo":
        repo.update_status(lead_id, LeadStatus.CONTATADO)

    return {"status": "sent", "phone": phone}


