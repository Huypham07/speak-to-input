"use client";

import { useSearchParams } from "next/navigation";
import { useState, useCallback, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Send } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { fetchWithAuth } from "@/lib/fetch-auth";
import { VoiceFormSync } from "@/components/speech/voice-form-sync";

interface TransferFormProps {
  accountId: number;
  currentBalance: number;
  onSuccess?: () => void;
}

export function TransferForm({ accountId, currentBalance, onSuccess }: TransferFormProps) {
  const searchParams = useSearchParams();
  const [recipientAccountNumber, setRecipientAccountNumber] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [amount, setAmount] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Read URL params and auto-fill form
  useEffect(() => {
    try {
      const accountNumber = searchParams.get("accountNumber");
      const recipientNameParam = searchParams.get("recipientName");
      if (accountNumber && accountNumber.trim()) {
        setRecipientAccountNumber(accountNumber.trim());
      }
      if (recipientNameParam && recipientNameParam.trim()) {
        setRecipientName(recipientNameParam.trim());
      }
    } catch (error) {
      // useSearchParams might not be available in some contexts
      console.error("Error reading search params:", error);
    }
  }, [searchParams]);
  
  // Handle voice parameters
  const handleVoiceParameters = useCallback((params: Record<string, any>) => {
    console.log("📝 Filling transfer form with voice params:", params);

    // Map backend 'recipient' to recipient_account_number
    if (params.recipient) {
      setRecipientAccountNumber(params.recipient);
    }
    if (params.recipient_account_number) {
      setRecipientAccountNumber(params.recipient_account_number);
    }
    if (params.recipient_name) {
      setRecipientName(params.recipient_name);
    }
    if (params.amount) {
      setAmount(String(params.amount));
    }
    if (params.description || params.message) {
      setMessage(params.description || params.message);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Trim values to ensure no whitespace issues
    const trimmedAccountNumber = recipientAccountNumber.trim();
    const trimmedAmount = amount.trim();

    if (!trimmedAccountNumber || !trimmedAmount || parseFloat(trimmedAmount) <= 0) {
      toast({
        title: "Lỗi",
        description: "Vui lòng nhập đầy đủ thông tin",
        variant: "destructive",
      });
      return;
    }

    const amountValue = parseFloat(trimmedAmount);
    if (amountValue > currentBalance) {
      toast({
        title: "Lỗi",
        description: "Số dư không đủ",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    try {
      const response = await fetchWithAuth(`/api/transfers`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          from_account_id: accountId,
          recipient_account_number: trimmedAccountNumber,
          recipient_name: recipientName?.trim() || null,
          amount: amountValue,
          message: message?.trim() || null,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        toast({
          title: "Lỗi",
          description: error.error || "Có lỗi xảy ra",
          variant: "destructive",
        });
        return;
      }

      const data = await response.json();

      toast({
        title: "Thành công",
        description: `Chuyển ${amountValue.toLocaleString("vi-VN")} VND thành công`,
      });

      // Reset form
      setRecipientAccountNumber("");
      setRecipientName("");
      setAmount("");
      setMessage("");

      if (onSuccess) {
        onSuccess();
      }
    } catch (error: any) {
      console.error("Transfer catch error:", error);
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
    <>
      {/* Voice Form Sync */}
      <VoiceFormSync
        intentType="create_transfer"
        onParametersReceived={handleVoiceParameters}
        getCurrentFormData={() => ({
          recipient_account_number: recipientAccountNumber,
          recipient_name: recipientName,
          amount,
          message,
        })}
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Send className="h-5 w-5" />
            Chuyển tiền
          </CardTitle>
          <CardDescription>
            Số dư hiện tại: <span className="font-semibold">{currentBalance.toLocaleString("vi-VN")} VND</span>
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Recipient Account Number */}
            <div className="space-y-2">
              <Label htmlFor="recipientAccountNumber">Số tài khoản người nhận *</Label>
              <Input
                id="recipientAccountNumber"
                type="text"
                placeholder="Nhập số tài khoản"
                value={recipientAccountNumber}
                onChange={(e) => setRecipientAccountNumber(e.target.value)}
                required
              />
            </div>

            {/* Recipient Name */}
            <div className="space-y-2">
              <Label htmlFor="recipientName">Tên người nhận (tùy chọn)</Label>
              <Input
                id="recipientName"
                type="text"
                placeholder="Nhập tên người nhận"
                value={recipientName}
                onChange={(e) => setRecipientName(e.target.value)}
              />
            </div>

            {/* Amount */}
            <div className="space-y-2">
              <Label htmlFor="amount">Số tiền *</Label>
              <Input
                id="amount"
                type="number"
                placeholder="0"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                min="10000"
                max={currentBalance}
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
                  disabled={quickAmount > currentBalance}>
                  {(quickAmount / 1000).toLocaleString("vi-VN")}k
                </Button>
              ))}
            </div>

            {/* Message */}
            <div className="space-y-2">
              <Label htmlFor="message">Nội dung chuyển khoản (tùy chọn)</Label>
              <Textarea
                id="message"
                placeholder="Nhập nội dung..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={3}
                maxLength={200}
              />
            </div>

            {/* Submit Button */}
            <Button type="submit" className="w-full" disabled={loading}>
              <Send className="h-4 w-4 mr-2" />
              {loading ? "Đang xử lý..." : "Chuyển tiền"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </>
  );
}
