"use client"

import type React from "react"
import { useState } from "react"
import { useFinancial } from "@/lib/financial-context"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"

export function TransferForm({ onSuccess }: { onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    recipientName: "",
    recipientAccount: "",
    amount: "",
    description: "",
  })
  const [isLoading, setIsLoading] = useState(false)
  const { addTransfer } = useFinancial()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 800))
      addTransfer({
        recipientName: formData.recipientName,
        recipientAccount: formData.recipientAccount,
        amount: Number.parseFloat(formData.amount),
        description: formData.description,
      })
      setFormData({ recipientName: "", recipientAccount: "", amount: "", description: "" })
      onSuccess()
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Send Money</CardTitle>
        <CardDescription>Transfer funds to another account</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Recipient Name</label>
              <Input
                placeholder="John Doe"
                value={formData.recipientName}
                onChange={(e) => setFormData({ ...formData, recipientName: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Account Number</label>
              <Input
                placeholder="1234567890"
                value={formData.recipientAccount}
                onChange={(e) => setFormData({ ...formData, recipientAccount: e.target.value })}
                required
              />
            </div>
          </div>
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
            <label className="text-sm font-medium">Description</label>
            <Textarea
              placeholder="Payment for..."
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
            />
          </div>
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? "Processing..." : "Send Transfer"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
