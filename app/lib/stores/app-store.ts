import { create } from "zustand";
import { devtools } from "zustand/middleware";

export type PageType = "dashboard" | "accounts" | "bills" | "funds" | "transfers";

export interface DialogState {
  isOpen: boolean;
  type: "transfer" | "bill" | "fund" | "deposit" | "withdraw" | null;
  data?: any;
}

interface AppState {
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

  // Voice loading mode
  voiceLoadingMode: "loading" | "ignore" | null;
  setVoiceLoadingMode: (mode: "loading" | "ignore" | null) => void;

  // Voice recording state
  isRecording: boolean;
  setIsRecording: (recording: boolean) => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial state
      currentPage: "dashboard",
      currentDialog: {
        isOpen: false,
        type: null,
        data: undefined,
      },
      isProcessingVoice: false,
      voiceLoadingMode: "loading",
      isRecording: false,

      // Actions
      setCurrentPage: (page) => set({ currentPage: page }, false, "setCurrentPage"),

      openDialog: (type, data) =>
        set(
          {
            currentDialog: {
              isOpen: true,
              type,
              data: data || {},
            },
          },
          false,
          "openDialog"
        ),

      closeDialog: () =>
        set(
          {
            currentDialog: {
              isOpen: false,
              type: null,
              data: undefined,
            },
          },
          false,
          "closeDialog"
        ),

      updateDialogData: (data) =>
        set(
          (state) => ({
            currentDialog: {
              ...state.currentDialog,
              data: { ...state.currentDialog.data, ...data },
            },
          }),
          false,
          "updateDialogData"
        ),

      setIsProcessingVoice: (processing) => set({ isProcessingVoice: processing }, false, "setIsProcessingVoice"),

      setVoiceLoadingMode: (mode) => set({ voiceLoadingMode: mode }, false, "setVoiceLoadingMode"),

      setIsRecording: (recording) => set({ isRecording: recording }, false, "setIsRecording"),
    }),
    { name: "AppStore" }
  )
);
