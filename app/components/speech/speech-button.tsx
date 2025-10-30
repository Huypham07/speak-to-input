"use client";

import { useSpeech } from "@/lib/speech-context";
import { Mic, Square } from "lucide-react";

export function SpeechButton() {
  const { isListening, isProcessing, startListening, stopListening } = useSpeech();

  const handleClick = async () => {
    if (isListening) {
      await stopListening();
    } else {
      await startListening();
    }
  };

  return (
    <>
      {/* Desktop Speech Button */}
      <button
        onClick={handleClick}
        disabled={isProcessing}
        className="hidden md:flex items-center justify-center w-14 h-14 rounded-full bg-linear-to-r from-blue-600 to-emerald-600 text-white shadow-lg hover:shadow-xl transition-all hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed relative">
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
        disabled={isProcessing}
        className="md:hidden fixed bottom-10 left-1/2 -translate-x-1/2 z-50 flex items-center justify-center w-20 h-20 rounded-full bg-linear-to-r from-blue-600 to-emerald-600 text-white shadow-2xl hover:shadow-3xl transition-all hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed">
        {isListening ? (
          <>
            <Square className="h-8 w-8" />
            <span className="absolute inset-0 rounded-full animate-pulse bg-red-500/20" />
          </>
        ) : (
          <Mic className="h-8 w-8" />
        )}
      </button>
    </>
  );
}
