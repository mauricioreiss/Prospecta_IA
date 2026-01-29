"""
API Routes - Realtime
WebSocket para eventos em tempo real (Vapi calls)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json

from app.integrations.vapi import (
    VapiWebSocketClient, parse_vapi_event, map_event_to_ui_status,
    start_call, end_call, VapiCallConfig
)
from app.integrations import supabase
from app.config import get_settings

router = APIRouter(prefix="/ws", tags=["realtime"])
settings = get_settings()

# Conexoes ativas do frontend
active_connections: Set[WebSocket] = set()


class ConnectionManager:
    """Gerencia conexoes WebSocket do frontend"""

    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Envia mensagem para todos os clientes conectados"""
        disconnected = set()
        for connection in self.connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Remove conexoes mortas
        self.connections -= disconnected


manager = ConnectionManager()


@router.websocket("/calls")
async def websocket_calls(websocket: WebSocket):
    """
    WebSocket para eventos de chamadas em tempo real

    O frontend conecta aqui para receber:
    - Status da chamada (conectando, falando, etc)
    - Transcricao em tempo real
    - Eventos do Vapi
    """
    await manager.connect(websocket)

    try:
        # Envia estado inicial
        await websocket.send_json({
            "type": "connected",
            "message": "Conectado ao servidor de chamadas"
        })

        while True:
            # Recebe comandos do frontend
            data = await websocket.receive_json()
            command = data.get("command")

            if command == "start_call":
                # Inicia chamada
                await handle_start_call(websocket, data)

            elif command == "end_call":
                # Encerra chamada
                await handle_end_call(websocket, data)

            elif command == "ping":
                # Keepalive
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(websocket)


async def handle_start_call(websocket: WebSocket, data: dict):
    """Inicia chamada via Vapi"""
    try:
        lead_id = data.get("lead_id")
        if not lead_id:
            await websocket.send_json({
                "type": "error",
                "message": "lead_id obrigatorio"
            })
            return

        # Busca lead
        lead = supabase.get_lead_by_id(lead_id)
        if not lead:
            await websocket.send_json({
                "type": "error",
                "message": "Lead nao encontrado"
            })
            return

        if not lead.get("telefone"):
            await websocket.send_json({
                "type": "error",
                "message": "Lead sem telefone"
            })
            return

        # Inicia chamada
        call_id = await start_call(VapiCallConfig(
            phone_number=lead["telefone"],
            lead_id=lead_id,
            lead_name=lead.get("nome_empresa", "Lead")
        ))

        # Notifica frontend
        await websocket.send_json({
            "type": "call-started",
            "call_id": call_id,
            "lead_id": lead_id,
            "lead_name": lead.get("nome_empresa"),
            "phone_number": lead.get("telefone"),
            "status": "Conectando..."
        })

        # Inicia listener de eventos do Vapi
        asyncio.create_task(
            listen_vapi_events(call_id, lead_id)
        )

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Erro ao iniciar chamada: {str(e)}"
        })


async def handle_end_call(websocket: WebSocket, data: dict):
    """Encerra chamada ativa"""
    call_id = data.get("call_id")
    if call_id:
        success = await end_call(call_id)
        await websocket.send_json({
            "type": "call-ended",
            "call_id": call_id,
            "success": success
        })


async def listen_vapi_events(call_id: str, lead_id: str):
    """
    Escuta eventos do Vapi e retransmite para o frontend

    Conecta ao WebSocket do Vapi e parseia eventos
    """
    async def on_event(event: dict):
        parsed = parse_vapi_event(event)

        # Mapeia para mensagem UI
        ui_message = {
            "type": parsed["type"],
            "call_id": call_id,
            "lead_id": lead_id,
            "status": map_event_to_ui_status(parsed),
            "timestamp": parsed.get("timestamp")
        }

        # Adiciona dados especificos por tipo
        if parsed["type"] == "transcript":
            ui_message["transcript"] = {
                "role": parsed.get("role"),
                "text": parsed.get("text")
            }

        if parsed["type"] == "call-ended":
            ui_message["duration"] = parsed.get("duration", 0)

        # Broadcast para todos os clientes
        await manager.broadcast(ui_message)

    try:
        client = VapiWebSocketClient(on_event)
        await client.connect()

        # Mantém conexao ate a chamada encerrar
        while client.is_connected:
            await asyncio.sleep(1)

    except Exception:
        pass  # Conexao encerrada


# ===========================================
# HTTP Endpoints para fallback
# ===========================================

@router.get("/status")
async def get_realtime_status():
    """Status do servidor de tempo real"""
    return {
        "active_connections": len(manager.connections),
        "vapi_configured": bool(settings.vapi_api_key)
    }
