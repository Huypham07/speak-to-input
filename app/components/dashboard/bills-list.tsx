"use client";

import { useFinancial } from "@/lib/financial-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";

export function BillsList() {
  const { bills } = useFinancial();

  const getStatusText = (status: string) => {
    switch (status) {
      case "paid":
        return "Đã thanh toán";
      case "overdue":
        return "Quá hạn";
      case "pending":
        return "Chờ thanh toán";
      default:
        return status;
    }
  };

  if (bills.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Hóa đơn chi tiêu</CardTitle>
          <CardDescription>Theo dõi hóa đơn và chi phí</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-2 opacity-50" />
            <p className="text-muted-foreground">Chưa có hóa đơn nào</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Hóa đơn chi tiêu</CardTitle>
        <CardDescription>Theo dõi hóa đơn và chi phí</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {bills.slice(0, 5).map((bill) => (
            <div
              key={bill.id}
              className="flex items-center justify-between p-3 border border-border rounded-lg hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="w-10 h-10 rounded-full bg-orange-100 dark:bg-orange-900 flex items-center justify-center shrink-0">
                  <FileText className="h-5 w-5 text-orange-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{bill.title}</p>
                  <p className="text-xs text-muted-foreground">{bill.category}</p>
                </div>
              </div>
              <div className="text-right shrink-0 ml-2">
                <p className="font-semibold">{bill.amount.toLocaleString("vi-VN")} đ</p>
                <Badge
                  variant="outline"
                  className={`text-xs mt-1 ${
                    bill.status === "paid"
                      ? "bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-400"
                      : bill.status === "overdue"
                      ? "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-400"
                      : "bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-400"
                  }`}>
                  {getStatusText(bill.status)}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
