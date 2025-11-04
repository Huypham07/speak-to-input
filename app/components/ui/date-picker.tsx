"use client"

import * as React from "react"
import { Calendar as CalendarIcon } from "lucide-react"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

interface DatePickerProps {
  value?: string
  onChange?: (value: string) => void
  onBlur?: () => void
  min?: string
  error?: boolean
  className?: string
  id?: string
  placeholder?: string
}

export function DatePicker({
  value,
  onChange,
  onBlur,
  min,
  error,
  className,
  id,
  placeholder = "Chọn ngày",
}: DatePickerProps) {
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value
    onChange?.(newValue)
  }

  return (
    <div className="relative">
      <CalendarIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground pointer-events-none" />
      <Input
        type="date"
        id={id}
        value={value || ""}
        onChange={handleDateChange}
        onBlur={onBlur}
        min={min}
        placeholder={placeholder}
        className={cn(
          "pl-10",
          error && "border-red-500 focus-visible:ring-red-500",
          className
        )}
      />
    </div>
  )
}
