"use client";

import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useAppStore } from "@/lib/stores/app-store";

export function VoiceProcessingOverlay() {
  const isProcessingVoice = useAppStore((state) => state.isProcessingVoice);
  const voiceLoadingMode = useAppStore((state) => state.voiceLoadingMode);

  // Prevent body scroll when overlay is visible
  useEffect(() => {
    if (isProcessingVoice && voiceLoadingMode === "loading") {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.body.style.overflow = "";
    };
  }, [isProcessingVoice, voiceLoadingMode]);

  if (!isProcessingVoice || voiceLoadingMode !== "loading") {
    return null;
  }

  return (
    <div className="fixed inset-0 z-9999 flex items-center justify-center bg-gray-800/70 backdrop-blur-xs pointer-events-none md:pointer-events-auto transition-opacity duration-300">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl p-8 flex flex-col items-center gap-6 max-w-sm mx-4 pointer-events-auto animate-in fade-in zoom-in-95 duration-300">
        {/* Animated loader */}
        <div className="relative w-20 h-20 flex items-center justify-center">
          {/* Pulsing background circle */}
          <div className="absolute inset-0 bg-linear-to-r from-blue-500 to-emerald-500 rounded-full opacity-20 animate-pulse" />
          {/* Spinning outer ring */}
          <div
            className="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-600 border-r-blue-600 animate-spin"
            style={{ animationDuration: "1s" }}
          />
        </div>

        {/* Text */}
        <div className="text-center space-y-2">
          <h3 className="text-xl font-semibold text-foreground">Đang xử lý giọng nói</h3>
          <p className="text-sm text-muted-foreground">Vui lòng đợi trong giây lát...</p>
        </div>

        {/* Progress animation */}
        <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5 overflow-hidden">
          <div
            className="h-full bg-linear-to-r from-blue-600 to-emerald-600 rounded-full animate-[progress_2s_ease-in-out_infinite]"
            style={{ willChange: "transform" }}
          />
        </div>
      </div>
    </div>
  );
}
