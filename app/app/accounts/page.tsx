"use client";

import { useAuth } from "@/lib/auth-context";
import { useSidebar } from "@/lib/sidebar-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DepositWithdrawForm } from "@/components/financial/deposit-withdraw-form";
import { Wallet, ArrowUpRight, ArrowDownRight, Clock } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";

interface Account {
  id: number;
  account_number: string;
  account_name: string;
  balance: number;
  currency: string;
  account_type: string;
  is_active: boolean;
}

export default function AccountsPage() {
  const { user, isLoading } = useAuth();
  const { isCollapsed } = useSidebar();
  const router = useRouter();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);

  // Lấy token từ localStorage hoặc cookie thông qua useAuth
  const getToken = () => {
    // Ưu tiên lấy từ localStorage
    return localStorage.getItem("access_token");
  };

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const token = getToken();
      if (!token) return;
      const response = await fetch("http://localhost:8000/api/v1/accounts", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setAccounts(data);
        if (data.length > 0 && !selectedAccount) {
          setSelectedAccount(data[0]);
        }
      }
    } catch (error) {
      console.error("Error fetching accounts:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchAccounts();
    }
  }, [user]);

  const handleSuccess = () => {
    // Refresh accounts after successful transaction
    fetchAccounts();
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <main
        className={`transition-all duration-300 px-4 sm:px-6 lg:px-8 py-8 pb-24 md:pb-8 ${
          isCollapsed ? "md:ml-20" : "md:ml-64"
        }`}>
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Header */}
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-foreground">Quản lý tài khoản</h1>
            <p className="text-muted-foreground mt-2">Xem và quản lý các tài khoản của bạn</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Accounts List */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Danh sách tài khoản</h2>

              {loading ? (
                <div className="space-y-3">
                  {[1, 2].map((i) => (
                    <Card key={i}>
                      <CardContent className="pt-6">
                        <Skeleton className="h-24 w-full" />
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : accounts.length === 0 ? (
                <Card>
                  <CardContent className="pt-6 text-center text-muted-foreground">
                    <Wallet className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Chưa có tài khoản nào</p>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-3">
                  {accounts.map((account) => (
                    <Card
                      key={account.id}
                      className={`cursor-pointer transition-all hover:shadow-md ${
                        selectedAccount?.id === account.id ? "ring-2 ring-primary" : ""
                      }`}
                      onClick={() => setSelectedAccount(account)}>
                      <CardHeader>
                        <div className="flex justify-between items-start">
                          <div>
                            <CardTitle className="flex items-center gap-2">
                              <Wallet className="h-5 w-5" />
                              {account.account_name}
                            </CardTitle>
                            <CardDescription className="mt-1">STK: {account.account_number}</CardDescription>
                          </div>
                          <Badge variant={account.is_active ? "default" : "secondary"}>
                            {account.is_active ? "Hoạt động" : "Tạm khóa"}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="flex justify-between items-end">
                          <div>
                            <p className="text-sm text-muted-foreground">Số dư</p>
                            <p className="text-2xl font-bold">
                              {account.balance.toLocaleString("vi-VN")} {account.currency}
                            </p>
                          </div>
                          <Badge variant="outline">{account.account_type}</Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>

            {/* Deposit/Withdraw Form */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Giao dịch</h2>

              {selectedAccount ? (
                <DepositWithdrawForm
                  accountId={selectedAccount.id}
                  currentBalance={selectedAccount.balance}
                  onSuccess={handleSuccess}
                />
              ) : (
                <Card>
                  <CardContent className="pt-6 text-center text-muted-foreground">
                    <p>Chọn một tài khoản để thực hiện giao dịch</p>
                  </CardContent>
                </Card>
              )}

              {/* Recent Transactions (Mock) */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Giao dịch gần đây
                  </CardTitle>
                  <CardDescription>Lịch sử giao dịch của tài khoản</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground text-center py-4">Chưa có giao dịch nào</p>
                  {/* TODO: Implement transaction history */}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
