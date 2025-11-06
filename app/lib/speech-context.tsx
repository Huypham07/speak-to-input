"use client";

import type React from "react";
import { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";
import { useVoiceWebSocket } from "@/hooks/use-voice-websocket";
import { useAuth } from "@/lib/auth-context";

interface SpeechContextType {
  isListening: boolean;
  transcript: string;
  isProcessing: boolean;
  error: string | null;
  startListening: (formData?: any, intentType?: string) => Promise<void>;
  stopListening: () => Promise<void>;
  clearTranscript: () => void;
  extractedIntent: { intent_type: string; parameters: any; confidence: number } | null;
  executeIntent: (intentType: string, parameters: any, needsConfirmation?: boolean) => void;
  isConnected: boolean;
}

const SpeechContext = createContext<SpeechContextType | undefined>(undefined);

export function SpeechProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractedIntent, setExtractedIntent] = useState<{
    intent_type: string;
    parameters: any;
    confidence: number;
  } | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);

  const {
    connect,
    disconnect,
    sendAudioChunk,
    processVoice,
    stopRecording,
    executeIntent: wsExecuteIntent,
    isConnected,
    isReady,
  } = useVoiceWebSocket({
    onIntentExtracted: (data) => {
      console.log("Intent extracted:", data);
      setExtractedIntent(data);
      setIsProcessing(false);
    },
    onExecutionSuccess: (data) => {
      console.log("Execution success:", data);
      setIsProcessing(false);
    },
    onExecutionError: (err) => {
      console.error("Execution error:", err);
      setError(err);
      setIsProcessing(false);
    },
    onError: (err) => {
      console.error("WebSocket error:", err);
      setError(err);
    },
  });

  const startListening = useCallback(
    async (formData?: any, intentType?: string) => {
      // Prevent double calls (React StrictMode)
      if (isListening || isConnected) {
        console.log("⚠️ Already listening/connected, ignoring duplicate call");
        return;
      }

      try {
        console.log("Form data:", JSON.stringify(formData, null, 2));
        console.log("Intent type:", intentType);

        setError(null);
        setTranscript("");
        setExtractedIntent(null);

        let actualToken = localStorage.getItem("access_token");

        if (!actualToken) {
          console.error("❌ NO TOKEN FOUND - STOPPING");
          setError("Authentication required - No access token found");
          return;
        }

        // Connect to WebSocket
        await connect(actualToken, formData, intentType);

        // Start recording audio
        console.log("Starting audio recording...");
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            sampleRate: 16000,
          },
        });
        audioStreamRef.current = stream;

        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: "audio/webm",
        });
        mediaRecorderRef.current = mediaRecorder;

        // Send audio chunks as they become available
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            console.log("📤 Sending audio chunk, size:", event.data.size);
            event.data.arrayBuffer().then((arrayBuffer) => {
              sendAudioChunk(arrayBuffer);
            });
          }
        };

        // Send chunks every 5 seconds (or remaining if < 5s)
        mediaRecorder.start(5000); // 5 second chunks
        console.log("🎙️ Recording started! Sending chunks every 5 seconds");
        setIsListening(true);
      } catch (err) {
        console.error("Error in startListening:", err);
        setError("Microphone access denied");
        console.error("Error accessing microphone:", err);
        disconnect();
      }
    },
    [connect, disconnect, isReady, sendAudioChunk, isListening, isConnected]
  );

  const stopListening = useCallback(async () => {
    if (!mediaRecorderRef.current) return;

    console.log("⏹️ Stopping recording...");
    setIsProcessing(true);

    try {
      // Stop recording - this will trigger final ondataavailable
      mediaRecorderRef.current.stop();

      // Wait longer for final chunk to be processed and sent
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Notify backend that recording stopped
      stopRecording();

      setIsListening(false);

      // Stop all tracks
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach((track: MediaStreamTrack) => track.stop());
        audioStreamRef.current = null;
      }

      // Close WebSocket connection after recording
      disconnect();

      console.log("✅ Recording stopped and saved on backend");
    } catch (err) {
      console.error("Error stopping recording:", err);
      setError("Failed to stop recording");
    } finally {
      setIsProcessing(false);
    }
  }, [stopRecording]);

  const clearTranscript = useCallback(() => {
    setTranscript("");
    setError(null);
    setExtractedIntent(null);
  }, []);

  const executeIntent = useCallback(
    (intentType: string, parameters: any, needsConfirmation: boolean = false) => {
      wsExecuteIntent(intentType, parameters, needsConfirmation);
    },
    [wsExecuteIntent]
  );

  // Cleanup on unmount only
  useEffect(() => {
    return () => {
      // Only cleanup when component unmounts
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach((track) => track.stop());
      }
      disconnect();
    };
  }, []); // Empty deps - only run on mount/unmount

  return (
    <SpeechContext.Provider
      value={{
        isListening,
        transcript,
        isProcessing,
        error,
        startListening,
        stopListening,
        clearTranscript,
        extractedIntent,
        executeIntent,
        isConnected,
      }}>
      {children}
    </SpeechContext.Provider>
  );
}

export function useSpeech() {
  const context = useContext(SpeechContext);
  if (context === undefined) {
    throw new Error("useSpeech must be used within SpeechProvider");
  }
  return context;
}
