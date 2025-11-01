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
import { Button } from "@/components/ui/button";
import { Settings, User, LogOut } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type ActiveForm = "transfer" | "bill" | "fund" | null;

interface Account {
  id: number;
  account_number: string;
  account_name: string;
  balance: number;
  currency: string;
  account_type: string;
  is_active: boolean;
}

export default function DashboardPage() {
  const { user, isLoading, logout } = useAuth();
  const { isCollapsed } = useSidebar();
  const router = useRouter();
  const [activeForm, setActiveForm] = useState<ActiveForm>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const { transcript } = useSpeech();
  const { addTransfer, addBill, addFund } = useFinancial();

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  // Fetch accounts for transfer form
  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const response = await fetch("/api/accounts");
        if (response.ok) {
          const data = await response.json();
          setAccounts(data);
        }
      } catch (error) {
        console.error("Error fetching accounts:", error);
      }
    };

    if (user) {
      fetchAccounts();
    }
  }, [user]);

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
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Xin chào,</p>
              <h1 className="text-xl md:text-2xl font-semibold text-foreground">{user.full_name}</h1>
            </div>

            {/* Settings dropdown for mobile */}
            <div className="md:hidden">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Settings className="h-6 w-6" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>Cài đặt</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="py-3">
                    <User className="mr-2 h-5 w-5" />
                    <span className="text-base">Tài khoản</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem className="py-3">
                    <Settings className="mr-2 h-5 w-5" />
                    <span className="text-base">Khác</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={logout} className="text-red-600 dark:text-red-400 py-3">
                    <LogOut className="mr-2 h-5 w-5" />
                    <span className="text-base">Đăng xuất</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
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
          {activeForm === "transfer" && accounts.length > 0 && (
            <TransferForm
              accountId={accounts[0].id}
              currentBalance={accounts[0].balance}
              onSuccess={() => setActiveForm(null)}
            />
          )}
          {activeForm === "bill" && <BillForm onSuccess={() => setActiveForm(null)} />}
          {activeForm === "fund" && <FundForm onSuccess={() => setActiveForm(null)} />}
        </DialogContent>
      </Dialog>

      {transcript && <SpeechResultModal onCommandMatched={handleCommandMatched} onClose={() => {}} />}
    </div>
  );
}
