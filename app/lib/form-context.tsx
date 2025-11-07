"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";

interface FormContextType {
  currentForm: {
    type: string | null;
    data: any;
  };
  setCurrentForm: (type: string | null, data: any) => void;
  clearForm: () => void;
}

const FormContext = createContext<FormContextType | undefined>(undefined);

export function FormProvider({ children }: { children: ReactNode }) {
  const [currentForm, setFormState] = useState<{ type: string | null; data: any }>({
    type: null,
    data: {},
  });

  const setCurrentForm = useCallback((type: string | null, data: any) => {
    setFormState({ type, data });
  }, []);

  const clearForm = useCallback(() => {
    setFormState({ type: null, data: {} });
  }, []);

  return <FormContext.Provider value={{ currentForm, setCurrentForm, clearForm }}>{children}</FormContext.Provider>;
}

export function useFormContext() {
  const context = useContext(FormContext);
  if (context === undefined) {
    throw new Error("useFormContext must be used within FormProvider");
  }
  return context;
}
