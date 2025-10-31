"use client";

import { useRouter } from "next/navigation";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-blue-50 to-emerald-50 dark:from-slate-900 dark:to-slate-800 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold bg-linear-to-r from-blue-600 to-emerald-600 bg-clip-text text-transparent">
            FinFlow
          </h1>
          <p className="text-muted-foreground mt-2">Smart Financial Management</p>
        </div>
        <LoginForm onSuccess={() => router.push("/dashboard")} />
      </div>
    </div>
  );
}
