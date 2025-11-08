"use client";

import { useEffect } from "react";
import { useSpeech } from "@/lib/speech-context";
import { UseFormReturn } from "react-hook-form";

/**
 * Hook to automatically fill form fields from voice parameters
 *
 * @param form - React Hook Form instance
 * @param intentType - Expected intent type for this form
 * @param fieldMapping - Mapping from voice parameter names to form field names
 *
 * @example
 * ```tsx
 * const form = useForm<BillFormData>();
 *
 * useVoiceFormFill(form, "create_bill", {
 *   bill_name: "billName",
 *   amount: "amount",
 *   category: "category",
 *   due_date: "dueDate",
 * });
 * ```
 */
export function useVoiceFormFill<T extends Record<string, any>>(
  form: UseFormReturn<T>,
  intentType: string,
  fieldMapping: Record<string, keyof T>
) {
  const { extractedIntent } = useSpeech();

  useEffect(() => {
    // Only fill if we have an intent and it matches the expected type
    if (!extractedIntent || extractedIntent.intent_type !== intentType) {
      return;
    }

    // Fill form fields based on mapping
    Object.entries(fieldMapping).forEach(([voiceParam, formField]) => {
      const value = extractedIntent.parameters[voiceParam];

      if (value !== undefined && value !== null) {
        // Type assertion to handle generic Path type
        form.setValue(formField as any, value as any, {
          shouldValidate: true,
          shouldDirty: true,
        });
      }
    });

    // Mark form as touched - removed setFocus to avoid type errors
    // User will see the filled values immediately
  }, [extractedIntent, intentType, fieldMapping, form]);
}

/**
 * Hook to get current form data for voice context initialization
 *
 * @param form - React Hook Form instance
 * @returns Current form values
 *
 * @example
 * ```tsx
 * const form = useForm<BillFormData>();
 * const formData = useVoiceFormData(form);
 *
 * // Pass to startListening
 * startListening(formData, "create_bill");
 * ```
 */
export function useVoiceFormData<T extends Record<string, any>>(form: UseFormReturn<T>): Record<string, any> {
  const values = form.watch();

  // Filter out empty values
  return Object.entries(values).reduce((acc, [key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      acc[key] = value;
    }
    return acc;
  }, {} as Record<string, any>);
}
