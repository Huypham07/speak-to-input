"use client";

import type React from "react";
import { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useVoiceWebSocket } from "@/hooks/use-voice-websocket";
import { useAuth } from "@/lib/auth-context";
import { VoiceRecordingDialog } from "@/components/speech/voice-recording-dialog";
import { cleanupMicrophoneResources, stopMediaStream } from "@/lib/microphone-utils";
import { encodeWav, downsampleBuffer } from "@/lib/audio-utils";
import { toast } from "sonner";

interface SpeechContextType {
  isListening: boolean;
  isRecordingDialogOpen: boolean;
  transcript: string;
  normalizedText: string;
  isProcessing: boolean;
  error: string | null;
  startListening: (formData?: any, intentType?: string) => Promise<void>;
  stopListening: () => Promise<void>;
  cancelRecording: () => void;
  clearTranscript: () => void;
  extractedIntent: {
    intent_type: string;
    parameters: any;
    intent_changed: boolean;
    needs_confirmation: boolean;
  } | null;
  confirmExecution: () => void;
  cancelExecution: () => void;
  isConnected: boolean;
}

const SpeechContext = createContext<SpeechContextType | undefined>(undefined);

export function SpeechProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();
  const [isListening, setIsListening] = useState(false);
  const [isRecordingDialogOpen, setIsRecordingDialogOpen] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [normalizedText, setNormalizedText] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractedIntent, setExtractedIntent] = useState<{
    intent_type: string;
    parameters: any;
    intent_changed: boolean;
    needs_confirmation: boolean;
  } | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioBufferRef = useRef<Float32Array[]>([]);

  const {
    connect,
    disconnect,
    sendAudioChunk,
    processVoice,
    stopRecording,
    confirmExecution: wsConfirmExecution,
    cancelRecording: wsCancelRecording,
    isConnected,
    isReady,
  } = useVoiceWebSocket({
    onIntentExtracted: (data) => {
      console.log("🎯 Intent extracted:", data);

      // Save transcript and normalized text
      setTranscript(data.asr_text);
      setNormalizedText(data.normalized_text);

      // Normalize intent type - convert backend IntentType to frontend intent types
      const normalizeIntentType = (type: string): string => {
        // Map backend IntentType enum to frontend intent types and routes
        const intentMapping: Record<string, string> = {
          // Transaction intents
          SEND_MONEY: "create_transfer",

          // Financial management intents
          CREATE_BILL: "create_bill",
          PAY_BILL: "pay_bill",
          CREATE_FUND: "create_fund",
          DEPOSIT_FUND: "deposit_fund",
          WITHDRAW_FUND: "withdraw_fund",
          DELETE_FUND: "delete_fund",

          // Query intents
          CHECK_BALANCE: "check_balance",
          QUERY_FINANCE: "query_finance",

          // Account intents
          ACCOUNT_OPENING: "account_opening",

          // Other intents
          QUICK_ACTION: "quick_action",
          CREATE_LOAN: "create_loan",
          BUDGET_ALLOCATION: "budget_allocation",

          // Meta intents
          UNKNOWN: "unknown",
          CONFIRMATION: "confirmation",
          CANCELLATION: "cancellation",
        };

        return intentMapping[type] || type.toLowerCase();
      };

      const normalizedIntentType = normalizeIntentType(data.intent_type);

      // Save intent data with normalized type
      setExtractedIntent({
        intent_type: normalizedIntentType,
        parameters: data.parameters,
        intent_changed: data.intent_changed,
        needs_confirmation: data.needs_confirmation,
      });

      setIsProcessing(false);

      // Map normalized intent types to routes and Vietnamese names
      const intentInfoMap: Record<string, { route: string; name: string }> = {
        // Transaction & Transfer
        create_transfer: { route: "/accounts?action=transfer", name: "Chuyển tiền" },

        // Bills
        create_bill: { route: "/bills", name: "Tạo hóa đơn" },
        pay_bill: { route: "/bills", name: "Thanh toán hóa đơn" },

        // Funds
        create_fund: { route: "/funds", name: "Tạo quỹ tiết kiệm" },
        deposit_fund: { route: "/funds", name: "Nạp vào quỹ" },
        withdraw_fund: { route: "/funds", name: "Rút từ quỹ" },
        delete_fund: { route: "/funds", name: "Xóa quỹ" },

        // Query
        check_balance: { route: "/accounts", name: "Kiểm tra số dư" },
        query_finance: { route: "/dashboard", name: "Tra cứu tài chính" },

        // Account
        account_opening: { route: "/accounts", name: "Mở tài khoản" },

        // Other
        quick_action: { route: "/dashboard", name: "Thao tác nhanh" },
        create_loan: { route: "/dashboard", name: "Tạo khoản vay" },
        budget_allocation: { route: "/dashboard", name: "Phân bổ ngân sách" },

        // Meta
        unknown: { route: "/dashboard", name: "Không nhận dạng được" },
      };

      const intentInfo = intentInfoMap[normalizedIntentType];

      if (intentInfo) {
        // Validate required parameters for each intent
        const validateParams = (
          intentType: string,
          params: Record<string, any>
        ): { valid: boolean; missing: string[] } => {
          const requiredParamsMap: Record<string, string[]> = {
            create_transfer: ["amount", "recipient"],
            create_bill: ["bill_name", "amount"],
            pay_bill: ["bill_id"], // Needs existing bill ID
            create_fund: ["fund_name", "target_amount"],
            deposit_fund: ["fund_id", "amount"], // Needs existing fund ID
            withdraw_fund: ["fund_id", "amount"], // Needs existing fund ID
            delete_fund: ["fund_id"], // Needs existing fund ID
          };

          const required = requiredParamsMap[intentType] || [];
          const missing = required.filter((key) => !params[key] || params[key] === "");

          return { valid: missing.length === 0, missing };
        };

        const validation = validateParams(normalizedIntentType, data.parameters);
        const paramCount = Object.keys(data.parameters).length;

        // Show navigation loading toast
        toast.loading("Đang chuyển trang...", {
          description: `Đang chuyển đến ${intentInfo.name}`,
          duration: 1500,
          id: "voice-navigate", // Use ID to dismiss later
        });

        // Navigate to the appropriate screen
        if (data.intent_changed) {
          console.log("🔄 Intent changed, navigating to:", data.intent_type);
        }

        router.push(intentInfo.route);

        // Dismiss loading toast and show result after navigation
        setTimeout(() => {
          toast.dismiss("voice-navigate");

          if (normalizedIntentType === "unknown") {
            // Special handling for unknown intent
            toast.warning("Không nhận dạng được lệnh", {
              description: `Nội dung: "${data.asr_text}". Vui lòng thử lại với câu lệnh rõ ràng hơn.`,
              duration: 5000,
            });
          } else if (!validation.valid) {
            // Missing required parameters
            toast.warning(`${intentInfo.name}`, {
              description: `Thiếu thông tin: ${validation.missing.join(", ")}. Vui lòng bổ sung thêm.`,
              duration: 5000,
            });
            console.log("⚠️ Missing params:", validation.missing);
          } else {
            // All parameters valid - success
            toast.success(`${intentInfo.name}`, {
              description: `Đã nhận dạng ${paramCount} thông tin. Vui lòng kiểm tra và xác nhận.`,
              duration: 4000,
            });
          }
        }, 800); // Wait 800ms for navigation to complete

        console.log("📝 Form will be auto-filled with:", data.parameters);
      } else {
        // Intent type not mapped - show error
        console.error("❌ Unknown intent type:", data.intent_type);
        toast.error("Lỗi hệ thống", {
          description: `Intent type "${data.intent_type}" chưa được hỗ trợ. Vui lòng liên hệ admin.`,
          duration: 5000,
        });
      }

      // Always disconnect after intent extraction - no confirmation dialog
      disconnect();
    },
    onExecutionSuccess: (data) => {
      console.log("✅ Execution success:", data);
      setIsProcessing(false);

      // Clear voice data
      setTranscript("");
      setNormalizedText("");
      setExtractedIntent(null);

      // Show success toast
      toast.success(data.message || "Thực hiện thành công!", {
        description: "Dữ liệu đã được cập nhật",
      });

      // Disconnect WebSocket after successful execution
      disconnect();

      // Reload page to refresh data
      router.refresh();
    },
    onExecutionError: (err) => {
      console.error("❌ Execution error:", err);
      setError(err);
      setIsProcessing(false);

      // Show error toast with details
      toast.error("Không thể thực hiện", {
        description: err,
        duration: 5000,
      });

      // Disconnect on error
      disconnect();
    },
    onError: (err) => {
      console.error("❌ WebSocket error:", err);
      setError(err);
      setIsProcessing(false);

      // Show error toast
      toast.error("Lỗi nhận dạng giọng nói", {
        description: err,
        duration: 5000,
      });

      // Disconnect on error
      disconnect();
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

        // Create AudioContext for processing raw audio
        const audioContext = new AudioContext({ sampleRate: 16000 });
        audioContextRef.current = audioContext;

        // Load AudioWorklet module
        await audioContext.audioWorklet.addModule("/recorder-worklet.js");

        const source = audioContext.createMediaStreamSource(stream);

        // Create AudioWorkletNode
        const workletNode = new AudioWorkletNode(audioContext, "recorder-worklet");
        workletNodeRef.current = workletNode;

        // Accumulate audio chunks
        audioBufferRef.current = [];
        let lastSendTime = Date.now();
        const SEND_INTERVAL = 5000; // Send every 5 seconds

        // Listen to messages from the worklet
        workletNode.port.onmessage = (event) => {
          if (event.data.type === "audio-data") {
            const chunk = event.data.data as Float32Array;
            audioBufferRef.current.push(chunk);

            // Send accumulated chunks every 5 seconds
            const now = Date.now();
            if (now - lastSendTime >= SEND_INTERVAL) {
              sendAccumulatedAudio();
              lastSendTime = now;
            }
          }
        };

        // Connect the audio graph
        source.connect(workletNode);
        // Note: We don't connect to destination to avoid echo

        console.log("🎙️ Recording started! Capturing raw PCM audio via AudioWorklet");
        setIsListening(true);
        setIsRecordingDialogOpen(true); // Show dialog
      } catch (err) {
        console.error("Error in startListening:", err);
        setError("Microphone access denied");
        console.error("Error accessing microphone:", err);
        disconnect();
      }
    },
    [connect, disconnect, isReady, sendAudioChunk, isListening, isConnected]
  );

  // Helper function to send accumulated audio
  const sendAccumulatedAudio = useCallback(() => {
    if (audioBufferRef.current.length === 0) return;

    // Merge all chunks into single Float32Array
    const totalLength = audioBufferRef.current.reduce((sum, chunk) => sum + chunk.length, 0);
    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of audioBufferRef.current) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    // Encode to WAV
    const wavBuffer = encodeWav(merged, 16000);

    console.log(
      `📤 Sending WAV chunk: ${audioBufferRef.current.length} buffers, ${totalLength} samples, ${wavBuffer.byteLength} bytes`
    );

    // Send to backend
    sendAudioChunk(wavBuffer);

    // Clear buffer
    audioBufferRef.current = [];
  }, [sendAudioChunk]);

  const stopListening = useCallback(async () => {
    console.log("⏹️ Stopping recording...");
    setIsProcessing(true);

    try {
      // Send any remaining audio
      sendAccumulatedAudio();

      // Stop audio processing
      if (workletNodeRef.current) {
        workletNodeRef.current.disconnect();
        workletNodeRef.current.port.onmessage = null;
        workletNodeRef.current = null;
      }

      if (audioContextRef.current) {
        await audioContextRef.current.close();
        audioContextRef.current = null;
      }

      // Notify backend that recording stopped
      stopRecording();

      setIsListening(false);
      setIsRecordingDialogOpen(false); // Close dialog

      // Stop all tracks using utility function
      stopMediaStream(audioStreamRef.current, "stopListening");
      audioStreamRef.current = null;

      // Clear buffer
      audioBufferRef.current = [];

      // DON'T close WebSocket yet - wait for backend response
      // disconnect() will be called after receiving intent_extracted or execution_success

      console.log("✅ Recording stopped, waiting for backend response...");
    } catch (err) {
      console.error("Error stopping recording:", err);
      setError("Failed to stop recording");

      // Cleanup on error
      if (workletNodeRef.current) {
        workletNodeRef.current.disconnect();
        workletNodeRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      stopMediaStream(audioStreamRef.current, "stopListening-error");
      audioStreamRef.current = null;
      audioBufferRef.current = [];

      disconnect(); // Only disconnect on error
    }
    // Don't set isProcessing to false here - will be set when response arrives
  }, [stopRecording, disconnect, sendAccumulatedAudio]);

  const cancelRecording = useCallback(() => {
    console.log("❌ Cancelling recording...");

    // Send cancel message to backend
    wsCancelRecording();

    // Stop audio processing
    if (workletNodeRef.current) {
      workletNodeRef.current.disconnect();
      workletNodeRef.current.port.onmessage = null;
      workletNodeRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Stop media stream
    stopMediaStream(audioStreamRef.current, "cancelRecording");
    audioStreamRef.current = null;

    // Clear buffer
    audioBufferRef.current = [];

    // Disconnect WebSocket
    disconnect();

    setIsListening(false);
    setIsRecordingDialogOpen(false);
    setIsProcessing(false);
    setTranscript("");
    setNormalizedText("");
    setExtractedIntent(null);

    console.log("🗑️ Recording cancelled and discarded");
  }, [disconnect, wsCancelRecording]);

  const clearTranscript = useCallback(() => {
    setTranscript("");
    setNormalizedText("");
    setError(null);
    setExtractedIntent(null);
  }, []);

  const confirmExecution = useCallback(() => {
    if (!extractedIntent) {
      console.error("❌ No intent to execute");
      return;
    }

    console.log("✅ Confirming execution:", extractedIntent);
    setIsProcessing(true);
    wsConfirmExecution(extractedIntent.intent_type, extractedIntent.parameters);
  }, [extractedIntent, wsConfirmExecution]);

  const cancelExecution = useCallback(() => {
    console.log("❌ Cancelling execution from confirmation dialog...");

    // Send cancel message to backend
    wsCancelRecording();

    // Disconnect WebSocket
    disconnect();

    // Reset all states
    setIsProcessing(false);
    setTranscript("");
    setNormalizedText("");
    setExtractedIntent(null);

    console.log("🗑️ Execution cancelled");
  }, [disconnect, wsCancelRecording]);

  // Cleanup on unmount only
  useEffect(() => {
    return () => {
      console.log("🧹 SpeechContext unmounting - cleaning up resources");

      // Stop audio processing
      if (workletNodeRef.current) {
        workletNodeRef.current.disconnect();
        workletNodeRef.current = null;
      }

      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }

      // Stop media stream
      stopMediaStream(audioStreamRef.current, "unmount");
      audioStreamRef.current = null;

      // Clear buffer
      audioBufferRef.current = [];

      // Disconnect WebSocket
      disconnect();

      console.log("✅ SpeechContext cleanup complete");
    };
  }, [disconnect]);

  return (
    <SpeechContext.Provider
      value={{
        isListening,
        isRecordingDialogOpen,
        transcript,
        normalizedText,
        isProcessing,
        error,
        startListening,
        stopListening,
        cancelRecording,
        clearTranscript,
        extractedIntent,
        confirmExecution,
        cancelExecution,
        isConnected,
      }}>
      {children}

      {/* Voice Recording Dialog - Only dialog we need */}
      <VoiceRecordingDialog
        open={isRecordingDialogOpen}
        onClose={cancelRecording}
        onStop={stopListening}
        isProcessing={isProcessing}
      />
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
