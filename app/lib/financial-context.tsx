"use client"

import type React from "react"
import { createContext, useContext, useState, useCallback } from "react"

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
  id: string
  name: string
  targetAmount: number
  currentAmount: number
  description: string
  deadline: Date
  category: string
  priority: "low" | "medium" | "high"
}

interface FinancialContextType {
  transfers: Transfer[]
  bills: ExpenseBill[]
  funds: SavingsFund[]
  addTransfer: (transfer: Omit<Transfer, "id" | "date" | "status">) => void
  addBill: (bill: Omit<ExpenseBill, "id">) => void
  addFund: (fund: Omit<SavingsFund, "id">) => void
  updateBill: (id: string, bill: Partial<ExpenseBill>) => void
  updateFund: (id: string, fund: Partial<SavingsFund>) => void
}

const FinancialContext = createContext<FinancialContextType | undefined>(undefined)

export function FinancialProvider({ children }: { children: React.ReactNode }) {
  const [transfers, setTransfers] = useState<Transfer[]>([])
  const [bills, setBills] = useState<ExpenseBill[]>([])
  const [funds, setFunds] = useState<SavingsFund[]>([])

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

  const addFund = useCallback((fund: Omit<SavingsFund, "id">) => {
    const newFund: SavingsFund = {
      ...fund,
      id: Date.now().toString(),
    }
    setFunds((prev) => [newFund, ...prev])
  }, [])

  const updateBill = useCallback((id: string, updates: Partial<ExpenseBill>) => {
    setBills((prev) => prev.map((bill) => (bill.id === id ? { ...bill, ...updates } : bill)))
  }, [])

  const updateFund = useCallback((id: string, updates: Partial<SavingsFund>) => {
    setFunds((prev) => prev.map((fund) => (fund.id === id ? { ...fund, ...updates } : fund)))
  }, [])

  return (
    <FinancialContext.Provider
      value={{ transfers, bills, funds, addTransfer, addBill, addFund, updateBill, updateFund }}
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
