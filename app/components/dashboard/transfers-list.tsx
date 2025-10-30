"use client";

import { useFinancial } from "@/lib/financial-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Send } from "lucide-react";

export function TransfersList() {
  const { transfers } = useFinancial();

  if (transfers.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Giao dịch gần đây</CardTitle>
          <CardDescription>Lịch sử chuyển tiền</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <Send className="h-12 w-12 text-muted-foreground mx-auto mb-2 opacity-50" />
            <p className="text-muted-foreground">Chưa có giao dịch nào</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Giao dịch gần đây</CardTitle>
        <CardDescription>Lịch sử chuyển tiền</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {transfers.slice(0, 5).map((transfer) => (
            <div
              key={transfer.id}
              className="flex items-center justify-between p-3 border border-border rounded-lg hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center shrink-0">
                  <Send className="h-5 w-5 text-blue-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{transfer.recipientName}</p>
                  <p className="text-xs text-muted-foreground truncate">{transfer.recipientAccount}</p>
                </div>
              </div>
              <div className="text-right shrink-0 ml-2">
                <p className="font-semibold">{transfer.amount.toLocaleString("vi-VN")} đ</p>
                <Badge variant="outline" className="text-xs mt-1">
                  {transfer.status === "completed"
                    ? "Hoàn thành"
                    : transfer.status === "pending"
                    ? "Đang xử lý"
                    : "Thất bại"}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
