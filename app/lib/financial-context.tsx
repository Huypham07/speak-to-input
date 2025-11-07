"use client";

import type React from "react";
import { createContext, useContext, useState, useCallback, useEffect } from "react";
import { useAuth } from "@/lib/auth-context";
import { fetchWithAuth } from "@/lib/fetch-auth";

export interface Transfer {
  id: number;
  fromAccountId: number; // Add this to identify user's outgoing transfers
  recipientName: string;
  recipientAccount: string;
  amount: number;
  description: string;
  date: Date;
  status: "pending" | "completed" | "failed";
}

export interface ExpenseBill {
  id: number;
  bill_name: string;
  category: string;
  amount: number;
  dueDate: Date;
  notes: string;
  status: "pending" | "paid" | "overdue";
  tags: string[];
}

export interface SavingsFund {
  id: number;
  fund_name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  category: string | null;
  monthly_contribution: number;
  progress_percentage: number;
  status: string;
  created_at: string;
}

interface FinancialContextType {
  transfers: Transfer[];
  bills: ExpenseBill[];
  funds: SavingsFund[];
  isLoadingFunds: boolean;
  addTransfer: (transfer: Omit<Transfer, "id" | "date" | "status">) => void;
  addBill: (bill: Omit<ExpenseBill, "id">) => Promise<void>;
  payBill: (billId: number, fromAccountId?: number) => Promise<void>;
  addFund: (fundData: {
    fund_name: string;
    target_amount: number;
    target_date: string;
    initial_amount?: number;
    monthly_contribution?: number;
    category?: string;
    auto_transfer?: boolean;
    notes?: string;
  }) => Promise<void>;
  updateBill: (id: number, bill: Partial<ExpenseBill>) => void;
  updateFund: (id: number, fund: Partial<SavingsFund>) => Promise<void>;
  refreshFunds: () => Promise<void>;
  refreshBills: () => Promise<void>;
  refreshTransfers: () => Promise<void>;
  depositToFund: (fundId: number, amount: number, fromAccountId?: number) => Promise<void>;
  withdrawFromFund: (fundId: number, amount: number, toAccountId?: number) => Promise<void>;
  deleteFund: (fundId: number) => Promise<void>;
}

const FinancialContext = createContext<FinancialContextType | undefined>(undefined);

