"use client";

import { useAuth } from "@/lib/auth-context";
import { useSidebar } from "@/lib/sidebar-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { BillsList } from "@/components/dashboard/bills-list";
import { BillForm } from "@/components/financial/bill-form";
import { FormDialog, FormDialogHeader, FormDialogTitle } from "@/components/ui/form-dialog";
import { ChevronLeft } from "lucide-react";
import { useSpeech } from "@/lib/speech-context";
import { VoiceFormSync } from "@/components/speech/voice-form-sync";
import { useAppStore } from "@/lib/stores/app-store";
import { useFinancial } from "@/lib/financial-context";

export default function BillsPage() {
  const { user, isLoading } = useAuth();
  const { isCollapsed } = useSidebar();
  const router = useRouter();
  const [isCreating, setIsCreating] = useState(false);
  const { extractedIntent } = useSpeech();
  const isRecording = useAppStore((state) => state.isRecording);
  const { refreshBills } = useFinancial();

  // Auto-open dialog ONLY for CREATE_BILL intent
  useEffect(() => {
    if (!extractedIntent) return;

    const { intent_type } = extractedIntent;

    // STRICTLY only handle create_bill - nothing else
    if (intent_type !== "create_bill") {
      return; // Exit early for all other intents
    }

    // Open dialog after a delay to ensure page is rendered
    setTimeout(() => {
      setIsCreating(true);
    }, 300);
  }, [extractedIntent]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  // Prevent dialog close when recording
  const handleOpenChange = (open: boolean) => {
    if (!open && isRecording) {
      // Don't close dialog while recording
      return;
    }
    setIsCreating(open);
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main
        className={`transition-all duration-300 px-4 sm:px-6 lg:px-8 py-8 pb-24 md:pb-8 ${
          isCollapsed ? "md:ml-20" : "md:ml-64"
        }`}>
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Header with Back Button */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/dashboard")}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              title="Quay lại Dashboard">
              <ChevronLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-foreground">Hóa đơn chi tiêu</h1>
              <p className="text-muted-foreground mt-2">Quản lý các hóa đơn và chi phí của bạn</p>
            </div>
          </div>

          {/* Bills List */}
          <BillsList onCreateBill={() => setIsCreating(true)} />
        </div>
      </main>

      {/* Create Bill Modal */}
      <FormDialog
        open={isCreating}
        onOpenChange={handleOpenChange}
        className="max-w-2xl w-[95vw] sm:w-full max-h-[calc(85vh-5rem)] sm:max-h-[90vh] flex flex-col p-0 rounded-xl sm:rounded-2xl gap-0">
        <FormDialogHeader className="px-4 sm:px-6 pt-4 sm:pt-6 pb-3 sm:pb-4 border-b shrink-0">
          <FormDialogTitle className="text-lg sm:text-xl">Tạo hóa đơn mới</FormDialogTitle>
        </FormDialogHeader>
        <div className="overflow-y-auto flex-1 px-4 sm:px-6 pt-3 sm:pt-4">
          <BillForm
            onSuccess={() => {
              setIsCreating(false);
              refreshBills(); // Refresh bills list after creating
            }}
          />
        </div>
      </FormDialog>
    </div>
  );
}
