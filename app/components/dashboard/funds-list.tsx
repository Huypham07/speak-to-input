"use client";

import { useFinancial } from "@/lib/financial-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PiggyBank, Plus, Minus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Skeleton } from "@/components/ui/skeleton";

interface FundsListProps {
  onCreateFund?: () => void;
}

export function FundsList({ onCreateFund }: FundsListProps = {}) {
  const { funds, isLoadingFunds, depositToFund, withdrawFromFund, deleteFund } = useFinancial();
  const [depositDialog, setDepositDialog] = useState<{ open: boolean; fundId: number | null }>({
    open: false,
    fundId: null,
  });
  const [withdrawDialog, setWithdrawDialog] = useState<{ open: boolean; fundId: number | null }>({
    open: false,
    fundId: null,
  });
  const [amount, setAmount] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedFund, setSelectedFund] = useState<{ id: number; current_amount: number; target_amount: number; fund_name: string } | null>(null);
  const [selectedFundForWithdraw, setSelectedFundForWithdraw] = useState<{ id: number; current_amount: number; target_amount: number; fund_name: string } | null>(null);
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<{ open: boolean; fundId: number | null; fundName: string }>({
    open: false,
    fundId: null,
    fundName: "",
  });

  const getCategoryLabel = (category: string | null) => {
    if (!category) return "Khác";
    const labels: Record<string, string> = {
      travel: "Du lịch",
      education: "Giáo dục",
      emergency: "Khẩn cấp",
      purchase: "Mua sắm",
      retirement: "Hưu trí",
      other: "Khác",
    };
    return labels[category] || category;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-400">Đang hoạt động</Badge>;
      case "completed":
        return <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-400">Hoàn thành</Badge>;
      case "cancelled":
        return <Badge variant="outline" className="bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-950 dark:text-gray-400">Đã hủy</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleDeposit = async () => {
    if (!depositDialog.fundId || !amount) return;

    const depositAmount = parseFloat(amount);
    if (!selectedFund) return;

    // Validate: không cho nạp nếu vượt quá target_amount
    const newTotal = selectedFund.current_amount + depositAmount;
    if (newTotal > selectedFund.target_amount) {
      toast.error(
        `Không thể nạp vượt quá số tiền mục tiêu. Số tiền tối đa có thể nạp: ${(selectedFund.target_amount - selectedFund.current_amount).toLocaleString("vi-VN")} VND`
      );
      return;
    }

    setIsProcessing(true);
    try {
      await depositToFund(depositDialog.fundId, depositAmount);
      toast.success(`Đã nạp ${depositAmount.toLocaleString("vi-VN")} VND thành công vào quỹ ${selectedFund.fund_name}`, {
        duration: 3000,
      });
      setDepositDialog({ open: false, fundId: null });
      setAmount("");
      setSelectedFund(null);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Nạp tiền thất bại";
      toast.error(errorMessage, {
        duration: 4000,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleWithdraw = async () => {
    if (!withdrawDialog.fundId || !amount) return;

    const withdrawAmount = parseFloat(amount);
    if (!selectedFundForWithdraw) return;

    // Validate: không cho rút nhiều hơn số tiền trong quỹ
    if (withdrawAmount > selectedFundForWithdraw.current_amount) {
      toast.error(
        `Không thể rút vượt quá số tiền hiện có. Số tiền tối đa có thể rút: ${selectedFundForWithdraw.current_amount.toLocaleString("vi-VN")} VND`,
        {
          duration: 4000,
        }
      );
      return;
    }

    if (withdrawAmount <= 0) {
      toast.error("Số tiền rút phải lớn hơn 0", {
        duration: 3000,
      });
      return;
    }

    setIsProcessing(true);
    try {
      await withdrawFromFund(withdrawDialog.fundId, withdrawAmount);
      toast.success(`Đã rút ${withdrawAmount.toLocaleString("vi-VN")} VND thành công từ quỹ ${selectedFundForWithdraw.fund_name}`, {
        duration: 3000,
      });
      setWithdrawDialog({ open: false, fundId: null });
      setAmount("");
      setSelectedFundForWithdraw(null);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Rút tiền thất bại";
      toast.error(errorMessage, {
        duration: 4000,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDeleteClick = (fundId: number, fundName: string, currentAmount: number) => {
    // Kiểm tra nếu quỹ còn tiền
    if (currentAmount > 0) {
      toast.error(
        `Quỹ "${fundName}" vẫn còn ${currentAmount.toLocaleString("vi-VN")} VND. Vui lòng rút hết tiền trước khi xóa quỹ.`,
        {
          duration: 5000,
        }
      );
      return;
    }

    // Nếu quỹ trống, hiển thị dialog xác nhận
    setDeleteConfirmDialog({
      open: true,
      fundId,
      fundName,
    });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmDialog.fundId) return;

    try {
      await deleteFund(deleteConfirmDialog.fundId);
      toast.success(`Đã xóa quỹ "${deleteConfirmDialog.fundName}" thành công`, {
        duration: 3000,
      });
      setDeleteConfirmDialog({ open: false, fundId: null, fundName: "" });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Xóa quỹ thất bại";
      toast.error(errorMessage, {
        duration: 4000,
      });
    }
  };

  if (isLoadingFunds) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Quỹ tiết kiệm</CardTitle>
          <CardDescription>Mục tiêu và tiến độ tiết kiệm</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (funds.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Quỹ tiết kiệm</CardTitle>
          <CardDescription>Mục tiêu và tiến độ tiết kiệm</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <PiggyBank className="h-12 w-12 text-muted-foreground mx-auto mb-4 opacity-50" />
            <p className="text-muted-foreground mb-4">Chưa có quỹ tiết kiệm nào</p>
            {onCreateFund && (
              <Button onClick={onCreateFund} className="gap-2">
                <Plus className="h-4 w-4" />
                Tạo quỹ mới
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Quỹ tiết kiệm</CardTitle>
              <CardDescription>Mục tiêu và tiến độ tiết kiệm</CardDescription>
            </div>
            {onCreateFund && (
              <Button onClick={onCreateFund} size="sm" className="gap-2">
                <Plus className="h-4 w-4" />
                Tạo quỹ mới
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {funds.slice(0, 5).map((fund) => {
              const progress = fund.progress_percentage || (fund.current_amount / fund.target_amount) * 100;
              return (
                <div key={fund.id} className="p-4 border border-border rounded-lg hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center shrink-0">
                        <PiggyBank className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="font-medium truncate">{fund.fund_name}</p>
                        <p className="text-xs text-muted-foreground">{getCategoryLabel(fund.category)}</p>
                        <div className="mt-1">{getStatusBadge(fund.status)}</div>
                      </div>
                    </div>
                  </div>
                  <div className="space-y-2 mb-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">
                        {fund.current_amount.toLocaleString("vi-VN")} đ / {fund.target_amount.toLocaleString("vi-VN")} đ
                      </span>
                      <span className="font-medium">{Math.round(progress)}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-emerald-500 to-emerald-600 h-2 rounded-full transition-all"
                        style={{ width: `${Math.min(progress, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setDepositDialog({ open: true, fundId: fund.id });
                        setSelectedFund({
                          id: fund.id,
                          current_amount: fund.current_amount,
                          target_amount: fund.target_amount,
                          fund_name: fund.fund_name,
                        });
                      }}
                      className="flex-1"
                      disabled={fund.status !== "active"}>
                      <Plus className="h-4 w-4 mr-1" />
                      Nạp
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setWithdrawDialog({ open: true, fundId: fund.id });
                        setSelectedFundForWithdraw({
                          id: fund.id,
                          current_amount: fund.current_amount,
                          target_amount: fund.target_amount,
                          fund_name: fund.fund_name,
                        });
                      }}
                      className="flex-1"
                      disabled={fund.status !== "active" || fund.current_amount === 0}>
                      <Minus className="h-4 w-4 mr-1" />
                      Rút
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDeleteClick(fund.id, fund.fund_name, fund.current_amount)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Deposit Dialog */}
      <Dialog
        open={depositDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setDepositDialog({ open: false, fundId: null });
            setAmount("");
            setSelectedFund(null);
          }
        }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nạp tiền vào quỹ</DialogTitle>
            <DialogDescription>
              {selectedFund && (
                <span>
                  Số dư hiện tại: {selectedFund.current_amount.toLocaleString("vi-VN")} VND / Mục tiêu:{" "}
                  {selectedFund.target_amount.toLocaleString("vi-VN")} VND
                  <br />
                  Số tiền tối đa có thể nạp:{" "}
                  {(selectedFund.target_amount - selectedFund.current_amount).toLocaleString("vi-VN")} VND
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="deposit-amount">Số tiền (VND)</Label>
              <Input
                id="deposit-amount"
                type="number"
                placeholder="100000"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                min="1000"
                step="1000"
                max={selectedFund ? selectedFund.target_amount - selectedFund.current_amount : undefined}
              />
              {selectedFund && amount && !isNaN(parseFloat(amount)) && (
                <p className="text-xs text-muted-foreground">
                  Sau khi nạp:{" "}
                  {(selectedFund.current_amount + parseFloat(amount)).toLocaleString("vi-VN")} VND /{" "}
                  {selectedFund.target_amount.toLocaleString("vi-VN")} VND
                  {selectedFund.current_amount + parseFloat(amount) > selectedFund.target_amount && (
                    <span className="text-red-500 ml-2">(Vượt quá mục tiêu!)</span>
                  )}
                </p>
              )}
            </div>
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => {
                  setDepositDialog({ open: false, fundId: null });
                  setAmount("");
                  setSelectedFund(null);
                }}>
                Hủy
              </Button>
              <Button
                onClick={handleDeposit}
                disabled={
                  !amount ||
                  isProcessing ||
                  parseFloat(amount) <= 0 ||
                  (selectedFund !== null &&
                    selectedFund.current_amount + parseFloat(amount) > selectedFund.target_amount)
                }>
                {isProcessing ? "Đang xử lý..." : "Nạp tiền"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Withdraw Dialog */}
      <Dialog
        open={withdrawDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setWithdrawDialog({ open: false, fundId: null });
            setAmount("");
            setSelectedFundForWithdraw(null);
          }
        }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rút tiền từ quỹ</DialogTitle>
            <DialogDescription>
              {selectedFundForWithdraw && (
                <span>
                  Số tiền hiện có: {selectedFundForWithdraw.current_amount.toLocaleString("vi-VN")} VND
                  <br />
                  Số tiền tối đa có thể rút: {selectedFundForWithdraw.current_amount.toLocaleString("vi-VN")} VND
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="withdraw-amount">Số tiền (VND)</Label>
              <Input
                id="withdraw-amount"
                type="number"
                placeholder="100000"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                min="1000"
                step="1000"
                max={selectedFundForWithdraw ? selectedFundForWithdraw.current_amount : undefined}
              />
              {selectedFundForWithdraw && amount && !isNaN(parseFloat(amount)) && (
                <p className="text-xs text-muted-foreground">
                  Sau khi rút:{" "}
                  {(selectedFundForWithdraw.current_amount - parseFloat(amount)).toLocaleString("vi-VN")} VND
                  {parseFloat(amount) > selectedFundForWithdraw.current_amount && (
                    <span className="text-red-500 ml-2">(Vượt quá số tiền hiện có!)</span>
                  )}
                </p>
              )}
            </div>
            <div className="flex gap-2 justify-end">
              <Button
                variant="outline"
                onClick={() => {
                  setWithdrawDialog({ open: false, fundId: null });
                  setAmount("");
                  setSelectedFundForWithdraw(null);
                }}
                disabled={isProcessing}>
                Hủy
              </Button>
              <Button
                onClick={handleWithdraw}
                disabled={
                  !amount ||
                  isProcessing ||
                  parseFloat(amount) <= 0 ||
                  (selectedFundForWithdraw !== null &&
                    parseFloat(amount) > selectedFundForWithdraw.current_amount)
                }>
                {isProcessing ? "Đang xử lý..." : "Rút tiền"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={deleteConfirmDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteConfirmDialog({ open: false, fundId: null, fundName: "" });
          }
        }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xác nhận xóa quỹ</AlertDialogTitle>
            <AlertDialogDescription>
              Bạn có chắc chắn muốn xóa quỹ <strong>"{deleteConfirmDialog.fundName}"</strong> không?
              <br />
              <span className="text-red-500 font-medium">Hành động này không thể hoàn tác.</span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Hủy</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              className="bg-red-600 hover:bg-red-700 focus:ring-red-600">
              Xóa quỹ
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
