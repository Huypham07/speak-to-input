import { create } from "zustand";
import { devtools } from "zustand/middleware";

interface FormState {
  // Current form state
  type: string | null;
  data: any;
  isDialogOpen: boolean;

  // Actions
  setCurrentForm: (type: string | null, data: any, isDialogOpen?: boolean) => void;
  updateFormData: (data: any) => void;
  clearForm: () => void;

  // Get current form for voice context
  getCurrentFormContext: () => {
    type: string | null;
    data: any;
    isDialogOpen: boolean;
  };
}

export const useFormStore = create<FormState>()(
  devtools(
    (set, get) => ({
      // Initial state
      type: null,
      data: {},
      isDialogOpen: false,

      // Actions
      setCurrentForm: (type, data, isDialogOpen = false) => set({ type, data, isDialogOpen }, false, "setCurrentForm"),

      updateFormData: (newData) =>
        set(
          (state) => ({
            data: { ...state.data, ...newData },
          }),
          false,
          "updateFormData"
        ),

      clearForm: () =>
        set(
          {
            type: null,
            data: {},
            isDialogOpen: false,
          },
          false,
          "clearForm"
        ),

      getCurrentFormContext: () => {
        const state = get();
        return {
          type: state.type,
          data: state.data,
          isDialogOpen: state.isDialogOpen,
        };
      },
    }),
    { name: "FormStore" }
  )
);
