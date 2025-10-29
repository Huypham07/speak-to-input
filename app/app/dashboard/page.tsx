"use client";

import { useAuth } from "@/lib/auth-context";
import { useSidebar } from "@/lib/sidebar-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { BalanceCard } from "@/components/dashboard/balance-card";
import { StatisticsOverview } from "@/components/dashboard/statistics-overview";
import { TransfersList } from "@/components/dashboard/transfers-list";
import { BillsList } from "@/components/dashboard/bills-list";
import { FundsList } from "@/components/dashboard/funds-list";
import { TransferForm } from "@/components/financial/transfer-form";
import { BillForm } from "@/components/financial/bill-form";
import { FundForm } from "@/components/financial/fund-form";
import { SpeechResultModal } from "@/components/speech/speech-result-modal";
import { useSpeech } from "@/lib/speech-context";
import { useFinancial } from "@/lib/financial-context";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

type ActiveForm = "transfer" | "bill" | "fund" | null;

export default function DashboardPage() {
  const { user } = useAuth();
  const { isCollapsed } = useSidebar();
  const router = useRouter();
  const [activeForm, setActiveForm] = useState<ActiveForm>(null);
  const { transcript } = useSpeech();
  const { addTransfer, addBill, addFund } = useFinancial();

  useEffect(() => {
    if (!user) {
      router.push("/login");
    }
  }, [user, router]);

  const handleCommandMatched = (commandId: string, data: Record<string, any>) => {
    switch (commandId) {
      case "transfer":
        addTransfer({
          recipientName: data.recipientName,
          recipientAccount: data.recipientAccount,
          amount: data.amount,
          description: data.description || "",
        });
        break;
      case "bill":
        addBill({
          title: data.title,
          category: data.category,
          amount: data.amount,
          dueDate: data.dueDate,
          description: data.description || "",
          status: "pending",
          tags: [],
        });
        break;
      case "fund":
        addFund({
          name: data.name,
          targetAmount: data.targetAmount,
          currentAmount: data.currentAmount || 0,
          description: data.description || "",
          deadline: data.deadline,
          category: data.category,
          priority: data.priority || "medium",
        });
        break;
    }
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
          <div>
            <p className="text-sm text-muted-foreground">Xin chào,</p>
            <h1 className="text-xl md:text-2xl font-semibold text-foreground">{user.name}</h1>
          </div>

          {/* Balance Card */}
          <BalanceCard />

          {/* Statistics Overview - Thay thế Quick Actions */}
          <StatisticsOverview />

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <TransfersList />
            <BillsList />
          </div>

          {/* Funds */}
          <FundsList />
        </div>
      </main>

      {/* Forms Modal */}
      <Dialog open={activeForm !== null} onOpenChange={(open) => !open && setActiveForm(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {activeForm === "transfer"
                ? "Chuyển tiền"
                : activeForm === "bill"
                ? "Tạo hóa đơn chi tiêu"
                : "Tạo quỹ tiết kiệm"}
            </DialogTitle>
          </DialogHeader>
          {activeForm === "transfer" && <TransferForm onSuccess={() => setActiveForm(null)} />}
          {activeForm === "bill" && <BillForm onSuccess={() => setActiveForm(null)} />}
          {activeForm === "fund" && <FundForm onSuccess={() => setActiveForm(null)} />}
        </DialogContent>
      </Dialog>

      {transcript && <SpeechResultModal onCommandMatched={handleCommandMatched} onClose={() => {}} />}
    </div>
  );
}
