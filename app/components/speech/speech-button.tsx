"use client";

import { useSpeech } from "@/lib/speech-context";
import { useFormContext } from "@/lib/form-context";
import { Mic, Square } from "lucide-react";

export function SpeechButton() {
  const { isListening, isProcessing, startListening, stopListening, isConnected } = useSpeech();
  const { currentForm } = useFormContext();

  const handleClick = async () => {
    if (isListening) {
      await stopListening();
    } else {
      // Start listening with current form data and intent type
      await startListening(currentForm.data, currentForm.type ?? undefined);
    }
  };

  const isDisabled = isProcessing || (!isListening && !isConnected && currentForm.type !== null);

  return (
    <>
      {/* Desktop Speech Button */}
      <button
        onClick={handleClick}
        disabled={isDisabled}
        className="hidden md:flex items-center justify-center w-14 h-14 rounded-full bg-linear-to-r from-blue-600 to-emerald-600 text-white shadow-lg hover:shadow-xl transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed relative"
        title={isListening ? "Dừng ghi âm" : "Bắt đầu ghi âm"}>
        {isListening ? (
          <>
            <Square className="h-6 w-6" />
            <span className="absolute inset-0 rounded-full animate-pulse bg-red-500/20" />
          </>
        ) : (
          <Mic className="h-6 w-6" />
        )}
      </button>

      {/* Mobile Speech Button - Floating over bottom nav */}
      <button
        onClick={handleClick}
        disabled={isDisabled}
        className="md:hidden fixed bottom-24 right-4 z-50 flex items-center justify-center w-16 h-16 rounded-full bg-linear-to-r from-blue-600 to-emerald-600 text-white shadow-2xl hover:shadow-3xl transition-all hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed"
        title={isListening ? "Dừng ghi âm" : "Bắt đầu ghi âm"}>
        {isListening ? (
          <>
            <Square className="h-7 w-7" />
            <span className="absolute inset-0 rounded-full animate-pulse bg-red-500/20" />
          </>
        ) : (
          <Mic className="h-7 w-7" />
        )}
      </button>
    </>
  );
}
