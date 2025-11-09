"use client";

import type React from "react";
import { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useVoiceWebSocket } from "@/hooks/use-voice-websocket";
import { useAuth } from "@/lib/auth-context";
import { useAppStore } from "@/lib/stores/app-store";
import { useFormStore } from "@/lib/stores/form-store";
import { VoiceRecordingDialog } from "@/components/speech/voice-recording-dialog";
import { VoiceProcessingOverlay } from "@/components/speech/voice-processing-overlay";
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
  clearIntent: () => void;
  confirmExecution: () => void;
  cancelExecution: () => void;
  isConnected: boolean;
}

const SpeechContext = createContext<SpeechContextType | undefined>(undefined);

export function SpeechProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Zustand stores
  const setIsProcessingVoice = useAppStore((state) => state.setIsProcessingVoice);
  const setIsRecording = useAppStore((state) => state.setIsRecording);
  const currentDialog = useAppStore((state) => state.currentDialog);
  const getCurrentFormContext = useFormStore((state) => state.getCurrentFormContext);

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

  // Track if navigation was triggered by voice command
  const isVoiceNavigationRef = useRef(false);
  const previousPathnameRef = useRef(pathname);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioBufferRef = useRef<Float32Array[]>([]);

  // Sync isProcessing with AppState
  const updateProcessingState = useCallback(
    (processing: boolean) => {
      setIsProcessing(processing);
      setIsProcessingVoice(processing);
    },
    [setIsProcessingVoice]
  );

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
      // Save transcript and normalized text
      setTranscript(data.asr_text);
      setNormalizedText(data.normalized_text);

      // Normalize intent type - convert backend IntentType to frontend intent types
      const normalizeIntentType = (type: string): string => {
        // Map backend IntentType enum to frontend intent types and routes
        const intentMapping: Record<string, string> = {
          // Transaction intents
          SEND_MONEY: "send_money",

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

          // Meta intents
          UNKNOWN: "unknown",
        };

        return intentMapping[type] || type.toLowerCase();
      };

      const normalizedIntentType = normalizeIntentType(data.intent_type);

      // Save intent data with normalized type
      console.log("✅ Setting extractedIntent:", {
        intent_type: normalizedIntentType,
        intent_changed: data.intent_changed,
        action: data.action,
        pathname: pathname,
      });

      setExtractedIntent({
        intent_type: normalizedIntentType,
        parameters: data.parameters,
        intent_changed: data.intent_changed,
        needs_confirmation: data.needs_confirmation,
      });

      updateProcessingState(false);

      // Get suggested action from backend (or default to navigate for backward compatibility)
      const suggestedAction = data.action || "navigate";

      // Map normalized intent types to routes and Vietnamese names
      const intentInfoMap: Record<string, { route: string; name: string }> = {
        // Transaction & Transfer
        send_money: { route: "/accounts?action=transfer", name: "Chuyển tiền" },

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
            send_money: ["amount"], // recipient is validated separately
            create_bill: ["bill_name", "amount"],
            pay_bill: [], // Can use bill_id OR bill_name
            create_fund: ["fund_name", "target_amount"],
            deposit_fund: ["amount"], // Can use fund_id OR fund_name
            withdraw_fund: ["amount"], // Can use fund_id OR fund_name
            delete_fund: [], // Can use fund_id OR fund_name
          };

          const required = requiredParamsMap[intentType] || [];
          const missing = required.filter((key) => !params[key] || params[key] === "");

          // Special validation for transfer - need recipient info
          if (intentType === "send_money") {
            // Accept: recipient OR (recipient_name OR recipient_account_number)
            const hasRecipient = params.recipient || params.recipient_name || params.recipient_account_number;
            if (!hasRecipient) {
              return { valid: false, missing: [...missing, "recipient"] };
            }
          }

          // Special validation for intents that can use either ID or name
          if (intentType === "pay_bill") {
            if (!params.bill_id && !params.bill_name) {
              return { valid: false, missing: ["bill_id hoặc bill_name"] };
            }
          } else if (["deposit_fund", "withdraw_fund", "delete_fund"].includes(intentType)) {
            if (!params.fund_id && !params.fund_name) {
              return { valid: false, missing: ["fund_id hoặc fund_name"] };
            }
          }

          return { valid: missing.length === 0, missing };
        };

        const validation = validateParams(normalizedIntentType, data.parameters);
        const paramCount = Object.keys(data.parameters).length;

        // Handle action based on backend suggestion
        if (suggestedAction === "stay") {
          // Just update form, don't navigate

          if (paramCount > 0) {
            toast.success("Đã cập nhật", {
              description: `Đã nhận dạng ${paramCount} thông tin. Vui lòng kiểm tra.`,
              duration: 3000,
            });
          } else {
            toast.info("Không có thay đổi", {
              description: "Không có thông tin mới để cập nhật.",
              duration: 2000,
            });
          }
        } else if (suggestedAction === "update_form") {
          // Update form without navigation

          toast.success("Đã cập nhật thông tin", {
            description: `Đã nhận dạng ${paramCount} thông tin mới.`,
            duration: 3000,
          });
        } else if (suggestedAction === "open_dialog") {
          // Open dialog without full navigation (if already on page)

          // For now, still navigate to page (dialog opening handled by page's useEffect)
          toast.loading("Đang mở form...", {
            description: `Đang mở ${intentInfo.name}`,
            duration: 1000,
            id: "voice-navigate",
          });

          // Mark as voice navigation before pushing
          isVoiceNavigationRef.current = true;
          router.push(intentInfo.route);

          setTimeout(() => {
            toast.dismiss("voice-navigate");
            toast.success(`${intentInfo.name}`, {
              description: `Đã nhận dạng ${paramCount} thông tin. Vui lòng kiểm tra và xác nhận.`,
              duration: 4000,
            });
          }, 800);
        } else {
          // Default: navigate (backward compatible)

          // Show navigation loading toast
          toast.loading("Đang chuyển trang...", {
            description: `Đang chuyển đến ${intentInfo.name}`,
            duration: 1500,
            id: "voice-navigate",
          });

          // Mark as voice navigation before pushing
          isVoiceNavigationRef.current = true;

          // Navigate to the appropriate screen
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
            } else {
              // All parameters valid
              // For operation intents (deposit, withdraw, pay, delete), don't show success toast
              // Let the component validate data existence and show appropriate message
              const operationIntents = ["deposit_fund", "withdraw_fund", "delete_fund", "pay_bill"];

              if (!operationIntents.includes(normalizedIntentType)) {
                // Only show success toast for create intents
                toast.success(`${intentInfo.name}`, {
                  description: `Đã nhận dạng ${paramCount} thông tin. Vui lòng kiểm tra và xác nhận.`,
                  duration: 4000,
                });
              }
            }
          }, 800); // Wait 800ms for navigation to complete
        }
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
      updateProcessingState(false);

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
      updateProcessingState(false);

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
      updateProcessingState(false);

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
        return;
      }

      try {
        // Get current form context from store
        const formContext = getCurrentFormContext();
        const contextFormData = formData || formContext.data;
        const contextIntentType = intentType || formContext.type;

        console.log("🎤 startListening called with:", {
          passedFormData: formData,
          passedIntentType: intentType,
          storeFormType: formContext.type,
          storeFormData: formContext.data,
          finalFormData: contextFormData,
          finalIntentType: contextIntentType,
          pathname: pathname,
        });
        console.log("📦 Full contextFormData:", JSON.stringify(contextFormData, null, 2));
        console.log("📦 Full finalIntentType:", contextIntentType);

        setError(null);
        setTranscript("");
        setExtractedIntent(null);

        let actualToken = localStorage.getItem("access_token");

        if (!actualToken) {
          console.error("❌ NO TOKEN FOUND - STOPPING");
          setError("Authentication required - No access token found");
          return;
        }

        // Prepare context data to send to backend
        const contextData = {
          formData: contextFormData,
          intentType: contextIntentType,
          currentPage: pathname,
          currentDialog: currentDialog.isOpen
            ? {
                type: currentDialog.type,
                data: currentDialog.data,
              }
            : null,
        };

        // Connect to WebSocket with context
        await connect(actualToken, contextData.formData, contextData.intentType ?? undefined);

        // Mark as recording
        setIsRecording(true);

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

        setIsListening(true);
        setIsRecordingDialogOpen(true); // Show dialog
      } catch (err) {
        console.error("Error in startListening:", err);
        setError("Microphone access denied");
        console.error("Error accessing microphone:", err);
        disconnect();
      }
    },
    [
      connect,
      disconnect,
      isReady,
      sendAudioChunk,
      isListening,
      isConnected,
      pathname,
      currentDialog,
      getCurrentFormContext,
      setIsRecording,
    ]
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

    // Send to backend
    sendAudioChunk(wavBuffer);

    // Clear buffer
    audioBufferRef.current = [];
  }, [sendAudioChunk]);

  const stopListening = useCallback(async () => {
    updateProcessingState(true);

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
      setIsRecording(false); // Clear recording state
      setIsRecordingDialogOpen(false); // Close dialog

      // Stop all tracks using utility function
      stopMediaStream(audioStreamRef.current, "stopListening");
      audioStreamRef.current = null;

      // Clear buffer
      audioBufferRef.current = [];

      // DON'T close WebSocket yet - wait for backend response
      // disconnect() will be called after receiving intent_extracted or execution_success
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
    setIsRecording(false); // Clear recording state
    setIsRecordingDialogOpen(false);
    updateProcessingState(false);
    setTranscript("");
    setNormalizedText("");
    setExtractedIntent(null);
  }, [disconnect, wsCancelRecording, setIsRecording]);

  const clearTranscript = useCallback(() => {
    setTranscript("");
    setNormalizedText("");
    setError(null);
    setExtractedIntent(null);
  }, []);

  const clearIntent = useCallback(() => {
    setExtractedIntent(null);
  }, []);

  const confirmExecution = useCallback(() => {
    if (!extractedIntent) {
      return;
    }

    updateProcessingState(true);
    wsConfirmExecution(extractedIntent.intent_type, extractedIntent.parameters);
  }, [extractedIntent, wsConfirmExecution, updateProcessingState]);

  const cancelExecution = useCallback(() => {
    // Send cancel message to backend
    wsCancelRecording();

    // Disconnect WebSocket
    disconnect();

    // Reset all states
    updateProcessingState(false);
    setTranscript("");
    setNormalizedText("");
    setExtractedIntent(null);
  }, [disconnect, wsCancelRecording, updateProcessingState]);

  // Cleanup on unmount only
  useEffect(() => {
    return () => {
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
    };
  }, [disconnect]);

  // Clear extractedIntent when user navigates to a different page
  useEffect(() => {
    // Only clear intent if this is a manual navigation (not triggered by voice)
    if (pathname !== previousPathnameRef.current) {
      if (isVoiceNavigationRef.current) {
        // This is a voice-triggered navigation, don't clear intent yet
        // Intent will be used by the new page's form
        console.log("🔄 Voice navigation to:", pathname, "- Keeping extractedIntent for form filling");
        isVoiceNavigationRef.current = false; // Reset flag
      } else {
        // This is a manual navigation (user clicked link), clear intent
        console.log("🔄 Manual navigation to:", pathname, "- Clearing extractedIntent");
        setExtractedIntent(null);
      }
      previousPathnameRef.current = pathname;
    }
  }, [pathname]);

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
        clearIntent,
        confirmExecution,
        cancelExecution,
        isConnected,
      }}>
      {children}

      {/* Voice Recording Dialog - Shows waveform during recording */}
      <VoiceRecordingDialog
        open={isRecordingDialogOpen}
        onClose={cancelRecording}
        onStop={stopListening}
        isProcessing={isProcessing}
      />

      {/* Voice Processing Overlay - Shows when processing voice */}
      <VoiceProcessingOverlay />
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
