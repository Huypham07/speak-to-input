"use client"

import * as React from "react"
import { Check } from "lucide-react"
import { cn } from "@/lib/utils"

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {}

const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, checked, ...props }, ref) => {
    return (
      <div className="relative inline-flex items-center">
        <input
          type="checkbox"
          className="peer sr-only"
          ref={ref}
          checked={checked}
          {...props}
        />
        <div
          className={cn(
            "flex h-4 w-4 items-center justify-center rounded border-2 transition-all cursor-pointer",
            "border-input bg-background",
            "peer-checked:border-primary peer-checked:bg-primary",
            "peer-focus-visible:outline-none peer-focus-visible:ring-2 peer-focus-visible:ring-ring peer-focus-visible:ring-offset-2",
            "peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
            "peer-checked:hover:bg-primary/90",
            className
          )}
          aria-hidden="true"
        >
          <Check
            className={cn(
              "h-3 w-3 text-primary-foreground transition-opacity",
              checked ? "opacity-100" : "opacity-0"
            )}
          />
        </div>
      </div>
    )
  }
)
Checkbox.displayName = "Checkbox"

export { Checkbox }
