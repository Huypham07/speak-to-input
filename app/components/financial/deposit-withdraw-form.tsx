"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Wallet, Plus, Minus } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface DepositWithdrawFormProps {
  accountId: number;
  currentBalance: number;
  onSuccess?: () => void;
}

export function DepositWithdrawForm({ accountId, currentBalance, onSuccess }: DepositWithdrawFormProps) {
  const [mode, setMode] = useState<"deposit" | "withdraw">("deposit");
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
      });
      return;
    }

    if (mode === "withdraw" && parseFloat(amount) > currentBalance) {
      toast({
        title: "Lỗi",
        description: "Số dư không đủ",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    try {
      const token = localStorage.getItem("access_token");
      const endpoint = mode === "deposit" ? "deposit" : "withdraw";

      const response = await fetch(`http://localhost:8000/api/v1/accounts/${accountId}/${endpoint}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          amount: parseFloat(amount),
          note: note || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Có lỗi xảy ra");
      }

      const data = await response.json();

      toast({
        title: "Thành công",
        description: `${mode === "deposit" ? "Nạp" : "Rút"} ${parseFloat(amount).toLocaleString(
          "vi-VN"
        )} VND thành công. Số dư mới: ${data.balance_after.toLocaleString("vi-VN")} VND`,
      });

      // Reset form
      setAmount("");
      setNote("");

      if (onSuccess) {
        onSuccess();
      }
    } catch (error: any) {
      toast({
        title: "Lỗi",
        description: error.message || "Có lỗi xảy ra",
        variant: "destructive",
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
          Nạp/Rút tiền
        </CardTitle>
        <CardDescription>
          Số dư hiện tại: <span className="font-semibold">{currentBalance.toLocaleString("vi-VN")} VND</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Mode Selection */}
          <div className="flex gap-2">
            <Button
              type="button"
              variant={mode === "deposit" ? "default" : "outline"}
              className="flex-1"
              onClick={() => setMode("deposit")}>
              <Plus className="h-4 w-4 mr-2" />
              Nạp tiền
            </Button>
            <Button
              type="button"
              variant={mode === "withdraw" ? "default" : "outline"}
              className="flex-1"
              onClick={() => setMode("withdraw")}>
              <Minus className="h-4 w-4 mr-2" />
              Rút tiền
            </Button>
          </div>

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
                onClick={() => setAmount(quickAmount.toString())}
                disabled={mode === "withdraw" && quickAmount > currentBalance}>
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
            {loading ? "Đang xử lý..." : mode === "deposit" ? "Nạp tiền" : "Rút tiền"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
