"use client";

import { useSpeech } from "@/lib/speech-context";
import { matchCommand } from "@/lib/command-registry";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertCircle, CheckCircle2, X } from "lucide-react";

interface SpeechResultModalProps {
  onCommandMatched: (command: string, data: Record<string, any>) => void;
  onClose: () => void;
}

export function SpeechResultModal({ onCommandMatched, onClose }: SpeechResultModalProps) {
  const { transcript, error, clearTranscript } = useSpeech();

  if (!transcript && !error) return null;

  const matchedCommand = transcript ? matchCommand(transcript) : null;

  const handleUseCommand = () => {
    if (matchedCommand) {
      onCommandMatched(matchedCommand.command.id, matchedCommand.data);
      clearTranscript();
      onClose();
    }
  };

  const handleClose = () => {
    clearTranscript();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={handleClose}>
      <Card className="w-full max-w-md" onClick={(e) => e.stopPropagation()}>
        <CardHeader className="relative">
          <button
            onClick={handleClose}
            className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none">
            <X className="h-4 w-4" />
            <span className="sr-only">Đóng</span>
          </button>
          <CardTitle className="flex items-center gap-2">
            {error ? (
              <>
                <AlertCircle className="h-5 w-5 text-destructive" />
                Lỗi
              </>
            ) : matchedCommand ? (
              <>
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                Đã nhận diện lệnh
              </>
            ) : (
              <>
                <AlertCircle className="h-5 w-5 text-yellow-600" />
                Không tìm thấy lệnh
              </>
            )}
          </CardTitle>
          <CardDescription>Kết quả xử lý giọng nói</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-muted p-3 rounded-md">
            <p className="text-sm font-medium mb-1">Nội dung:</p>
            <p className="text-sm text-muted-foreground italic">{transcript || error}</p>
          </div>

          {matchedCommand && (
            <div className="bg-green-50 dark:bg-green-950 p-3 rounded-md">
              <p className="text-sm font-medium mb-2">Lệnh được phát hiện:</p>
              <p className="text-sm font-semibold text-green-700 dark:text-green-300 mb-2">
                {matchedCommand.command.name}
              </p>
              <div className="text-xs space-y-1">
                {Object.entries(matchedCommand.data).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-muted-foreground">{key}:</span>
                    <span className="font-medium">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2">
            {matchedCommand && (
              <Button onClick={handleUseCommand} className="flex-1">
                Sử dụng lệnh này
              </Button>
            )}
            <Button onClick={handleClose} variant="outline" className="flex-1">
              Đóng
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