export function FinancialProvider({ children }: { children: React.ReactNode }) {
  const { user, isLoading: isAuthLoading } = useAuth();
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [bills, setBills] = useState<ExpenseBill[]>([]);
  const [funds, setFunds] = useState<SavingsFund[]>([]);
  const [isLoadingFunds, setIsLoadingFunds] = useState(false);

  // Fetch transfers from API
  const fetchTransfers = useCallback(async () => {
    if (!user) {
      setTransfers([]);
      return;
    }

    try {
      const response = await fetchWithAuth("/api/transfers");
      if (response.ok) {
        const data = await response.json();
        // Transform API response to match Transfer interface
        const transformedTransfers: Transfer[] = data.map((transfer: any) => ({
          id: transfer.id,
          fromAccountId: transfer.from_account_id,
          recipientName: transfer.to_account_number, // API uses to_account_number
          recipientAccount: transfer.to_account_number,
          amount: transfer.amount,
          description: transfer.message || "",
          date: new Date(transfer.created_at),
          status: transfer.status,
        }));
        setTransfers(transformedTransfers);
      } else if (response.status === 401) {
        console.warn("⚠️ Unauthorized - clearing transfers");
        setTransfers([]);
      }
    } catch (error) {
      console.error("❌ Error fetching transfers:", error);
      setTransfers([]);
    }
  }, [user]);

  // Fetch bills from API
  const fetchBills = useCallback(async () => {
    // Don't fetch if user is not authenticated
    if (!user) {
      setBills([]);
      return;
    }

    try {
      const response = await fetchWithAuth("/api/bills");
      if (response.ok) {
        const data = await response.json();
        // Transform API response to match ExpenseBill interface
        const transformedBills: ExpenseBill[] = data.map((bill: any) => ({
          id: bill.id,
          bill_name: bill.bill_name,
          category: bill.category || "other",
          amount: bill.amount,
          dueDate: new Date(bill.due_date),
          notes: bill.notes || "",
          status: bill.status,
          tags: [],
        }));
        setBills(transformedBills);
      } else if (response.status === 401) {
        // Unauthorized - clear bills
        setBills([]);
      }
    } catch (error) {
      console.error("Error fetching bills:", error);
      setBills([]);
    }
  }, [user]);

  // Fetch funds from API
  const fetchFunds = useCallback(async () => {
    // Don't fetch if user is not authenticated
    if (!user) {
      setFunds([]);
      return;
    }

    setIsLoadingFunds(true);
    try {
      const response = await fetchWithAuth("/api/funds");
      if (response.ok) {
        const data = await response.json();
        setFunds(data);
      } else if (response.status === 401) {
        // Unauthorized - clear funds
        setFunds([]);
      }
    } catch (error) {
      console.error("Error fetching funds:", error);
      setFunds([]);
    } finally {
      setIsLoadingFunds(false);
    }
  }, [user]);

  // Fetch funds when user is authenticated
  useEffect(() => {
    // Only fetch if auth check is complete and user is logged in
    if (!isAuthLoading && user) {
      fetchTransfers();
      fetchFunds();
      fetchBills();
    } else if (!isAuthLoading && !user) {
      // Clear data when user logs out
      setTransfers([]);
      setFunds([]);
      setBills([]);
    }
  }, [user, isAuthLoading, fetchTransfers, fetchFunds, fetchBills]);

  const addTransfer = useCallback((transfer: Omit<Transfer, "id" | "date" | "status">) => {
    const newTransfer: Transfer = {
      ...transfer,
      id: Date.now(),
      date: new Date(),
      status: "completed",
    };
    setTransfers((prev) => [newTransfer, ...prev]);
  }, []);

  const addBill = useCallback(
    async (bill: Omit<ExpenseBill, "id">) => {
      try {
        const response = await fetchWithAuth("/api/bills", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            bill_name: bill.bill_name,
            amount: bill.amount,
            due_date: bill.dueDate.toISOString().split("T")[0], // Convert Date to YYYY-MM-DD
            category: bill.category,
            notes: bill.notes || undefined,
            recurring: false, // Default to false, can be extended later
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || error.detail || "Failed to create bill");
        }

        // Refresh bills list to get latest data
        await fetchBills();
      } catch (error) {
        console.error("Error creating bill:", error);
        throw error;
      }
    },
    [fetchBills]
  );

  const payBill = useCallback(
    async (billId: number, fromAccountId?: number) => {
      try {
        const url = `/api/bills/${billId}/pay${fromAccountId ? `?from_account_id=${fromAccountId}` : ""}`;
        const response = await fetchWithAuth(url, {
          method: "POST",
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || error.detail || "Failed to pay bill");
        }

        // Refresh bills list to get latest data
        await fetchBills();
      } catch (error) {
        console.error("Error paying bill:", error);
        throw error;
      }
    },
    [fetchBills]
  );

  const addFund = useCallback(
    async (fundData: {
      fund_name: string;
      target_amount: number;
      target_date: string;
      initial_amount?: number;
      monthly_contribution?: number;
      category?: string;
      auto_transfer?: boolean;
      notes?: string;
    }) => {
      try {
        const response = await fetchWithAuth("/api/funds", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(fundData),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || error.detail || "Failed to create fund");
        }

        // Refresh funds list to get latest data
        await fetchFunds();
      } catch (error) {
        console.error("Error creating fund:", error);
        throw error;
      }
    },
    [fetchFunds]
  );

  const updateBill = useCallback((id: number, updates: Partial<ExpenseBill>) => {
    setBills((prev) => prev.map((bill) => (bill.id === id ? { ...bill, ...updates } : bill)));
  }, []);

  const updateFund = useCallback(
    async (id: number, updates: Partial<SavingsFund>) => {
      // For now, just refresh from server after update
      await fetchFunds();
    },
    [fetchFunds]
  );

  const depositToFund = useCallback(
    async (fundId: number, amount: number, fromAccountId?: number) => {
      try {
        const response = await fetchWithAuth(`/api/funds/${fundId}/deposit`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            amount,
            from_account_id: fromAccountId,
          }),
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
          throw new Error(result.message || result.detail || "Failed to deposit");
        }

        // Refresh funds after deposit
        await fetchFunds();
        return result;
      } catch (error) {
        console.error("Error depositing to fund:", error);
        throw error;
      }
    },
    [fetchFunds]
  );

  const withdrawFromFund = useCallback(
    async (fundId: number, amount: number, toAccountId?: number) => {
      try {
        const response = await fetchWithAuth(`/api/funds/${fundId}/withdraw`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            amount,
            to_account_id: toAccountId,
          }),
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
          throw new Error(result.message || result.detail || "Failed to withdraw");
        }

        // Refresh funds after withdrawal
        await fetchFunds();
        return result;
      } catch (error) {
        console.error("Error withdrawing from fund:", error);
        throw error;
      }
    },
    [fetchFunds]
  );

  const deleteFund = useCallback(async (fundId: number) => {
    try {
      const response = await fetchWithAuth(`/api/funds/${fundId}`, {
        method: "DELETE",
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.message || result.detail || "Failed to delete fund");
      }

      // Remove from state
      setFunds((prev) => prev.filter((fund) => fund.id !== fundId));
      return result;
    } catch (error) {
      console.error("Error deleting fund:", error);
      throw error;
    }
  }, []);

  return (
    <FinancialContext.Provider
      value={{
        transfers,
        bills,
        funds,
        isLoadingFunds,
        addTransfer,
        addBill,
        payBill,
        addFund,
        updateBill,
        updateFund,
        refreshFunds: fetchFunds,
        refreshBills: fetchBills,
        refreshTransfers: fetchTransfers,
        depositToFund,
        withdrawFromFund,
        deleteFund,
      }}>
      {children}
    </FinancialContext.Provider>
  );
}

export function useFinancial() {
  const context = useContext(FinancialContext);
  if (context === undefined) {
    throw new Error("useFinancial must be used within FinancialProvider");
  }
  return context;
}
