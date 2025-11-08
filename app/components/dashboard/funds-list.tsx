"use client";

import { useFinancial } from "@/lib/financial-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PiggyBank, Plus, Minus, Trash2, AlertTriangle, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { FormDialog, FormDialogHeader, FormDialogTitle, FormDialogDescription } from "@/components/ui/form-dialog";
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
import { useSpeech } from "@/lib/speech-context";

interface FundsListProps {
  onCreateFund?: () => void;
}

export function FundsList({ onCreateFund }: FundsListProps = {}) {
  const { funds, isLoadingFunds, depositToFund, withdrawFromFund, deleteFund, refreshFunds } = useFinancial();
  const { extractedIntent, clearIntent } = useSpeech();
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
  const [isDeletingFund, setIsDeletingFund] = useState(false);
  const [selectedFund, setSelectedFund] = useState<{
    id: number;
    current_amount: number;
    target_amount: number;
    fund_name: string;
  } | null>(null);
  const [selectedFundForWithdraw, setSelectedFundForWithdraw] = useState<{
    id: number;
    current_amount: number;
    target_amount: number;
    fund_name: string;
  } | null>(null);
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<{
    open: boolean;
    fundId: number | null;
    fundName: string;
    currentAmount: number;
  }>({
    open: false,
    fundId: null,
    fundName: "",
    currentAmount: 0,
  });

  // Disambiguation dialog for multiple matching funds
  const [disambiguationDialog, setDisambiguationDialog] = useState<{
    open: boolean;
    funds: Array<{
      id: number;
      fund_name: string;
      current_amount: number;
      target_amount: number;
      category: string | null;
    }>;
    action: "deposit" | "withdraw" | "delete" | null;
    amount?: number;
  }>({
    open: false,
    funds: [],
    action: null,
  });

  // Handle voice intents for fund operations
  useEffect(() => {
    if (!extractedIntent || extractedIntent.intent_changed || !funds || funds.length === 0) return;

    const { intent_type, parameters } = extractedIntent;

    // Find all matching funds by ID or name
    const findFunds = () => {
      if (parameters.fund_id) {
        const fund = funds.find((f) => f.id === parseInt(parameters.fund_id));
        return fund ? [fund] : [];
      } else if (parameters.fund_name) {
        const name = parameters.fund_name.toLowerCase();
        return funds.filter((f) => f.fund_name.toLowerCase() === name);
      }
      return [];
    };

    const matchingFunds = findFunds();

    // Check for duplicate names
    if (matchingFunds.length > 1) {
      // Show disambiguation dialog to let user choose
      // Use setTimeout to ensure overlay is closed and navigation is complete
      setTimeout(() => {
        setDisambiguationDialog({
          open: true,
          funds: matchingFunds,
          action: intent_type === "deposit_fund" ? "deposit" : intent_type === "withdraw_fund" ? "withdraw" : "delete",
          amount: parameters.amount,
        });
      }, 100); // Small delay to ensure UI is ready

      clearIntent(); // Clear intent to prevent re-trigger
      return;
    }

    const fund = matchingFunds[0];
    if (!fund) {
      // No matching fund found
      if (parameters.fund_name) {
        toast.error(`Không tìm thấy quỹ với tên "${parameters.fund_name}"`, {
          duration: 4000,
        });
      }
      clearIntent();
      return;
    }

    if (intent_type === "deposit_fund" && parameters.amount) {
      // Auto-open deposit dialog with fund and amount pre-filled
      setSelectedFund({
        id: fund.id,
        current_amount: fund.current_amount,
        target_amount: fund.target_amount,
        fund_name: fund.fund_name,
      });
      setAmount(String(parameters.amount));
      setDepositDialog({ open: true, fundId: fund.id });

      // Show success toast when found and opening dialog
      toast.success("Nạp vào quỹ", {
        description: `Đã tìm thấy quỹ "${fund.fund_name}". Vui lòng xác nhận số tiền.`,
        duration: 3000,
      });

      clearIntent(); // Clear intent after handling
    } else if (intent_type === "withdraw_fund" && parameters.amount) {
      // Auto-open withdraw dialog with fund and amount pre-filled
      setSelectedFundForWithdraw({
        id: fund.id,
        current_amount: fund.current_amount,
        target_amount: fund.target_amount,
        fund_name: fund.fund_name,
      });
      setAmount(String(parameters.amount));
      setWithdrawDialog({ open: true, fundId: fund.id });

      // Show success toast when found and opening dialog
      toast.success("Rút từ quỹ", {
        description: `Đã tìm thấy quỹ "${fund.fund_name}". Vui lòng xác nhận số tiền.`,
        duration: 3000,
      });

      clearIntent(); // Clear intent after handling
    } else if (intent_type === "delete_fund") {
      // Auto-open delete confirmation dialog
      setDeleteConfirmDialog({
        open: true,
        fundId: fund.id,
        fundName: fund.fund_name,
        currentAmount: fund.current_amount,
      });

      // Show info toast when found and opening confirmation
      toast.info("Xóa quỹ", {
        description: `Đã tìm thấy quỹ "${fund.fund_name}". Vui lòng xác nhận xóa.`,
        duration: 3000,
      });

      clearIntent(); // Clear intent after handling
    }
  }, [extractedIntent, funds, clearIntent]);

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

  // Handle fund selection from disambiguation dialog
  const handleFundSelection = (fund: (typeof disambiguationDialog.funds)[0]) => {
    try {
      const { action, amount } = disambiguationDialog;

      // Close disambiguation dialog
      setDisambiguationDialog({ open: false, funds: [], action: null });

      // Perform the action based on what was requested
      if (action === "deposit" && amount) {
        setSelectedFund({
          id: fund.id,
          current_amount: fund.current_amount,
          target_amount: fund.target_amount,
          fund_name: fund.fund_name,
        });
        setAmount(String(amount));
        setDepositDialog({ open: true, fundId: fund.id });
      } else if (action === "withdraw" && amount) {
        setSelectedFundForWithdraw({
          id: fund.id,
          current_amount: fund.current_amount,
          target_amount: fund.target_amount,
          fund_name: fund.fund_name,
        });
        setAmount(String(amount));
        setWithdrawDialog({ open: true, fundId: fund.id });
      } else if (action === "delete") {
        setDeleteConfirmDialog({
          open: true,
          fundId: fund.id,
          fundName: fund.fund_name,
          currentAmount: fund.current_amount,
        });
      }
    } catch (error) {
      console.error("Error in handleFundSelection:", error);
      toast.error("Có lỗi xảy ra khi chọn quỹ. Vui lòng thử lại.");
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "active":
        return (
          <Badge
            variant="outline"
            className="bg-green-50 text-green-700 border-green-200 dark:bg-green-950 dark:text-green-400">
            Đang hoạt động
          </Badge>
        );
      case "completed":
        return (
          <Badge
            variant="outline"
            className="bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-400">
            Hoàn thành
          </Badge>
        );
      case "cancelled":
        return (
          <Badge
            variant="outline"
            className="bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-950 dark:text-gray-400">
            Đã hủy
          </Badge>
        );
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
        `Không thể nạp vượt quá số tiền mục tiêu. Số tiền tối đa có thể nạp: ${(
          selectedFund.target_amount - selectedFund.current_amount
        ).toLocaleString("vi-VN")} VND`
      );
      return;
    }

    setIsProcessing(true);
    try {
      await depositToFund(depositDialog.fundId, depositAmount);
      toast.success(
        `Đã nạp ${depositAmount.toLocaleString("vi-VN")} VND thành công vào quỹ ${selectedFund.fund_name}`,
        {
          duration: 3000,
        }
      );
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
        `Không thể rút vượt quá số tiền hiện có. Số tiền tối đa có thể rút: ${selectedFundForWithdraw.current_amount.toLocaleString(
          "vi-VN"
        )} VND`,
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
      toast.success(
        `Đã rút ${withdrawAmount.toLocaleString("vi-VN")} VND thành công từ quỹ ${selectedFundForWithdraw.fund_name}`,
        {
          duration: 3000,
        }
      );
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
    // Luôn hiển thị dialog xác nhận (tiền sẽ tự động trả về tài khoản chính nếu có)
    setDeleteConfirmDialog({
      open: true,
      fundId,
      fundName,
      currentAmount,
    });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmDialog.fundId) return;

    setIsDeletingFund(true);
    try {
      await deleteFund(deleteConfirmDialog.fundId);

      // Đóng dialog trước
      setDeleteConfirmDialog({ open: false, fundId: null, fundName: "", currentAmount: 0 });

      // Hiển thị thông báo
      toast.success(
        deleteConfirmDialog.currentAmount > 0
          ? `Đã xóa quỹ "${deleteConfirmDialog.fundName}". ${deleteConfirmDialog.currentAmount.toLocaleString(
              "vi-VN"
            )} VND đã được tự động trả về tài khoản chính.`
          : `Đã xóa quỹ "${deleteConfirmDialog.fundName}" thành công`,
        {
          duration: 4000,
        }
      );

      // Reload danh sách quỹ
      await refreshFunds();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Xóa quỹ thất bại";
      toast.error(errorMessage, {
        duration: 4000,
      });
    } finally {
      setIsDeletingFund(false);
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
                        className="bg-linear-to-r from-emerald-500 to-emerald-600 h-2 rounded-full transition-all"
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
      <FormDialog
        open={depositDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setDepositDialog({ open: false, fundId: null });
            setAmount("");
            setSelectedFund(null);
          }
        }}
        className="max-w-2xl w-[95vw] sm:w-full rounded-xl sm:rounded-2xl">
        <FormDialogHeader>
          <FormDialogTitle>Nạp tiền vào quỹ</FormDialogTitle>
          <FormDialogDescription>
            {selectedFund && (
              <span>
                Số dư hiện tại: {selectedFund.current_amount.toLocaleString("vi-VN")} VND / Mục tiêu:{" "}
                {selectedFund.target_amount.toLocaleString("vi-VN")} VND
                <br />
                Số tiền tối đa có thể nạp:{" "}
                {(selectedFund.target_amount - selectedFund.current_amount).toLocaleString("vi-VN")} VND
              </span>
            )}
          </FormDialogDescription>
        </FormDialogHeader>
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
                Sau khi nạp: {(selectedFund.current_amount + parseFloat(amount)).toLocaleString("vi-VN")} VND /{" "}
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
                (selectedFund !== null && selectedFund.current_amount + parseFloat(amount) > selectedFund.target_amount)
              }>
              {isProcessing ? "Đang xử lý..." : "Nạp tiền"}
            </Button>
          </div>
        </div>
      </FormDialog>

      {/* Withdraw Dialog */}
      <FormDialog
        open={withdrawDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setWithdrawDialog({ open: false, fundId: null });
            setAmount("");
            setSelectedFundForWithdraw(null);
          }
        }}>
        <FormDialogHeader>
          <FormDialogTitle>Rút tiền từ quỹ</FormDialogTitle>
          <FormDialogDescription>
            {selectedFundForWithdraw && (
              <span>
                Số tiền hiện có: {selectedFundForWithdraw.current_amount.toLocaleString("vi-VN")} VND
                <br />
                Số tiền tối đa có thể rút: {selectedFundForWithdraw.current_amount.toLocaleString("vi-VN")} VND
              </span>
            )}
          </FormDialogDescription>
        </FormDialogHeader>
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
                Sau khi rút: {(selectedFundForWithdraw.current_amount - parseFloat(amount)).toLocaleString("vi-VN")} VND
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
                (selectedFundForWithdraw !== null && parseFloat(amount) > selectedFundForWithdraw.current_amount)
              }>
              {isProcessing ? "Đang xử lý..." : "Rút tiền"}
            </Button>
          </div>
        </div>
      </FormDialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog
        open={deleteConfirmDialog.open}
        onOpenChange={(open) => {
          // Không cho phép đóng dialog khi đang xóa
          if (!open && !isDeletingFund) {
            setDeleteConfirmDialog({ open: false, fundId: null, fundName: "", currentAmount: 0 });
          }
        }}>
        <AlertDialogContent className="max-w-md w-[95vw] sm:w-full rounded-xl sm:rounded-2xl p-0 gap-0 border border-border shadow-xl bg-background">
          {/* Header with Icon */}
          <div className="flex items-center gap-4 px-6 pt-6 pb-4 border-b border-border bg-card">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 dark:bg-destructive/20 shrink-0 ring-2 ring-destructive/20 dark:ring-destructive/30">
              <AlertTriangle className="h-6 w-6 text-destructive" />
            </div>
            <div className="flex-1 min-w-0">
              <AlertDialogTitle className="text-xl font-semibold text-foreground mb-1">
                Xác nhận xóa quỹ
              </AlertDialogTitle>
              <p className="text-sm text-muted-foreground">Hành động này không thể hoàn tác</p>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-5 space-y-4 bg-background">
            <p className="text-base text-foreground leading-relaxed">
              Bạn có chắc chắn muốn xóa quỹ{" "}
              <span className="font-semibold text-foreground">"{deleteConfirmDialog.fundName}"</span> không?
            </p>

            {deleteConfirmDialog.currentAmount > 0 && (
              <div className="flex items-start gap-3 p-4 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 shadow-sm">
                <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-amber-900 dark:text-amber-100 mb-1.5">Quỹ này còn tiền</p>
                  <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
                    Quỹ còn{" "}
                    <span className="font-semibold">
                      {deleteConfirmDialog.currentAmount.toLocaleString("vi-VN")} VND
                    </span>
                    . Số tiền này sẽ được tự động trả về tài khoản chính khi xóa quỹ.
                  </p>
                </div>
              </div>
            )}

            {deleteConfirmDialog.currentAmount === 0 && (
              <div className="flex items-center gap-2.5 p-3.5 rounded-lg bg-muted/50 dark:bg-muted/30 border border-border">
                <PiggyBank className="h-4 w-4 text-muted-foreground shrink-0" />
                <p className="text-sm text-muted-foreground">Quỹ này đang trống, có thể xóa an toàn.</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <AlertDialogFooter className="px-6 py-4 border-t border-border gap-3 sm:gap-2 bg-card/50">
            <AlertDialogCancel
              className="m-0 flex-1 sm:flex-initial border-border hover:bg-muted"
              disabled={isDeletingFund}>
              Hủy
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                // Ngăn dialog tự đóng khi click
                e.preventDefault();
                handleDeleteConfirm();
              }}
              disabled={isDeletingFund}
              className="m-0 flex-1 sm:flex-initial bg-destructive text-destructive-foreground hover:bg-destructive/90 focus:ring-destructive focus:ring-offset-2 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed">
              {isDeletingFund ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Đang xóa...
                </>
              ) : (
                <>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Xóa quỹ
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Disambiguation Dialog - When multiple funds have the same name */}
      <AlertDialog
        open={disambiguationDialog.open}
        onOpenChange={(open) => !open && setDisambiguationDialog({ open: false, funds: [], action: null })}>
        <AlertDialogContent className="max-w-2xl">
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <PiggyBank className="h-5 w-5 text-primary" />
              Chọn quỹ
            </AlertDialogTitle>
            <AlertDialogDescription>
              Tìm thấy nhiều quỹ có cùng tên. Vui lòng chọn quỹ bạn muốn{" "}
              {disambiguationDialog.action === "deposit"
                ? "nạp tiền vào"
                : disambiguationDialog.action === "withdraw"
                ? "rút tiền từ"
                : "xóa"}
              :
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {disambiguationDialog.funds.map((fund) => (
              <button
                key={fund.id}
                onClick={() => handleFundSelection(fund)}
                className="w-full p-4 rounded-lg border border-border hover:border-primary hover:bg-accent transition-all text-left group">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-base group-hover:text-primary transition-colors">
                        {fund.fund_name}
                      </h4>
                      {fund.category && (
                        <Badge variant="outline" className="text-xs">
                          {getCategoryLabel(fund.category)}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>
                        Số dư:{" "}
                        <span className="font-medium text-foreground">
                          {fund.current_amount.toLocaleString("vi-VN")} VND
                        </span>
                      </span>
                      <span>•</span>
                      <span>
                        Mục tiêu: <span className="font-medium">{fund.target_amount.toLocaleString("vi-VN")} VND</span>
                      </span>
                    </div>
                    <div className="mt-2">
                      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all"
                          style={{
                            width: `${Math.min((fund.current_amount / fund.target_amount) * 100, 100)}%`,
                          }}
                        />
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        {((fund.current_amount / fund.target_amount) * 100).toFixed(1)}% hoàn thành
                      </p>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel onClick={() => setDisambiguationDialog({ open: false, funds: [], action: null })}>
              Hủy
            </AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
