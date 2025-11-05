"use client";

import type React from "react";
import { useState } from "react";
import { useFinancial } from "@/lib/financial-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";

const BILL_CATEGORIES = [
  { value: "utilities", label: "Tiện ích (điện, nước, gas)" },
  { value: "rent", label: "Tiền nhà" },
  { value: "insurance", label: "Bảo hiểm" },
  { value: "subscription", label: "Dịch vụ đăng ký" },
  { value: "other", label: "Khác" },
];

interface FormErrors {
  bill_name?: string;
  amount?: string;
  due_date?: string;
}

export function BillForm({ onSuccess }: { onSuccess: () => void }) {
  const [formData, setFormData] = useState({
    bill_name: "",
    amount: "",
    due_date: "",
    category: "other",
    recurring: false,
    notes: "",
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isLoading, setIsLoading] = useState(false);
  const { addBill, refreshBills } = useFinancial();

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
      case "title":
        if (!value || (typeof value === "string" && value.trim().length === 0)) {
          return "Tên hóa đơn không được để trống";
        }
        if (typeof value === "string" && value.trim().length > 100) {
          return "Tên hóa đơn không được vượt quá 100 ký tự";
        }
        return undefined;

      case "amount":
        if (!value || value === "") {
          return "Số tiền không được để trống";
        }
        const amount = parseFloat(String(value));
        if (isNaN(amount)) {
          return "Số tiền phải là số";
        }
        if (amount < 1000) {
          return "Số tiền phải từ 1,000 VND trở lên";
        }
        if (amount > 100000000) {
          return "Số tiền không được vượt quá 100,000,000 VND";
        }
        return undefined;

      case "due_date":
        if (!value || value === "") {
          return "Ngày hết hạn không được để trống";
        }
        return undefined;

      default:
        return undefined;
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    const billNameError = validateField("bill_name", formData.bill_name);
    if (billNameError) newErrors.bill_name = billNameError;

    const amountError = validateField("amount", formData.amount);
    if (amountError) newErrors.amount = amountError;

    const dueDateError = validateField("due_date", formData.due_date);
    if (dueDateError) newErrors.due_date = dueDateError;

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleBlur = (name: string) => {
    setTouched({ ...touched, [name]: true });
    const value = formData[name as keyof typeof formData];
    // Only validate fields that accept string/number (not boolean)
    if (typeof value !== "boolean") {
      const error = validateField(name, value);
      setErrors({ ...errors, [name]: error });
    }
  };

  const handleChange = (name: string, value: string | boolean) => {
    setFormData({ ...formData, [name]: value });

    // Clear error when user starts typing (only validate string/number fields)
    if (touched[name] && typeof value !== "boolean") {
      const error = validateField(name, value);
      setErrors({ ...errors, [name]: error });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Mark all fields as touched
    setTouched({
      title: true,
      amount: true,
      due_date: true,
    });

    if (!validateForm()) {
      toast.error("Vui lòng kiểm tra lại thông tin");
      return;
    }

    setIsLoading(true);
    try {
      // Use addBill from context (which internally calls the API)
      await addBill({
        bill_name: formData.bill_name.trim(),
        category: formData.category,
        amount: parseFloat(formData.amount),
        dueDate: new Date(formData.due_date),
        notes: formData.notes.trim(),
        status: "pending",
        tags: [],
      });

      toast.success("Tạo hóa đơn thành công");

      // Refresh bills list
      await refreshBills();

      // Reset form
      setFormData({
        bill_name: "",
        amount: "",
        due_date: "",
        category: "other",
        recurring: false,
        notes: "",
      });
      setErrors({});
      setTouched({});

      onSuccess();
    } catch (error) {
      console.error("Create bill error:", error);
      toast.error(error instanceof Error ? error.message : "Tạo hóa đơn thất bại");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 pb-4">
      {/* Bill Name */}
      <div className="space-y-2">
        <Label htmlFor="title" className="text-sm font-medium">
          Tên hóa đơn <span className="text-red-500">*</span>
        </Label>
        <Input
          id="bill_name"
          placeholder='Ví dụ: "Tiền điện", "Tiền nước"'
          value={formData.bill_name}
          onChange={(e) => handleChange("bill_name", e.target.value)}
          onBlur={() => handleBlur("bill_name")}
          className={errors.bill_name && touched.bill_name ? "border-red-500" : ""}
          disabled={isLoading}
        />
        {errors.bill_name && touched.bill_name && <p className="text-sm text-red-500">{errors.bill_name}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Amount */}
        <div className="space-y-2">
          <Label htmlFor="amount" className="text-sm font-medium">
            Số tiền (VND) <span className="text-red-500">*</span>
          </Label>
          <Input
            id="amount"
            type="number"
            placeholder="1,000 - 100,000,000"
            step="1000"
            value={formData.amount}
            onChange={(e) => handleChange("amount", e.target.value)}
            onBlur={() => handleBlur("amount")}
            className={errors.amount && touched.amount ? "border-red-500" : ""}
            disabled={isLoading}
          />
          {errors.amount && touched.amount && <p className="text-sm text-red-500">{errors.amount}</p>}
        </div>

        {/* Due Date */}
        <div className="space-y-2">
          <Label htmlFor="due_date" className="text-sm font-medium">
            Ngày hết hạn <span className="text-red-500">*</span>
          </Label>
          <Input
            id="due_date"
            type="date"
            min={getMinDate()}
            value={formData.due_date}
            onChange={(e) => handleChange("due_date", e.target.value)}
            onBlur={() => handleBlur("due_date")}
            className={errors.due_date && touched.due_date ? "border-red-500" : ""}
            disabled={isLoading}
          />
          {errors.due_date && touched.due_date && <p className="text-sm text-red-500">{errors.due_date}</p>}
        </div>
      </div>

      {/* Category */}
      <div className="space-y-2">
        <Label htmlFor="category" className="text-sm font-medium">
          Danh mục
        </Label>
        <select
          id="category"
          className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          value={formData.category}
          onChange={(e) => handleChange("category", e.target.value)}
          disabled={isLoading}>
          {BILL_CATEGORIES.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>
      </div>

      {/* Recurring */}
      <div className="flex items-center space-x-2">
        <Checkbox
          id="recurring"
          checked={formData.recurring}
          onChange={(e) => handleChange("recurring", e.target.checked)}
          disabled={isLoading}
        />
        <Label
          htmlFor="recurring"
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer">
          Hóa đơn định kỳ hàng tháng
        </Label>
      </div>

      {/* Notes */}
      <div className="space-y-2">
        <Label htmlFor="description" className="text-sm font-medium">
          Ghi chú
        </Label>
        <Textarea
          id="notes"
          placeholder="Thêm ghi chú cho hóa đơn (không bắt buộc)"
          value={formData.notes}
          onChange={(e) => handleChange("notes", e.target.value)}
          rows={3}
          className="resize-none"
          disabled={isLoading}
        />
        <p className="text-xs text-muted-foreground">Tối đa 500 ký tự</p>
      </div>

      {/* Submit Button */}
      <div className="pt-4">
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? "Đang tạo..." : "Tạo hóa đơn"}
        </Button>
      </div>
    </form>
  );
}
