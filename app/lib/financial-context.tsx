"use client"

import type React from "react"
import { createContext, useContext, useState, useCallback, useEffect } from "react"

export interface Transfer {
  id: string
  recipientName: string
  recipientAccount: string
  amount: number
  description: string
  date: Date
  status: "pending" | "completed" | "failed"
}

export interface ExpenseBill {
  id: string
  title: string
  category: string
  amount: number
  dueDate: Date
  description: string
  status: "pending" | "paid" | "overdue"
  tags: string[]
}

export interface SavingsFund {
  id: number
  fund_name: string
  target_amount: number
  current_amount: number
  target_date: string
  category: string | null
  monthly_contribution: number
  progress_percentage: number
  status: string
  created_at: string
}

interface FinancialContextType {
  transfers: Transfer[]
  bills: ExpenseBill[]
  funds: SavingsFund[]
  isLoadingFunds: boolean
  addTransfer: (transfer: Omit<Transfer, "id" | "date" | "status">) => void
  addBill: (bill: Omit<ExpenseBill, "id">) => void
  addFund: (fundData: {
    fund_name: string
    target_amount: number
    target_date: string
    initial_amount?: number
    monthly_contribution?: number
    category?: string
    auto_transfer?: boolean
    notes?: string
  }) => Promise<void>
  updateBill: (id: string, bill: Partial<ExpenseBill>) => void
  updateFund: (id: number, fund: Partial<SavingsFund>) => Promise<void>
  refreshFunds: () => Promise<void>
  depositToFund: (fundId: number, amount: number, fromAccountId?: number) => Promise<void>
  withdrawFromFund: (fundId: number, amount: number, toAccountId?: number) => Promise<void>
  deleteFund: (fundId: number) => Promise<void>
}

const FinancialContext = createContext<FinancialContextType | undefined>(undefined)

export function FinancialProvider({ children }: { children: React.ReactNode }) {
  const [transfers, setTransfers] = useState<Transfer[]>([])
  const [bills, setBills] = useState<ExpenseBill[]>([])
  const [funds, setFunds] = useState<SavingsFund[]>([])
  const [isLoadingFunds, setIsLoadingFunds] = useState(false)

  // Fetch funds from API
  const fetchFunds = useCallback(async () => {
    setIsLoadingFunds(true)
    try {
      const response = await fetch("/api/funds")
      if (response.ok) {
        const data = await response.json()
        setFunds(data)
      }
    } catch (error) {
      console.error("Error fetching funds:", error)
    } finally {
      setIsLoadingFunds(false)
    }
  }, [])

  // Fetch funds on mount
  useEffect(() => {
    fetchFunds()
  }, [fetchFunds])

  const addTransfer = useCallback((transfer: Omit<Transfer, "id" | "date" | "status">) => {
    const newTransfer: Transfer = {
      ...transfer,
      id: Date.now().toString(),
      date: new Date(),
      status: "completed",
    }
    setTransfers((prev) => [newTransfer, ...prev])
  }, [])

  const addBill = useCallback((bill: Omit<ExpenseBill, "id">) => {
    const newBill: ExpenseBill = {
      ...bill,
      id: Date.now().toString(),
    }
    setBills((prev) => [newBill, ...prev])
  }, [])

  const addFund = useCallback(async (fundData: {
    fund_name: string
    target_amount: number
    target_date: string
    initial_amount?: number
    monthly_contribution?: number
    category?: string
    auto_transfer?: boolean
    notes?: string
  }) => {
    try {
      const response = await fetch("/api/funds", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(fundData),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || error.detail || "Failed to create fund")
      }

      // Refresh funds list to get latest data
      await fetchFunds()
    } catch (error) {
      console.error("Error creating fund:", error)
      throw error
    }
  }, [fetchFunds])

  const updateBill = useCallback((id: string, updates: Partial<ExpenseBill>) => {
    setBills((prev) => prev.map((bill) => (bill.id === id ? { ...bill, ...updates } : bill)))
  }, [])

  const updateFund = useCallback(async (id: number, updates: Partial<SavingsFund>) => {
    // For now, just refresh from server after update
    await fetchFunds()
  }, [fetchFunds])

  const depositToFund = useCallback(async (fundId: number, amount: number, fromAccountId?: number) => {
    try {
      const response = await fetch(`/api/funds/${fundId}/deposit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          amount,
          from_account_id: fromAccountId,
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || error.detail || "Failed to deposit")
      }

      // Refresh funds after deposit
      await fetchFunds()
    } catch (error) {
      console.error("Error depositing to fund:", error)
      throw error
    }
  }, [fetchFunds])

  const withdrawFromFund = useCallback(async (fundId: number, amount: number, toAccountId?: number) => {
    try {
      const response = await fetch(`/api/funds/${fundId}/withdraw`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          amount,
          to_account_id: toAccountId,
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || error.detail || "Failed to withdraw")
      }

      // Refresh funds after withdrawal
      await fetchFunds()
    } catch (error) {
      console.error("Error withdrawing from fund:", error)
      throw error
    }
  }, [fetchFunds])

  const deleteFund = useCallback(async (fundId: number) => {
    try {
      const response = await fetch(`/api/funds/${fundId}`, {
        method: "DELETE",
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || error.detail || "Failed to delete fund")
      }

      // Remove from state
      setFunds((prev) => prev.filter((fund) => fund.id !== fundId))
    } catch (error) {
      console.error("Error deleting fund:", error)
      throw error
    }
  }, [])

  return (
    <FinancialContext.Provider
      value={{
        transfers,
        bills,
        funds,
        isLoadingFunds,
        addTransfer,
        addBill,
        addFund,
        updateBill,
        updateFund,
        refreshFunds: fetchFunds,
        depositToFund,
        withdrawFromFund,
        deleteFund,
      }}
    >
      {children}
    </FinancialContext.Provider>
  )
}

export function useFinancial() {
  const context = useContext(FinancialContext)
  if (context === undefined) {
    throw new Error("useFinancial must be used within FinancialProvider")
  }
  return context
}
