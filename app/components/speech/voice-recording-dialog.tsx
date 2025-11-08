"use client";

import { useEffect, useRef } from "react";
import { X, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogPortal,
  DialogOverlay,
} from "@/components/ui/dialog";
import { useAppStore } from "@/lib/stores/app-store";
import * as DialogPrimitive from "@radix-ui/react-dialog";

interface VoiceRecordingDialogProps {
  open: boolean;
  onClose: () => void;
  onStop: () => void;
  isProcessing?: boolean;
}

export function VoiceRecordingDialog({ open, onClose, onStop, isProcessing = false }: VoiceRecordingDialogProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | undefined>(undefined);
  const audioContextRef = useRef<AudioContext | undefined>(undefined);
  const analyserRef = useRef<AnalyserNode | undefined>(undefined);
  const dataArrayRef = useRef<Uint8Array | undefined>(undefined);
  const streamRef = useRef<MediaStream | undefined>(undefined); // 🔥 Lưu stream để cleanup

  useEffect(() => {
    if (!open) return;

    // Create audio context and analyser for visualization
    const setupAudioVisualization = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream; // 🔥 Lưu stream reference

        audioContextRef.current = new AudioContext();
        analyserRef.current = audioContextRef.current.createAnalyser();
        analyserRef.current.fftSize = 256;

        const source = audioContextRef.current.createMediaStreamSource(stream);
        source.connect(analyserRef.current);

        const bufferLength = analyserRef.current.frequencyBinCount;
        dataArrayRef.current = new Uint8Array(bufferLength);

        drawWaveform();
      } catch (err) {
        console.error("Error setting up audio visualization:", err);
      }
    };

    setupAudioVisualization();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }

      if (audioContextRef.current) {
        audioContextRef.current.close();
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => {
          track.stop();
          console.log("🎤 Stopped microphone track:", track.label);
        });
        streamRef.current = undefined;
      }
    };
  }, [open]);

  const drawWaveform = () => {
    if (!canvasRef.current || !analyserRef.current || !dataArrayRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx || !dataArrayRef.current) return;

    const WIDTH = canvas.width;
    const HEIGHT = canvas.height;
    const bufferLength = analyserRef.current.frequencyBinCount;

    // @ts-ignore - TypeScript strict checking for Uint8Array buffer type
    analyserRef.current.getByteFrequencyData(dataArrayRef.current);

    ctx.clearRect(0, 0, WIDTH, HEIGHT);

    // Draw wave bars
    const barWidth = (WIDTH / bufferLength) * 2.5;
    let barHeight;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      barHeight = (dataArrayRef.current[i] / 255) * HEIGHT * 0.8;

      // Create gradient (blue-600 to emerald-600)
      const gradient = ctx.createLinearGradient(0, HEIGHT - barHeight, 0, HEIGHT);
      gradient.addColorStop(0, "rgba(37, 99, 235, 0.8)"); // blue-600
      gradient.addColorStop(1, "rgba(5, 150, 105, 0.8)"); // emerald-600

      ctx.fillStyle = gradient;
      ctx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);

      x += barWidth + 2;
    }

    animationRef.current = requestAnimationFrame(drawWaveform);
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogPortal>
        {/* Custom overlay with higher z-index and transparent on mobile */}
        <DialogPrimitive.Overlay className="fixed inset-0 z-90 bg-transparent md:bg-gray-800/50 md:backdrop-blur-xs data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 pointer-events-none md:pointer-events-auto" />

        <DialogPrimitive.Content className="fixed left-[50%] sm:top-[50%] bottom-24 sm:bottom-auto top-auto translate-x-[-50%] translate-y-0 sm:translate-y-[-50%] z-100 sm:max-w-[400px] max-w-[90vw] rounded-2xl p-4 bg-background border border-border shadow-lg pointer-events-auto data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
          <DialogHeader className="sr-only">
            <DialogTitle>Đang ghi âm</DialogTitle>
            <DialogDescription>Ghi âm giọng nói đang tiến hành</DialogDescription>
          </DialogHeader>

          <div className="flex flex-col items-center gap-4">
            {/* Waveform Visualization - Compact */}
            <div className="relative w-full h-24 bg-linear-to-br from-blue-50 to-emerald-50 dark:from-blue-950/20 dark:to-emerald-950/20 rounded-lg overflow-hidden">
              <canvas ref={canvasRef} width={320} height={96} className="w-full h-full" />

              {/* Pulsing indicator when processing */}
              {isProcessing && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-sm">
                  <div className="relative">
                    <div className="absolute inset-0 bg-blue-500 rounded-full animate-ping opacity-75" />
                    <div className="relative bg-linear-to-r from-blue-600 to-emerald-600 rounded-full p-3">
                      <Check className="w-5 h-5 text-white" />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons - Compact */}
            <div className="flex items-center justify-center gap-6">
              {/* Cancel Button (X) */}
              <Button
                variant="outline"
                size="icon"
                onClick={onClose}
                disabled={isProcessing}
                className="rounded-full h-12 w-12 border-2"
                title="Hủy">
                <X className="w-5 h-5" />
              </Button>

              {/* Stop & Save Button (Check) */}
              <Button
                size="icon"
                onClick={onStop}
                disabled={isProcessing}
                className="rounded-full h-14 w-14 bg-linear-to-r from-blue-600 to-emerald-600 hover:from-blue-700 hover:to-emerald-700 shadow-lg"
                title="Dừng và lưu">
                <Check className="w-6 h-6" />
              </Button>
            </div>
          </div>
        </DialogPrimitive.Content>
      </DialogPortal>
    </Dialog>
  );
}
