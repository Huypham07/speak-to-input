"use client";

import { useAuth } from "@/lib/auth-context";
import { useSidebar } from "@/lib/sidebar-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { FundsList } from "@/components/dashboard/funds-list";
import { FundForm } from "@/components/financial/fund-form";
import { FormDialog, FormDialogHeader, FormDialogTitle } from "@/components/ui/form-dialog";
import { ChevronLeft } from "lucide-react";
import { useSpeech } from "@/lib/speech-context";
import { useAppStore } from "@/lib/stores/app-store";
import { useFinancial } from "@/lib/financial-context";

export default function FundsPage() {
  const { user, isLoading } = useAuth();
  const { isCollapsed } = useSidebar();
  const router = useRouter();
  const [isCreating, setIsCreating] = useState(false);
  const { extractedIntent } = useSpeech();
  const isRecording = useAppStore((state) => state.isRecording);
  const { refreshFunds } = useFinancial();

  // Auto-open dialog for fund-related voice intents
  useEffect(() => {
    if (!extractedIntent) return;

    const { intent_type, parameters } = extractedIntent;

    // Handle CREATE_FUND - auto-open dialog when intent is detected
    if (intent_type === "create_fund") {
      // Open dialog after a delay to ensure page is rendered
      setTimeout(() => {
        setIsCreating(true);
      }, 300);
      return;
    }

    // Handle DEPOSIT_FUND and WITHDRAW_FUND - can handle even if navigated here
    if (intent_type === "deposit_fund" || intent_type === "withdraw_fund") {
      // For deposit/withdraw, we need to select which fund
      // This will be handled by opening a dialog/form
      // For now, just open the create dialog as placeholder
      // TODO: Implement fund selection dialog
      console.log(`📝 [FundsPage] Handling ${intent_type} with params:`, parameters);
      // Don't auto-open for now, let user select fund from list
      // setIsCreating(true);
    }
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
              <h1 className="text-2xl md:text-3xl font-bold text-foreground">Quỹ tiết kiệm</h1>
              <p className="text-muted-foreground mt-2">Quản lý các quỹ tiết kiệm của bạn</p>
            </div>
          </div>

          {/* Funds List */}
          <FundsList onCreateFund={() => setIsCreating(true)} />
        </div>
      </main>

      {/* Create Fund Modal */}
      <FormDialog
        open={isCreating}
        onOpenChange={handleOpenChange}
        className="max-w-2xl w-[95vw] sm:w-full max-h-[calc(85vh-5rem)] sm:max-h-[90vh] flex flex-col p-0 rounded-xl sm:rounded-2xl gap-0">
        <FormDialogHeader className="px-4 sm:px-6 pt-4 sm:pt-6 pb-3 sm:pb-4 border-b shrink-0">
          <FormDialogTitle className="text-lg sm:text-xl">Tạo quỹ tiết kiệm</FormDialogTitle>
        </FormDialogHeader>
        <div className="overflow-y-auto flex-1 px-4 sm:px-6 pt-3 sm:pt-4">
          <FundForm
            onSuccess={() => {
              setIsCreating(false);
              refreshFunds(); // Refresh funds list after creating
            }}
          />
        </div>
      </FormDialog>
    </div>
  );
}
