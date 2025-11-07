"use client";

import { useFinancial } from "@/lib/financial-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Plus, CreditCard } from "lucide-react";
import { toast } from "sonner";
import { useState } from "react";

interface BillsListProps {
  onCreateBill?: () => void;
}

export function BillsList({ onCreateBill }: BillsListProps) {
  const { bills, payBill } = useFinancial();
  const [payingBillId, setPayingBillId] = useState<number | null>(null);

  const handlePayBill = async (billId: number, billName: string) => {
    if (payingBillId) return; // Prevent multiple simultaneous payments

    try {
      setPayingBillId(billId);
      await payBill(billId);
      toast.success(`Đã thanh toán hóa đơn "${billName}"`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Thanh toán thất bại");
    } finally {
      setPayingBillId(null);
    }
  };

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

  const getCategoryText = (category: string) => {
    switch (category.toLowerCase()) {
      case "utilities":
        return "Tiện ích";
      case "rent":
        return "Tiền thuê";
      case "insurance":
        return "Bảo hiểm";
      case "subscription":
        return "Đăng ký";
      case "internet":
        return "Internet";
      case "phone":
        return "Điện thoại";
      case "electricity":
        return "Điện";
      case "water":
        return "Nước";
      case "gas":
        return "Gas";
      case "healthcare":
        return "Y tế";
      case "education":
        return "Giáo dục";
      case "entertainment":
        return "Giải trí";
      case "other":
        return "Khác";
      default:
        return category;
    }
  };

  if (bills.length === 0) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Hóa đơn chi tiêu</CardTitle>
            <CardDescription>Theo dõi hóa đơn và chi phí</CardDescription>
          </div>
          {onCreateBill && (
            <Button onClick={onCreateBill} size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Tạo hóa đơn
            </Button>
          )}
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <div className="w-16 h-16 rounded-full bg-muted mx-auto mb-4 flex items-center justify-center">
              <FileText className="h-8 w-8 text-muted-foreground" />
            </div>
            <h3 className="font-semibold text-lg mb-2">Chưa có hóa đơn nào</h3>
            <p className="text-muted-foreground mb-6">Bắt đầu tạo hóa đơn để theo dõi chi phí của bạn</p>
            {onCreateBill && (
              <Button onClick={onCreateBill} variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Tạo hóa đơn đầu tiên
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Hóa đơn chi tiêu</CardTitle>
          <CardDescription>Theo dõi hóa đơn và chi phí</CardDescription>
        </div>
        {onCreateBill && (
          <Button onClick={onCreateBill} size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Tạo hóa đơn
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {bills.map((bill) => (
            <div
              key={bill.id}
              className="flex flex-col sm:flex-row sm:items-center gap-3 p-4 border border-border rounded-lg hover:shadow-md transition-shadow">
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="w-10 h-10 rounded-full bg-orange-100 dark:bg-orange-900 flex items-center justify-center shrink-0">
                  <FileText className="h-5 w-5 text-orange-600" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="font-medium truncate">{bill.bill_name}</p>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <p className="text-xs text-muted-foreground">{getCategoryText(bill.category)}</p>
                    <span className="text-xs text-muted-foreground">•</span>
                    <p className="text-xs text-muted-foreground">
                      Hạn: {new Date(bill.dueDate).toLocaleDateString("vi-VN")}
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0">
                <div className="text-left sm:text-right">
                  <p className="font-semibold text-base sm:text-sm">{bill.amount.toLocaleString("vi-VN")} đ</p>
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
                {bill.status === "pending" && (
                  <Button
                    size="sm"
                    onClick={() => handlePayBill(bill.id, bill.bill_name)}
                    disabled={payingBillId === bill.id}
                    className="shrink-0 whitespace-nowrap">
                    <CreditCard className="h-4 w-4 sm:mr-1" />
                    {payingBillId === bill.id ? "Đang xử lý..." : "Thanh toán"}
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
