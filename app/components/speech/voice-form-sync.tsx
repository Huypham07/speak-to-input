"use client";

import { useEffect } from "react";
import { useSpeech } from "@/lib/speech-context";

interface VoiceFormSyncProps {
  intentType: string;
  onParametersReceived: (parameters: Record<string, any>) => void;
  getCurrentFormData?: () => Record<string, any>;
}

/**
 * Component to sync voice parameters with form state
 *
 * @example
 * ```tsx
 * <VoiceFormSync
 *   intentType="create_bill"
 *   onParametersReceived={(params) => {
 *     if (params.bill_name) setBillName(params.bill_name);
 *     if (params.amount) setAmount(params.amount);
 *     if (params.category) setCategory(params.category);
 *     if (params.due_date) setDueDate(params.due_date);
 *   }}
 *   getCurrentFormData={() => ({
 *     bill_name: billName,
 *     amount,
 *     category,
 *     due_date: dueDate,
 *   })}
 * />
 * ```
 */
export function VoiceFormSync({ intentType, onParametersReceived, getCurrentFormData }: VoiceFormSyncProps) {
  const { extractedIntent, startListening } = useSpeech();

  // Auto-fill form when voice parameters are received
  useEffect(() => {
    if (extractedIntent && extractedIntent.intent_type === intentType) {
      console.log(`📝 [VoiceFormSync] Auto-filling ${intentType} with:`, extractedIntent.parameters);
      onParametersReceived(extractedIntent.parameters);
    } else if (extractedIntent) {
      console.log(`⚠️ [VoiceFormSync] Intent mismatch: expected ${intentType}, got ${extractedIntent.intent_type}`);
    }
  }, [extractedIntent, intentType, onParametersReceived]);

  // This component doesn't render anything
  return null;
}

/**
 * Hook to handle voice button click with form context
 *
 * @param intentType - The intent type for this form
 * @param getFormData - Function to get current form data
 * @returns Function to start voice recording with form context
 *
 * @example
 * ```tsx
 * const handleVoiceClick = useVoiceWithFormContext("create_bill", () => ({
 *   bill_name: billName,
 *   amount,
 *   category,
 * }));
 *
 * <button onClick={handleVoiceClick}>Voice</button>
 * ```
 */
export function useVoiceWithFormContext(intentType: string, getFormData: () => Record<string, any>) {
  const { startListening } = useSpeech();

  return () => {
    const formData = getFormData();
    console.log(`🎤 [Voice] Starting with context:`, { intentType, formData });
    startListening(formData, intentType);
  };
}
