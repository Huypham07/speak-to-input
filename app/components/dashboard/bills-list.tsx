"use client";

import { useFinancial } from "@/lib/financial-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { FileText, Plus, CreditCard } from "lucide-react";
import { toast } from "sonner";
import { useState, useEffect } from "react";
import { useSpeech } from "@/lib/speech-context";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface BillsListProps {
  onCreateBill?: () => void;
}

export function BillsList({ onCreateBill }: BillsListProps) {
  const { bills, payBill, refreshBills } = useFinancial();
  const { extractedIntent, clearIntent } = useSpeech();
  const [payingBillId, setPayingBillId] = useState<number | null>(null);
  const [payConfirmDialog, setPayConfirmDialog] = useState<{
    open: boolean;
    billId: number | null;
    billName: string;
    amount: number;
  }>({
    open: false,
    billId: null,
    billName: "",
    amount: 0,
  });

  // Disambiguation dialog for multiple matching bills
  const [disambiguationDialog, setDisambiguationDialog] = useState<{
    open: boolean;
    bills: typeof bills;
  }>({
    open: false,
    bills: [],
  });

  // Handle voice intent for pay_bill
  useEffect(() => {
    if (!extractedIntent || extractedIntent.intent_changed || !bills || bills.length === 0) return;

    const { intent_type, parameters } = extractedIntent;

    if (intent_type === "pay_bill") {
      // Find all matching bills by ID or name
      let matchingBills: typeof bills = [];

      if (parameters.bill_id) {
        const bill = bills.find((b) => b.id === parseInt(parameters.bill_id));
        matchingBills = bill ? [bill] : [];
      } else if (parameters.bill_name) {
        const name = parameters.bill_name.toLowerCase();
        matchingBills = bills.filter((b) => b.bill_name.toLowerCase() === name);
      }

      // Check for duplicate names
      if (matchingBills.length > 1) {
        // Show disambiguation dialog to let user choose
        // Use setTimeout to ensure overlay is closed and navigation is complete
        setTimeout(() => {
          setDisambiguationDialog({
            open: true,
            bills: matchingBills,
          });
        }, 100); // Small delay to ensure UI is ready

        clearIntent();
        return;
      }

      const bill = matchingBills[0];
      if (!bill) {
        if (parameters.bill_name) {
          toast.error(`Không tìm thấy hóa đơn với tên "${parameters.bill_name}"`, {
            duration: 4000,
          });
        }
        clearIntent();
        return;
      }

      if (bill.status !== "paid") {
        // Auto-open pay confirmation dialog
        setPayConfirmDialog({
          open: true,
          billId: bill.id,
          billName: bill.bill_name,
          amount: bill.amount,
        });

        // Show success toast when found and opening confirmation
        toast.success("Thanh toán hóa đơn", {
          description: `Đã tìm thấy hóa đơn "${bill.bill_name}". Vui lòng xác nhận thanh toán.`,
          duration: 3000,
        });

        clearIntent(); // Clear intent after handling
      } else {
        toast.info(`Hóa đơn "${bill.bill_name}" đã được thanh toán rồi`, {
          duration: 3000,
        });
        clearIntent();
      }
    }
  }, [extractedIntent, bills, clearIntent]);

  const handlePayBill = async (billId: number, billName: string) => {
    if (payingBillId) return; // Prevent multiple simultaneous payments

    try {
      setPayingBillId(billId);
      await payBill(billId);

      // Đóng dialog trước (nếu đang mở)
      setPayConfirmDialog({ open: false, billId: null, billName: "", amount: 0 });

      toast.success(`Đã thanh toán hóa đơn "${billName}"`);

      // Reload danh sách hóa đơn
      await refreshBills();
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

  // Handle bill selection from disambiguation dialog
  const handleBillSelection = (bill: (typeof disambiguationDialog.bills)[0]) => {
    try {
      // Close disambiguation dialog
      setDisambiguationDialog({ open: false, bills: [] });

      // Open pay confirmation for selected bill
      if (bill.status !== "paid") {
        setPayConfirmDialog({
          open: true,
          billId: bill.id,
          billName: bill.bill_name,
          amount: bill.amount,
        });
      } else {
        toast.info(`Hóa đơn "${bill.bill_name}" đã được thanh toán rồi`, {
          duration: 3000,
        });
      }
    } catch (error) {
      console.error("Error in handleBillSelection:", error);
      toast.error("Có lỗi xảy ra khi chọn hóa đơn. Vui lòng thử lại.");
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
        <CardHeader>
          <CardTitle>Hóa đơn chi tiêu</CardTitle>
          <CardDescription>Theo dõi hóa đơn và chi phí</CardDescription>
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
                Tạo hóa đơn
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

      {/* Pay Bill Confirmation Dialog */}
      <AlertDialog
        open={payConfirmDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setPayConfirmDialog({ open: false, billId: null, billName: "", amount: 0 });
          }
        }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xác nhận thanh toán</AlertDialogTitle>
            <AlertDialogDescription>
              Bạn có chắc chắn muốn thanh toán hóa đơn <strong>{payConfirmDialog.billName}</strong> với số tiền{" "}
              <strong>{payConfirmDialog.amount.toLocaleString("vi-VN")} đ</strong>?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              onClick={async () => {
                if (payConfirmDialog.billId) {
                  await handlePayBill(payConfirmDialog.billId, payConfirmDialog.billName);
                  setPayConfirmDialog({ open: false, billId: null, billName: "", amount: 0 });
                }
              }}>
              Xác nhận thanh toán
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Disambiguation Dialog - When multiple bills have the same name */}
      <AlertDialog
        open={disambiguationDialog.open}
        onOpenChange={(open) => !open && setDisambiguationDialog({ open: false, bills: [] })}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Chọn hóa đơn
            </AlertDialogTitle>
            <AlertDialogDescription>
              Tìm thấy nhiều hóa đơn có cùng tên. Vui lòng chọn hóa đơn bạn muốn thanh toán:
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {disambiguationDialog.bills.map((bill) => (
              <button
                key={bill.id}
                onClick={() => handleBillSelection(bill)}
                disabled={bill.status === "paid"}
                className="w-full p-4 rounded-lg border border-border hover:border-primary hover:bg-accent transition-all text-left group disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:border-border disabled:hover:bg-transparent">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-base group-hover:text-primary transition-colors">
                        {bill.bill_name}
                      </h4>
                      {bill.category && (
                        <Badge variant="outline" className="text-xs">
                          {getCategoryText(bill.category)}
                        </Badge>
                      )}
                      {bill.status === "paid" && (
                        <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                          Đã thanh toán
                        </Badge>
                      )}
                      {bill.status === "overdue" && (
                        <Badge variant="outline" className="text-xs bg-red-50 text-red-700 border-red-200">
                          Quá hạn
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>
                        Số tiền:{" "}
                        <span className="font-medium text-foreground">{bill.amount.toLocaleString("vi-VN")} VND</span>
                      </span>
                      <span>•</span>
                      <span>
                        Hạn:{" "}
                        <span className="font-medium">
                          {bill.dueDate instanceof Date
                            ? bill.dueDate.toLocaleDateString("vi-VN")
                            : new Date(bill.dueDate).toLocaleDateString("vi-VN")}
                        </span>
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDisambiguationDialog({ open: false, bills: [] })}>
              Hủy
            </AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Card>
  );
}
