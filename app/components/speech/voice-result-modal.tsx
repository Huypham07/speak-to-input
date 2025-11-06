"use client";

import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useSpeech } from "@/lib/speech-context";
import { VoiceConfirmationDialog } from "./voice-confirmation-dialog";
import { CheckCircle2, XCircle } from "lucide-react";

interface VoiceResultModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function VoiceResultModal({ open, onOpenChange }: VoiceResultModalProps) {
  const { extractedIntent, transcript, normalizedText, error } = useSpeech();
  const [showConfirmation, setShowConfirmation] = useState(false);

  // Auto-show confirmation dialog when intent is extracted and needs confirmation
  useEffect(() => {
    if (extractedIntent && extractedIntent.needs_confirmation && open) {
      setShowConfirmation(true);
    }
  }, [extractedIntent, open]);

  const handleClose = () => {
    setShowConfirmation(false);
    onOpenChange(false);
  };

  if (!extractedIntent && !error) {
    return null;
  }

  return (
    <>
      <Dialog open={open && !showConfirmation} onOpenChange={handleClose}>
        <DialogContent className="sm:max-w-[500px] max-w-[90vw]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {error ? (
                <>
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span>Lỗi xử lý</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  <span>Kết quả</span>
                </>
              )}
            </DialogTitle>
            <DialogDescription className="sr-only">
              {error ? "Kết quả xử lý lỗi" : "Kết quả nhận dạng lệnh thoại"}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 pt-2">
            {error ? (
              <div className="bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <span className="text-sm text-red-800 dark:text-red-300">{error}</span>
              </div>
            ) : (
              <>
                <div>
                  <span className="text-sm font-medium text-foreground">Bạn đã nói: </span>
                  <span className="text-sm text-muted-foreground italic">"{transcript}"</span>
                </div>

                {normalizedText && normalizedText !== transcript && (
                  <div>
                    <span className="text-sm font-medium text-foreground">Đã chuyển đổi: </span>
                    <span className="text-sm text-muted-foreground">"{normalizedText}"</span>
                  </div>
                )}

                {extractedIntent && (
                  <div className="pt-2 border-t">
                    <div className="text-sm font-medium text-foreground mb-2">
                      Hành động đã nhận diện: {extractedIntent.intent_type}
                    </div>
                    <div className="space-y-1">
                      {Object.entries(extractedIntent.parameters).map(([key, value]) => (
                        <div key={key} className="text-sm">
                          <span className="font-medium">{key}:</span>{" "}
                          <span className="text-muted-foreground">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {extractedIntent?.intent_changed && (
                  <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                    <span className="text-sm text-blue-800 dark:text-blue-300">
                      ℹ️ Hệ thống đã chuyển sang màn hình phù hợp với yêu cầu của bạn.
                    </span>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="flex justify-end pt-4">
            <Button onClick={handleClose}>Đóng</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Confirmation Dialog */}
      <VoiceConfirmationDialog open={showConfirmation} onOpenChange={setShowConfirmation} />
    </>
  );
}
