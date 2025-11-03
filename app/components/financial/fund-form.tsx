"use client";

import type React from "react";
import { useState } from "react";
import { useFinancial } from "@/lib/financial-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { DatePicker } from "@/components/ui/date-picker";
import { toast } from "sonner";

const FUND_CATEGORIES = [
  { value: "travel", label: "Du lịch" },
  { value: "education", label: "Giáo dục" },
  { value: "emergency", label: "Khẩn cấp" },
  { value: "purchase", label: "Mua sắm" },
  { value: "retirement", label: "Hưu trí" },
  { value: "other", label: "Khác" },
];

interface FormErrors {
  fund_name?: string;
  target_amount?: string;
  target_date?: string;
  initial_amount?: string;
  monthly_contribution?: string;
}

export function FundForm({ onSuccess }: { onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    fund_name: "",
    target_amount: "",
    target_date: "",
    initial_amount: "0",
    monthly_contribution: "0",
    category: "other",
    auto_transfer: false,
    notes: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(false);
  const { addFund } = useFinancial();

  // Get minimum date (today) for date input
  const getMinDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, "0");
    const day = String(today.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const validateField = (name: string, value: string | number): string | undefined => {
    switch (name) {
      case "fund_name":
        if (!value || (typeof value === "string" && value.trim().length === 0)) {
          return "Tên quỹ không được để trống";
        }
        if (typeof value === "string" && value.trim().length < 1) {
          return "Tên quỹ phải có ít nhất 1 ký tự";
        }
        if (typeof value === "string" && value.trim().length > 100) {
          return "Tên quỹ không được vượt quá 100 ký tự";
        }
        return undefined;

      case "target_amount":
        if (!value || value === "") {
          return "Số tiền mục tiêu không được để trống";
        }
        const targetAmount = parseFloat(String(value));
        if (isNaN(targetAmount)) {
          return "Số tiền mục tiêu phải là số";
        }
        if (targetAmount < 100000) {
          return "Số tiền mục tiêu phải từ 100,000 VND trở lên";
        }
        if (targetAmount > 10000000000) {
          return "Số tiền mục tiêu không được vượt quá 10,000,000,000 VND";
        }
        return undefined;

      case "target_date":
        if (!value || value === "") {
          return "Ngày mục tiêu không được để trống";
        }
        const selectedDate = new Date(value);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (selectedDate < today) {
          return "Ngày mục tiêu không được là ngày trong quá khứ";
        }
        return undefined;

      case "initial_amount":
        if (value !== "" && value !== "0") {
          const initialAmount = parseFloat(String(value));
          if (isNaN(initialAmount)) {
            return "Số tiền ban đầu phải là số";
          }
          if (initialAmount < 0) {
            return "Số tiền ban đầu không được âm";
          }
        }
        return undefined;

      case "monthly_contribution":
        if (value !== "" && value !== "0") {
          const monthlyAmount = parseFloat(String(value));
          if (isNaN(monthlyAmount)) {
            return "Số tiền đóng góp hàng tháng phải là số";
          }
          if (monthlyAmount < 0) {
            return "Số tiền đóng góp hàng tháng không được âm";
          }
        }
        return undefined;

      default:
        return undefined;
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // Validate all required fields
    const fundNameError = validateField("fund_name", formData.fund_name);
    if (fundNameError) newErrors.fund_name = fundNameError;

    const targetAmountError = validateField("target_amount", formData.target_amount);
    if (targetAmountError) newErrors.target_amount = targetAmountError;

    const targetDateError = validateField("target_date", formData.target_date);
    if (targetDateError) newErrors.target_date = targetDateError;

    // Validate optional fields if they have values
    if (formData.initial_amount && formData.initial_amount !== "0") {
      const initialAmountError = validateField("initial_amount", formData.initial_amount);
      if (initialAmountError) newErrors.initial_amount = initialAmountError;
    }

    if (formData.monthly_contribution && formData.monthly_contribution !== "0") {
      const monthlyError = validateField("monthly_contribution", formData.monthly_contribution);
      if (monthlyError) newErrors.monthly_contribution = monthlyError;
    }

    setErrors(newErrors);
    setTouched({
      fund_name: true,
      target_amount: true,
      target_date: true,
      initial_amount: true,
      monthly_contribution: true,
    });

    return Object.keys(newErrors).length === 0;
  };

  const handleBlur = (fieldName: string) => {
    setTouched((prev) => ({ ...prev, [fieldName]: true }));
    const value = formData[fieldName as keyof typeof formData];
    const error = validateField(fieldName, value as string);
    setErrors((prev) => ({ ...prev, [fieldName]: error }));
  };

  const handleChange = (fieldName: string, value: string) => {
    setFormData((prev) => ({ ...prev, [fieldName]: value }));
    // Clear error when user starts typing
    if (touched[fieldName] && errors[fieldName as keyof FormErrors]) {
      const error = validateField(fieldName, value);
      setErrors((prev) => ({ ...prev, [fieldName]: error }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form
    if (!validateForm()) {
      toast.error("Vui lòng sửa các lỗi trong form");
      return;
    }

    setIsLoading(true);
    try {
      await addFund({
        fund_name: formData.fund_name.trim(),
        target_amount: parseFloat(formData.target_amount),
        target_date: formData.target_date,
        initial_amount: parseFloat(formData.initial_amount) || 0,
        monthly_contribution: parseFloat(formData.monthly_contribution) || 0,
        category: formData.category,
        auto_transfer: formData.auto_transfer,
        notes: formData.notes || undefined,
      });

      toast.success("Tạo quỹ tiết kiệm thành công");
      setFormData({
        fund_name: "",
        target_amount: "",
        target_date: "",
        initial_amount: "0",
        monthly_contribution: "0",
        category: "other",
        auto_transfer: false,
        notes: "",
      });
      setErrors({});
      setTouched({});
      onSuccess();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Tạo quỹ thất bại");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="fund_name">Tên quỹ *</Label>
            <Input
              id="fund_name"
              placeholder="Ví dụ: Du lịch châu Âu"
              value={formData.fund_name}
              onChange={(e) => handleChange("fund_name", e.target.value)}
              onBlur={() => handleBlur("fund_name")}
              className={touched.fund_name && errors.fund_name ? "border-red-500 focus-visible:ring-red-500" : ""}
            />
            {touched.fund_name && errors.fund_name && <p className="text-sm text-red-500">{errors.fund_name}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="category">Danh mục</Label>
            <select
              id="category"
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50">
              {FUND_CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="target_amount">Số tiền mục tiêu (VND) *</Label>
            <Input
              id="target_amount"
              type="number"
              placeholder="5000000"
              step="1000"
              min="100000"
              value={formData.target_amount}
              onChange={(e) => handleChange("target_amount", e.target.value)}
              onBlur={() => handleBlur("target_amount")}
              className={
                touched.target_amount && errors.target_amount ? "border-red-500 focus-visible:ring-red-500" : ""
              }
            />
            {touched.target_amount && errors.target_amount && (
              <p className="text-sm text-red-500">{errors.target_amount}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="target_date">Ngày mục tiêu *</Label>
            <DatePicker
              id="target_date"
              value={formData.target_date}
              onChange={(value) => handleChange("target_date", value)}
              onBlur={() => handleBlur("target_date")}
              min={getMinDate()}
              error={touched.target_date && !!errors.target_date}
            />
            {touched.target_date && errors.target_date && <p className="text-sm text-red-500">{errors.target_date}</p>}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="initial_amount">Số tiền ban đầu (VND)</Label>
            <Input
              id="initial_amount"
              type="number"
              placeholder="0"
              step="1000"
              min="0"
              value={formData.initial_amount}
              onChange={(e) => handleChange("initial_amount", e.target.value)}
              onBlur={() => handleBlur("initial_amount")}
              className={
                touched.initial_amount && errors.initial_amount ? "border-red-500 focus-visible:ring-red-500" : ""
              }
            />
            {touched.initial_amount && errors.initial_amount ? (
              <p className="text-sm text-red-500">{errors.initial_amount}</p>
            ) : (
              <p className="text-xs text-muted-foreground">Số tiền nạp ban đầu khi tạo quỹ</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="monthly_contribution">Đóng góp hàng tháng (VND)</Label>
            <Input
              id="monthly_contribution"
              type="number"
              placeholder="0"
              step="1000"
              min="0"
              value={formData.monthly_contribution}
              onChange={(e) => handleChange("monthly_contribution", e.target.value)}
              onBlur={() => handleBlur("monthly_contribution")}
              className={
                touched.monthly_contribution && errors.monthly_contribution
                  ? "border-red-500 focus-visible:ring-red-500"
                  : ""
              }
            />
            {touched.monthly_contribution && errors.monthly_contribution ? (
              <p className="text-sm text-red-500">{errors.monthly_contribution}</p>
            ) : (
              <p className="text-xs text-muted-foreground">Số tiền dự kiến đóng góp mỗi tháng</p>
            )}
          </div>
        </div>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox
              id="auto_transfer"
              checked={formData.auto_transfer}
              onChange={(e) => setFormData({ ...formData, auto_transfer: e.target.checked })}
            />
            <Label htmlFor="auto_transfer" className="text-sm font-normal cursor-pointer">
              Tự động chuyển tiền hàng tháng
            </Label>
          </div>
        </div>
        <div className="space-y-2">
          <Label htmlFor="notes">Ghi chú</Label>
          <Textarea
            id="notes"
            placeholder="Ghi chú về quỹ tiết kiệm..."
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            rows={3}
          />
        </div>
        <div className="rounded-b-xl sm:rounded-b-2xl sticky bottom-0 left-0 right-0 bg-background border-t pt-4 -mx-4 sm:-mx-6 px-4 sm:px-6 pb-4 shadow-lg z-10">
          <Button type="submit" form="fund-form" className="w-full" disabled={isLoading}>
            {isLoading ? "Đang tạo..." : "Tạo quỹ tiết kiệm"}
          </Button>
        </div>
      </form>
    </>
  );
}
