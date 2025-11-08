"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

interface FormContextType {
  currentForm: {
    type: string | null;
    data: any;
    isDialogOpen?: boolean; // Track if form is in a dialog
  };
  setCurrentForm: (type: string | null, data: any, isDialogOpen?: boolean) => void;
  updateFormData: (data: any) => void;
  clearForm: () => void;
}

const FormContext = createContext<FormContextType | undefined>(undefined);

export function FormProvider({ children }: { children: ReactNode }) {
  const [currentForm, setFormState] = useState<{ type: string | null; data: any; isDialogOpen?: boolean }>({
    type: null,
    data: {},
    isDialogOpen: false,
  });

  const setCurrentForm = useCallback((type: string | null, data: any, isDialogOpen = false) => {
    setFormState({ type, data, isDialogOpen });
  }, []);

  const updateFormData = useCallback((data: any) => {
    setFormState((prev) => ({
      ...prev,
      data: { ...prev.data, ...data },
    }));
  }, []);

  const clearForm = useCallback(() => {
    setFormState({ type: null, data: {}, isDialogOpen: false });
  }, []);

  return (
    <FormContext.Provider value={{ currentForm, setCurrentForm, updateFormData, clearForm }}>
      {children}
    </FormContext.Provider>
  );
}

export function useFormContext() {
  const context = useContext(FormContext);
  if (context === undefined) {
    throw new Error("useFormContext must be used within FormProvider");
  }
  return context;
}
