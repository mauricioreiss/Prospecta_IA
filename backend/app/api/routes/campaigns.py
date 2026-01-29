"""Campaigns API Routes - Prospecting jobs"""
from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.app.models import CampaignCreate, CampaignProgress, CampaignStatus
from backend.app.core.prospecting import prospect_google_maps

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# In-memory job storage (replace with Redis in production)
_jobs = {}
_job_counter = 0


@router.post("/start")
async def start_campaign(
    request: CampaignCreate,
    background_tasks: BackgroundTasks
):
    """Start a new prospecting campaign"""
    global _job_counter
    _job_counter += 1
    job_id = _job_counter

    _jobs[job_id] = CampaignProgress(
        job_id=job_id,
        status=CampaignStatus.RUNNING,
        progresso=0,
        leads_encontrados=0,
        leads_qualificados=0,
        mensagem="Iniciando busca..."
    )

    def run_prospecting():
        def progress_callback(pct, msg):
            _jobs[job_id].progresso = pct
            _jobs[job_id].mensagem = msg

        try:
            stats = prospect_google_maps(
                nicho=request.nicho,
                cidade=request.cidade,
                limite=request.limite,
                progress_callback=progress_callback
            )

            _jobs[job_id].status = CampaignStatus.COMPLETED
            _jobs[job_id].progresso = 100
            _jobs[job_id].leads_encontrados = stats["encontrados"]
            _jobs[job_id].leads_qualificados = stats["salvos_telefone"] + stats["salvos_site"]
            _jobs[job_id].mensagem = f"Concluido! {_jobs[job_id].leads_qualificados} leads qualificados"

        except Exception as e:
            _jobs[job_id].status = CampaignStatus.FAILED
            _jobs[job_id].mensagem = str(e)

    background_tasks.add_task(run_prospecting)

    return {"job_id": job_id, "status": "started"}


@router.get("/{job_id}")
def get_campaign_status(job_id: int):
    """Get campaign progress"""
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job nao encontrado")
    return _jobs[job_id]
