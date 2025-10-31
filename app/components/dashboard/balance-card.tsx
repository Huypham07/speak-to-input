"use client";

import { useAuth } from "@/lib/auth-context";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, Wallet } from "lucide-react";
import { useEffect, useState } from "react";
import { Skeleton } from "@/components/ui/skeleton";

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
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await fetch("http://localhost:8000/api/v1/accounts", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

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
    <Card className="bg-linear-to-br from-blue-600 to-emerald-600 border-0 text-white">
      <CardContent className="pt-6">
        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-blue-100 text-sm">Số dư tổng</p>
              {loading ? (
                <Skeleton className="h-10 w-48 mt-2 bg-white/20" />
              ) : (
                <p className="text-4xl font-bold mt-2">{totalBalance.toLocaleString("vi-VN")} đ</p>
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
