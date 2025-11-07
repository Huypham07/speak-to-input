"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Wallet, Plus } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { fetchWithAuth } from "@/lib/fetch-auth";

interface DepositWithdrawFormProps {
  accountId: number;
  currentBalance: number;
  onSuccess?: () => void;
}

export function DepositWithdrawForm({ accountId, currentBalance, onSuccess }: DepositWithdrawFormProps) {
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!amount || parseFloat(amount) <= 0) {
      toast({
        title: "Lỗi",
        description: "Vui lòng nhập số tiền hợp lệ",
        variant: "destructive",
        duration: 4000,
      });
      return;
    }

    setLoading(true);

    try {
      const response = await fetchWithAuth(`/api/accounts/deposit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          account_id: accountId,
          amount: parseFloat(amount),
          note: note || null,
        }),
      });

      console.log("Deposit response status:", response.status);

      if (!response.ok) {
        const error = await response.json();
        console.error("Deposit error:", error);
        throw new Error(error.error || "Có lỗi xảy ra");
      }

      const data = await response.json();
      console.log("Deposit success data:", data);

      toast({
        title: "Thành công",
        description: `Nạp ${parseFloat(amount).toLocaleString("vi-VN")} VND thành công`,
        duration: 4000,
      });

      // Reset form
      setAmount("");
      setNote("");

      if (onSuccess) {
        console.log("Calling onSuccess callback");
        onSuccess();
      }
    } catch (error: any) {
      console.error("Deposit catch error:", error);
      toast({
        title: "Lỗi",
        description: error.message || "Có lỗi xảy ra",
        variant: "destructive",
        duration: 4000,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Wallet className="h-5 w-5" />
          Nạp tiền
        </CardTitle>
        <CardDescription>
          Số dư hiện tại: <span className="font-semibold">{currentBalance.toLocaleString("vi-VN")} VND</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Amount */}
          <div className="space-y-2">
            <Label htmlFor="amount">Số tiền</Label>
            <Input
              id="amount"
              type="number"
              placeholder="0"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              min="0"
              step="1000"
              required
            />
          </div>

          {/* Quick Amounts */}
          <div className="flex gap-2 flex-wrap">
            {[100000, 200000, 500000, 1000000, 2000000, 5000000].map((quickAmount) => (
              <Button
                key={quickAmount}
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setAmount(quickAmount.toString())}>
                {(quickAmount / 1000).toLocaleString("vi-VN")}k
              </Button>
            ))}
          </div>

          {/* Note */}
          <div className="space-y-2">
            <Label htmlFor="note">Ghi chú (tùy chọn)</Label>
            <Textarea
              id="note"
              placeholder="Nhập ghi chú..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
              rows={3}
            />
          </div>

          {/* Submit Button */}
          <Button type="submit" className="w-full" disabled={loading}>
            <Plus className="h-4 w-4 mr-2" />
            {loading ? "Đang xử lý..." : "Nạp tiền"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
