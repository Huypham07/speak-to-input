import { useCallback, useEffect, useRef, useState } from "react";

interface VoiceWebSocketOptions {
  onTranscriptReceived?: (text: string) => void;
  onIntentExtracted?: (data: {
    asr_text: string;
    normalized_text: string;
    intent_type: string;
    parameters: any;
    intent_changed: boolean;
    needs_confirmation: boolean;
  }) => void;
  onExecutionSuccess?: (data: { data: any; message: string }) => void;
  onExecutionError?: (error: string) => void;
  onError?: (error: string) => void;
}

interface UseVoiceWebSocketResult {
  connect: (token: string, formData?: any, intentType?: string) => Promise<void>;
  disconnect: () => void;
  sendAudioChunk: (audioData: ArrayBuffer) => void;
  processVoice: () => void;
  stopRecording: () => boolean;
  confirmExecution: (intentType: string, parameters: any) => void;
  cancelRecording: () => void;
  isConnected: boolean;
  isReady: boolean;
  error: string | null;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function useVoiceWebSocket(options: VoiceWebSocketOptions = {}): UseVoiceWebSocketResult {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(
    async (token: string, formData?: any, intentType?: string) => {
      return new Promise<void>((resolve, reject) => {
        try {
          setError(null);
          setIsReady(false);

          // Close existing connection
          if (wsRef.current && wsRef.current.readyState !== WebSocket.CLOSED) {
            console.log("Closing existing connection...");
            wsRef.current.close();
            wsRef.current = null;
          }

          const wsUrl = `${WS_URL}/api/v1/voice/stream?token=${token}`;

          const ws = new WebSocket(wsUrl);
          wsRef.current = ws;

          // Set timeout for connection
          const connectionTimeout = setTimeout(() => {
            console.error("❌ WebSocket connection timeout");
            ws.close();
            reject(new Error("WebSocket connection timeout"));
          }, 10000); // 10 seconds timeout

          ws.onopen = () => {
            console.log("✅ WebSocket connected!");
            setIsConnected(true);

            // Send initialization message
            const initMessage = {
              type: "init",
              intent_type: intentType || null,
              form_data: formData || {},
            };
            console.log("📤 Sending init message:", initMessage);
            ws.send(JSON.stringify(initMessage));
          };

          ws.onmessage = (event) => {
            try {
              const message = JSON.parse(event.data);
              console.log("📥 WebSocket message received:", message);

              switch (message.type) {
                case "connected":
                  console.log("✅ Connection confirmed:", message.message);
                  break;

                case "init_ack":
                  console.log("✅ Session initialized:", message.message);
                  setIsReady(true);
                  clearTimeout(connectionTimeout);
                  resolve(); // Connection successful and ready
                  break;

                case "audio_chunk_ack":
                  // Audio chunk acknowledged - silent success
                  break;

                case "recording_stopped":
                  console.log("✅ Recording saved:", message.message);
                  console.log("📁 File:", message.filename);
                  console.log("📊 Chunks:", message.chunks_count);
                  break;

                case "intent_extracted":
                  options.onIntentExtracted?.(message);
                  break;

                case "execution_success":
                  options.onExecutionSuccess?.(message);
                  break;

                case "execution_error":
                  options.onExecutionError?.(message.error);
                  setError(message.error);
                  break;

                case "confirmation_required":
                  // Handle confirmation UI
                  console.log("Confirmation required:", message);
                  break;

                case "error":
                  console.error("WebSocket error:", message.error);
                  setError(message.error);
                  options.onError?.(message.error);
                  clearTimeout(connectionTimeout);
                  reject(new Error(message.error));
                  break;

                case "pong":
                  // Heartbeat response
                  break;

                default:
                  console.warn("Unknown message type:", message.type);
              }
            } catch (err) {
              console.error("Error parsing WebSocket message:", err);
            }
          };

          ws.onerror = (event) => {
            console.error("❌ WebSocket error:", event);
            setError("WebSocket connection error");
            options.onError?.("WebSocket connection error");
            clearTimeout(connectionTimeout);
            reject(new Error("WebSocket connection error"));
          };

          ws.onclose = (event) => {
            console.log("🔌 WebSocket closed");
            console.log("Close code:", event.code);
            console.log("Close reason:", event.reason);
            console.log("Was clean:", event.wasClean);
            setIsConnected(false);
            setIsReady(false);
            clearTimeout(connectionTimeout);

            // If not clean close during connection, reject
            if (!event.wasClean && !isConnected) {
              reject(new Error(`WebSocket closed unexpectedly: ${event.code} ${event.reason || "No reason provided"}`));
            }
          };
        } catch (err) {
          console.error("❌ Error connecting to WebSocket:", err);
          setError("Failed to connect to voice service");
          options.onError?.("Failed to connect to voice service");
          reject(err);
        }
      });
    },
    [options]
  );

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsReady(false);
  }, []);

  const sendAudioChunk = useCallback((audioData: ArrayBuffer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Send binary data directly (faster than base64)
      wsRef.current.send(audioData);
    }
  }, []);

  const processVoice = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "process_voice",
        })
      );
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log("📨 Sending stop_recording message to backend");
      wsRef.current.send(
        JSON.stringify({
          type: "stop_recording",
        })
      );
      return true;
    }
    return false;
  }, []);

  const confirmExecution = useCallback((intentType: string, parameters: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log("📨 Sending confirm_execute message");
      wsRef.current.send(
        JSON.stringify({
          type: "confirm_execute",
          intent_type: intentType,
          parameters,
        })
      );
    }
  }, []);

  const cancelRecording = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log("📨 Sending cancel message");
      wsRef.current.send(
        JSON.stringify({
          type: "cancel",
        })
      );
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      disconnect();
    };
  }, [disconnect]);

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, [isConnected]);

  return {
    connect,
    disconnect,
    sendAudioChunk,
    processVoice,
    stopRecording,
    confirmExecution,
    cancelRecording,
    isConnected,
    isReady,
    error,
  };
}
