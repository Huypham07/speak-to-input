"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

interface FormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
  className?: string;
}

export function FormDialog({ open, onOpenChange, children, className }: FormDialogProps) {
  if (!open) return null;

  return (
    <>
      <div
        className={cn(
          "fixed bg-gray-800/70 backdrop-blur-xs z-50",
          "inset-0 bottom-0 md:bottom-0 md:inset-0",
          "animate-in fade-in-0 duration-200 m-0"
        )}
        aria-hidden="true"
      />

      {/* Dialog Content */}
      <div
        role="dialog"
        aria-modal="false"
        className={cn(
          "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg",
          "translate-x-[-50%] translate-y-[-50%]",
          "gap-4 border border-border bg-background p-6 shadow-lg",
          "animate-in fade-in-0 zoom-in-95 duration-200",
          "sm:rounded-lg",
          "pointer-events-auto",
          className
        )}>
        {children}

        {/* Close Button */}
        <button
          onClick={() => onOpenChange(false)}
          className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </button>
      </div>
    </>
  );
}

export function FormDialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col space-y-1.5 text-center sm:text-left", className)} {...props} />;
}

export function FormDialogTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn("text-lg font-semibold leading-none tracking-tight", className)} {...props} />;
}

export function FormDialogDescription({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("text-sm text-muted-foreground", className)} {...props} />;
}

export function FormDialogFooter({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className)} {...props} />;
}
