"use client";

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
import { useSpeech } from "@/lib/speech-context";

interface VoiceConfirmationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function VoiceConfirmationDialog({ open, onOpenChange }: VoiceConfirmationDialogProps) {
  const { extractedIntent, transcript, normalizedText, confirmExecution, cancelExecution } = useSpeech();

  const handleConfirm = () => {
    confirmExecution();
    onOpenChange(false);
  };

  const handleCancel = () => {
    cancelExecution();
    onOpenChange(false);
  };

  if (!extractedIntent) {
    return null;
  }

  // Map intent types to Vietnamese
  const intentNameMap: Record<string, string> = {
    create_bill: "Tạo hóa đơn",
    pay_bill: "Thanh toán hóa đơn",
    create_transfer: "Chuyển tiền",
    deposit: "Nạp tiền",
    withdraw: "Rút tiền",
    create_fund: "Tạo quỹ tiết kiệm",
    add_to_fund: "Thêm vào quỹ",
  };

  const intentName = intentNameMap[extractedIntent.intent_type] || extractedIntent.intent_type;

  // Format parameter value for display
  const formatParamValue = (key: string, value: any): string => {
    // Format amount with thousand separators
    if (key === "amount" || key === "target_amount" || key === "initial_amount" || key === "monthly_contribution") {
      const num = parseFloat(String(value));
      if (!isNaN(num)) {
        return num.toLocaleString("vi-VN") + " VND";
      }
    }

    // Format category to Vietnamese
    if (key === "category") {
      const categoryMap: Record<string, string> = {
        utilities: "Tiện ích",
        rent: "Tiền thuê",
        insurance: "Bảo hiểm",
        subscription: "Đăng ký",
        internet: "Internet",
        phone: "Điện thoại",
        transportation: "Di chuyển",
        food: "Ăn uống",
        healthcare: "Y tế",
        education: "Giáo dục",
        entertainment: "Giải trí",
        shopping: "Mua sắm",
        other: "Khác",
        // Fund categories
        travel: "Du lịch",
        emergency: "Khẩn cấp",
        purchase: "Mua sắm",
        retirement: "Hưu trí",
      };
      return categoryMap[String(value)] || String(value);
    }

    // Format date
    if (key === "due_date" || key === "target_date") {
      try {
        const date = new Date(String(value));
        return date.toLocaleDateString("vi-VN");
      } catch {
        return String(value);
      }
    }

    return String(value);
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="sm:max-w-[500px] max-w-[90vw]">
        <AlertDialogHeader>
          <AlertDialogTitle className="text-xl">Xác nhận lệnh thoại</AlertDialogTitle>
          <AlertDialogDescription className="sr-only">
            Xác nhận thực hiện lệnh thoại đã nhận dạng
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-3 pt-2 pb-4">
          <div>
            <span className="text-sm font-medium text-foreground">Bạn đã nói: </span>
            <span className="text-sm text-muted-foreground italic">"{transcript}"</span>
          </div>

          {normalizedText && normalizedText !== transcript && (
            <div>
              <span className="text-sm font-medium text-foreground">Đã chuyển đổi: </span>
              <span className="text-sm text-muted-foreground">"{normalizedText}"</span>
            </div>
          )}

          <div className="pt-2 border-t">
            <div className="text-sm font-medium text-foreground mb-2">Hành động: {intentName}</div>
            <div className="space-y-1">
              {Object.entries(extractedIntent.parameters).map(([key, value]) => {
                // Format parameter names to Vietnamese
                const paramNameMap: Record<string, string> = {
                  bill_name: "Tên hóa đơn",
                  amount: "Số tiền",
                  category: "Danh mục",
                  due_date: "Hạn thanh toán",
                  recipient_account_number: "Số tài khoản",
                  recipient_name: "Người nhận",
                  description: "Mô tả",
                  fund_name: "Tên quỹ",
                  target_amount: "Mục tiêu",
                };

                const paramName = paramNameMap[key] || key;

                return (
                  <div key={key} className="text-sm">
                    <span className="font-medium">{paramName}:</span>{" "}
                    <span className="text-muted-foreground">{formatParamValue(key, value)}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {extractedIntent.intent_changed && (
            <div className="bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
              <span className="text-sm text-blue-800 dark:text-blue-300">
                ℹ️ Hệ thống phát hiện bạn muốn thực hiện hành động khác với màn hình hiện tại.
              </span>
            </div>
          )}

          <div className="text-sm text-muted-foreground pt-2">Bạn có chắc muốn thực hiện hành động này?</div>
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel onClick={handleCancel}>Hủy</AlertDialogCancel>
          <AlertDialogAction onClick={handleConfirm} className="bg-emerald-600 hover:bg-emerald-700">
            Xác nhận
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
