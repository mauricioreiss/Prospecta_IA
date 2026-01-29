"""
Prospecta IA - FastAPI Backend
Clean Architecture entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import settings
from backend.app.api.routes import (
    leads_router,
    campaigns_router,
    webhooks_router,
    reactivation_router,
    ai_responder_router
)

app = FastAPI(
    title=settings.app_name,
    description="Sistema inteligente de prospeccao B2B",
    version=settings.app_version
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(leads_router, prefix="/api")
app.include_router(campaigns_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(reactivation_router, prefix="/api")
app.include_router(ai_responder_router, prefix="/api")


@app.get("/")
def root():
    """Health check"""
    return {
        "status": "online",
        "app": settings.app_name,
        "version": settings.app_version
    }


@app.get("/health")
def health():
    """Detailed health check"""
    from backend.app.integrations.supabase import get_supabase_client

    try:
        client = get_supabase_client()
        client.table(settings.table_leads).select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
