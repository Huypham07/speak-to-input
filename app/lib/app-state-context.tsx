"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

export type PageType = "dashboard" | "accounts" | "bills" | "funds" | "transfers";

export interface DialogState {
  isOpen: boolean;
  type: "transfer" | "bill" | "fund" | "deposit" | "withdraw" | null;
  data?: any;
}

interface AppStateContextType {
  // Page tracking
  currentPage: PageType;
  setCurrentPage: (page: PageType) => void;

  // Dialog tracking
  currentDialog: DialogState;
  openDialog: (type: DialogState["type"], data?: any) => void;
  closeDialog: () => void;
  updateDialogData: (data: any) => void;

  // Voice processing state
  isProcessingVoice: boolean;
  setIsProcessingVoice: (processing: boolean) => void;

  // Loading mode for voice processing
  voiceLoadingMode: "loading" | "ignore" | null;
  setVoiceLoadingMode: (mode: "loading" | "ignore" | null) => void;
}

const AppStateContext = createContext<AppStateContextType | undefined>(undefined);

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [currentPage, setCurrentPage] = useState<PageType>("dashboard");
  const [currentDialog, setCurrentDialog] = useState<DialogState>({
    isOpen: false,
    type: null,
    data: undefined,
  });
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const [voiceLoadingMode, setVoiceLoadingMode] = useState<"loading" | "ignore" | null>(null);

  const openDialog = useCallback((type: DialogState["type"], data?: any) => {
    setCurrentDialog({
      isOpen: true,
      type,
      data: data || {},
    });
  }, []);

  const closeDialog = useCallback(() => {
    setCurrentDialog({
      isOpen: false,
      type: null,
      data: undefined,
    });
  }, []);

  const updateDialogData = useCallback((data: any) => {
    setCurrentDialog((prev) => ({
      ...prev,
      data: { ...prev.data, ...data },
    }));
  }, []);

  return (
    <AppStateContext.Provider
      value={{
        currentPage,
        setCurrentPage,
        currentDialog,
        openDialog,
        closeDialog,
        updateDialogData,
        isProcessingVoice,
        setIsProcessingVoice,
        voiceLoadingMode,
        setVoiceLoadingMode,
      }}>
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (context === undefined) {
    throw new Error("useAppState must be used within AppStateProvider");
  }
  return context;
}
