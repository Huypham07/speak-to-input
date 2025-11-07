"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Send, FileText, PiggyBank } from "lucide-react"

interface QuickActionsProps {
  onTransfer: () => void
  onBill: () => void
  onFund: () => void
}

export function QuickActions({ onTransfer, onBill, onFund }: QuickActionsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
        <CardDescription>Access your most used features</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Button onClick={onTransfer} variant="outline" className="h-auto flex-col gap-2 py-4 bg-transparent">
            <Send className="h-5 w-5 text-blue-600" />
            <span className="text-sm">Send Money</span>
          </Button>
          <Button onClick={onBill} variant="outline" className="h-auto flex-col gap-2 py-4 bg-transparent">
            <FileText className="h-5 w-5 text-orange-600" />
            <span className="text-sm">Create Bill</span>
          </Button>
          <Button onClick={onFund} variant="outline" className="h-auto flex-col gap-2 py-4 bg-transparent">
            <PiggyBank className="h-5 w-5 text-emerald-600" />
            <span className="text-sm">Save Fund</span>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
