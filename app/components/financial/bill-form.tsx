"use client"

import type React from "react"
import { useState } from "react"
import { useFinancial } from "@/lib/financial-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"

const BILL_CATEGORIES = ["Utilities", "Rent", "Insurance", "Subscription", "Healthcare", "Education", "Other"]

export function BillForm({ onSuccess }: { onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    title: "",
    category: "Utilities",
    amount: "",
    dueDate: "",
    description: "",
    tags: "",
  })
  const [isLoading, setIsLoading] = useState(false)
  const { addBill } = useFinancial()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 800))
      addBill({
        title: formData.title,
        category: formData.category,
        amount: Number.parseFloat(formData.amount),
        dueDate: new Date(formData.dueDate),
        description: formData.description,
        status: "pending",
        tags: formData.tags.split(",").map((t) => t.trim()),
      })
      setFormData({ title: "", category: "Utilities", amount: "", dueDate: "", description: "", tags: "" })
      onSuccess()
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Expense Bill</CardTitle>
        <CardDescription>Track and manage your recurring expenses</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Bill Title</label>
              <Input
                placeholder="Monthly Internet Bill"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Category</label>
              <select
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              >
                {BILL_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Amount (USD)</label>
              <Input
                type="number"
                placeholder="0.00"
                step="0.01"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Due Date</label>
              <Input
                type="date"
                value={formData.dueDate}
                onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
                required
              />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Description</label>
            <Textarea
              placeholder="Bill details..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Tags (comma-separated)</label>
            <Input
              placeholder="important, recurring, monthly"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
            />
          </div>
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Creating..." : "Create Bill"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
