"use client";

import { useAuth } from "@/lib/auth-context";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, Wallet, ChevronRight } from "lucide-react";
import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouter } from "next/navigation";

interface Account {
  id: number;
  account_number: string;
  account_name: string;
  balance: number;
  currency: string;
  account_type: string;
  is_active: boolean;
}

export function BalanceCard() {
  const { user } = useAuth();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const response = await fetch("/api/accounts");

        if (response.ok) {
          const data = await response.json();
          setAccounts(data);
        }
      } catch (error) {
        console.error("Error fetching accounts:", error);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      fetchAccounts();
    }
  }, [user]);

  if (!user) return null;

  const totalBalance = accounts.reduce((sum, acc) => sum + acc.balance, 0);

  return (
    <Card
      className="bg-linear-to-br from-blue-600 to-emerald-600 border-0 text-white cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => router.push("/accounts")}>
      <CardContent className="pt-6">
        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <p className="text-blue-100 text-sm">Số dư tổng</p>
              {loading ? (
                <Skeleton className="h-10 w-48 mt-2 bg-white/20" />
              ) : (
                <div className="flex items-center gap-2 mt-2">
                  <p className="text-4xl font-bold">{totalBalance.toLocaleString("vi-VN")} đ</p>
                  <ChevronRight className="h-6 w-6 text-blue-100" />
                </div>
              )}
            </div>
            <TrendingUp className="h-8 w-8 text-blue-100" />
          </div>

          {/* Accounts List */}
          {!loading && accounts.length > 0 && (
            <div className="pt-4 border-t border-white/20 space-y-2">
              {accounts.map((account) => (
                <div key={account.id} className="flex justify-between items-center text-sm">
                  <div className="flex items-center gap-2">
                    <Wallet className="h-4 w-4 text-blue-100" />
                    <span className="text-blue-100">{account.account_name}</span>
                  </div>
                  <span className="font-semibold">{account.balance.toLocaleString("vi-VN")} đ</span>
                </div>
              ))}
            </div>
          )}

          <div className="pt-4 border-t border-white/20">
            <p className="text-xs text-blue-100">
              Trạng thái tài khoản: {user.is_active ? "Hoạt động" : "Không hoạt động"}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
