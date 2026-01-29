'use client';

import { useEffect, useRef, useCallback, useState } from 'react';
import { useApp } from '@/contexts/AppContext';

const WS_URL = process.env.NEXT_PUBLIC_BACKEND_URL?.replace('http', 'ws') || 'ws://localhost:8000';

interface VapiEvent {
  type: string;
  call_id?: string;
  lead_id?: string;
  lead_name?: string;
  phone_number?: string;
  status?: string;
  transcript?: { role: string; text: string };
  duration?: number;
}

export function useVapiConnection() {
  const { setActiveCall } = useApp();
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const ws = new WebSocket(`${WS_URL}/api/ws/calls`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data: VapiEvent = JSON.parse(event.data);
        handleEvent(data);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);

      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    wsRef.current = ws;
  }, []);

  const handleEvent = useCallback((event: VapiEvent) => {
    switch (event.type) {
      case 'connected':
        console.log('Vapi connection established');
        break;

      case 'call-started':
        setActiveCall({
          isActive: true,
          callId: event.call_id || null,
          leadId: event.lead_id || null,
          leadName: event.lead_name || 'Lead',
          phoneNumber: event.phone_number || '',
          status: event.status || 'Conectando...',
          transcript: [],
          duration: 0,
        });
        break;

      case 'transcript':
        if (event.transcript) {
          setActiveCall((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              transcript: [...prev.transcript, event.transcript!],
            };
          });
        }
        break;

      case 'status-update':
        setActiveCall((prev) => {
          if (!prev) return null;
          return {
            ...prev,
            status: event.status || prev.status,
          };
        });
        break;

      case 'call-ended':
        setActiveCall((prev) => {
          if (!prev) return null;
          return {
            ...prev,
            isActive: false,
            duration: event.duration || prev.duration,
          };
        });
        break;

      case 'pong':
        // Keepalive response
        break;

      default:
        console.log('Unknown event:', event.type);
    }
  }, [setActiveCall]);

  const startCall = useCallback((leadId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        command: 'start_call',
        lead_id: leadId,
      }));
    }
  }, []);

  const endCall = useCallback((callId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        command: 'end_call',
        call_id: callId,
      }));
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    // Keepalive ping every 30 seconds
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ command: 'ping' }));
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  return {
    isConnected,
    startCall,
    endCall,
  };
}
