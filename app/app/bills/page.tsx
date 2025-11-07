"use client";

import { useAuth } from "@/lib/auth-context";
import { useSidebar } from "@/lib/sidebar-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { BillsList } from "@/components/dashboard/bills-list";
import { BillForm } from "@/components/financial/bill-form";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ChevronLeft } from "lucide-react";
import { useSpeech } from "@/lib/speech-context";
import { VoiceFormSync } from "@/components/speech/voice-form-sync";

export default function BillsPage() {
  const { user, isLoading } = useAuth();
  const { isCollapsed } = useSidebar();
  const router = useRouter();
  const [isCreating, setIsCreating] = useState(false);
  const { extractedIntent } = useSpeech();

  // Auto-open dialog ONLY when voice intent has sufficient parameters
  useEffect(() => {
    if (!extractedIntent || extractedIntent.intent_changed) return;

    const { intent_type, parameters } = extractedIntent;

    // CREATE_BILL: Auto-open if has basic info (bill_name or amount)
    if (intent_type === "create_bill" && (parameters.bill_name || parameters.amount)) {
      setIsCreating(true);
    }

    // PAY_BILL: Auto-open ONLY if has bill_id (otherwise just navigate to list)
    if (intent_type === "pay_bill" && parameters.bill_id) {
      setIsCreating(true);
    }
  }, [extractedIntent]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

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
      <Dialog open={isCreating} onOpenChange={setIsCreating}>
        <DialogContent className="max-w-2xl w-[95vw] sm:w-full max-h-[85vh] sm:max-h-[90vh] flex flex-col p-0 rounded-xl sm:rounded-2xl gap-0">
          <DialogHeader className="px-4 sm:px-6 pt-4 sm:pt-6 pb-3 sm:pb-4 border-b shrink-0">
            <DialogTitle className="text-lg sm:text-xl">Tạo hóa đơn mới</DialogTitle>
          </DialogHeader>
          <div className="overflow-y-auto flex-1 px-4 sm:px-6 pt-3 sm:pt-4">
            <BillForm onSuccess={() => setIsCreating(false)} />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
