"""
Integracao com Vapi - Voice AI para chamadas automaticas
"""
import asyncio
import aiohttp
from typing import Optional, Callable
from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()


class VapiCallConfig(BaseModel):
    """Configuracao para iniciar chamada"""
    phone_number: str
    lead_id: str
    lead_name: str
    assistant_id: Optional[str] = None
    first_message: Optional[str] = None


class VapiCallResult(BaseModel):
    """Resultado da chamada"""
    call_id: str
    status: str
    duration: int = 0
    transcript: Optional[str] = None
    summary: Optional[str] = None
    outcome: Optional[str] = None  # interested, not_interested, callback, no_answer


async def start_call(config: VapiCallConfig) -> str:
    """
    Inicia chamada via Vapi API

    Returns:
        call_id da chamada iniciada
    """
    if not settings.vapi_api_key:
        raise ValueError("VAPI_API_KEY nao configurado")

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.vapi.ai/call",
            headers={
                "Authorization": f"Bearer {settings.vapi_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "phoneNumber": config.phone_number,
                "assistantId": config.assistant_id,
                "metadata": {
                    "lead_id": config.lead_id,
                    "lead_name": config.lead_name
                },
                "firstMessage": config.first_message
            }
        ) as response:
            if response.status != 200:
                raise Exception(f"Erro ao iniciar chamada: {await response.text()}")

            data = await response.json()
            return data.get("id")


async def end_call(call_id: str) -> bool:
    """Encerra chamada ativa"""
    if not settings.vapi_api_key:
        return False

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://api.vapi.ai/call/{call_id}/end",
            headers={
                "Authorization": f"Bearer {settings.vapi_api_key}"
            }
        ) as response:
            return response.status == 200


async def get_call_status(call_id: str) -> dict:
    """Busca status da chamada"""
    if not settings.vapi_api_key:
        return {}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.vapi.ai/call/{call_id}",
            headers={
                "Authorization": f"Bearer {settings.vapi_api_key}"
            }
        ) as response:
            if response.status == 200:
                return await response.json()
            return {}


class VapiWebSocketClient:
    """
    Cliente WebSocket para eventos em tempo real do Vapi
    Usado para mostrar status da chamada na UI
    """

    def __init__(self, on_event: Callable):
        self.on_event = on_event
        self.ws = None
        self.is_connected = False

    async def connect(self):
        """Conecta ao WebSocket do Vapi"""
        if not settings.vapi_api_key:
            raise ValueError("VAPI_API_KEY nao configurado")

        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(
            f"wss://api.vapi.ai/ws?api_key={settings.vapi_api_key}"
        )
        self.is_connected = True

        # Inicia loop de eventos
        asyncio.create_task(self._event_loop())

    async def _event_loop(self):
        """Loop para receber eventos"""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    import json
                    event = json.loads(msg.data)
                    await self.on_event(event)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
        finally:
            self.is_connected = False

    async def disconnect(self):
        """Desconecta do WebSocket"""
        if self.ws:
            await self.ws.close()
        if self.session:
            await self.session.close()
        self.is_connected = False


def parse_vapi_event(event: dict) -> dict:
    """
    Parseia evento do Vapi para formato padronizado

    Eventos suportados:
    - call-started
    - call-ended
    - speech-update
    - transcript
    - function-call
    """
    event_type = event.get("type", "unknown")

    parsed = {
        "type": event_type,
        "call_id": event.get("call", {}).get("id"),
        "timestamp": event.get("timestamp"),
    }

    if event_type == "call-started":
        parsed["lead_id"] = event.get("call", {}).get("metadata", {}).get("lead_id")
        parsed["lead_name"] = event.get("call", {}).get("metadata", {}).get("lead_name")
        parsed["phone_number"] = event.get("call", {}).get("phoneNumber")

    elif event_type == "call-ended":
        parsed["duration"] = event.get("call", {}).get("duration", 0)
        parsed["status"] = event.get("call", {}).get("status")

    elif event_type == "transcript":
        parsed["role"] = event.get("role")  # assistant or user
        parsed["text"] = event.get("transcript")

    elif event_type == "speech-update":
        parsed["status"] = event.get("status")  # started, stopped

    elif event_type == "function-call":
        parsed["function_name"] = event.get("functionCall", {}).get("name")
        parsed["function_args"] = event.get("functionCall", {}).get("arguments")

    return parsed


def map_event_to_ui_status(event: dict) -> str:
    """
    Mapeia evento para mensagem amigavel na UI

    Ex: function-call "check_decision_maker" -> "Confirmando tomador de decisao..."
    """
    event_type = event.get("type")

    if event_type == "call-started":
        return "Conectando..."

    if event_type == "speech-update":
        if event.get("status") == "started":
            return "Falando..."
        return "Ouvindo..."

    if event_type == "function-call":
        function_name = event.get("function_name", "")

        function_messages = {
            "check_decision_maker": "Confirmando tomador de decisao...",
            "identify_pain_point": "Identificando necessidades...",
            "present_solution": "Apresentando solucao...",
            "check_interest": "Verificando interesse...",
            "schedule_meeting": "Agendando proximo passo...",
            "handle_objection": "Respondendo objecao...",
        }

        return function_messages.get(function_name, "Processando...")

    if event_type == "call-ended":
        return "Chamada encerrada"

    return "Em andamento..."
