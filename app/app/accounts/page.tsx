"use client";

import { useAuth } from "@/lib/auth-context";
import { useSidebar } from "@/lib/sidebar-context";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { Navbar } from "@/components/layout/navbar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { DepositWithdrawForm } from "@/components/financial/deposit-withdraw-form";
import { TransferForm } from "@/components/financial/transfer-form";
import TransactionHistory from "@/components/financial/transaction-history";
import { Wallet, ArrowUpRight, ArrowDownRight, Clock, ChevronLeft, Users } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface Account {
  id: number;
  account_number: string;
  account_name: string;
  balance: number;
  currency: string;
  account_type: string;
  is_active: boolean;
}

interface OtherUserAccount {
  id: number;
  account_number: string;
  account_name: string;
  balance: number;
  currency: string;
  account_type: string;
  is_active: boolean;
  user_id: number;
  user_full_name: string;
  user_username: string;
}

function AccountsPageContent() {
  const { user, isLoading } = useAuth();
  const { isCollapsed } = useSidebar();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [transactionKey, setTransactionKey] = useState(0);
  const [activeTab, setActiveTab] = useState<string>("deposit");
  const [otherAccounts, setOtherAccounts] = useState<OtherUserAccount[]>([]);
  const [loadingOtherAccounts, setLoadingOtherAccounts] = useState(false);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  // Check for action query parameter
  useEffect(() => {
    const action = searchParams.get("action");
    if (action === "transfer") {
      setActiveTab("transfer");
    } else if (action === "deposit") {
      setActiveTab("deposit");
    }
  }, [searchParams]);

  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/accounts");
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
      fetchOtherAccounts();
    }
  }, [user]);

  const fetchOtherAccounts = async () => {
    setLoadingOtherAccounts(true);
    try {
      const response = await fetch("/api/accounts/others");
      if (response.ok) {
        const data = await response.json();
        setOtherAccounts(data);
      }
    } catch (error) {
      console.error("Error fetching other users accounts:", error);
    } finally {
      setLoadingOtherAccounts(false);
    }
  };

  const handleSelectOtherAccount = (account: OtherUserAccount) => {
    // Switch to transfer tab and pass account info via URL params
    setActiveTab("transfer");
    router.push(
      `/accounts?action=transfer&accountNumber=${encodeURIComponent(account.account_number)}&recipientName=${encodeURIComponent(account.user_full_name)}`,
      { scroll: false }
    );
  };

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    // Update URL without reload
    const newUrl = value === "deposit" ? "/accounts?action=deposit" : `/accounts?action=${value}`;
    router.push(newUrl, { scroll: false });
  };

  const handleSuccess = () => {
    // Refresh accounts and transaction history after successful transaction
    fetchAccounts();
    setTransactionKey((prev) => prev + 1); // Force TransactionHistory to re-fetch
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
          {/* Header with Back Button */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push("/dashboard")}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
              title="Quay lại Dashboard">
              <ChevronLeft className="h-5 w-5" />
            </button>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-foreground">Quản lý tài khoản</h1>
              <p className="text-muted-foreground mt-2">Xem và quản lý các tài khoản của bạn</p>
            </div>
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
                          <Badge variant={account.is_active ? "default" : "secondary"} className="text-xs">
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
                          {/* <Badge variant="outline">{account.account_type}</Badge> */}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              {/* Other Users Accounts List */}
              {otherAccounts.length > 0 && (
                <div className="mt-8 space-y-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    Tài khoản người dùng khác
                  </h2>
                  <div className="space-y-3">
                    {loadingOtherAccounts ? (
                      <div className="space-y-3">
                        {[1, 2].map((i) => (
                          <Card key={i}>
                            <CardContent className="pt-6">
                              <Skeleton className="h-24 w-full" />
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    ) : (
                      otherAccounts.map((account) => (
                        <Card
                          key={account.id}
                          className="cursor-pointer transition-all hover:shadow-md border-muted"
                          onClick={() => handleSelectOtherAccount(account)}>
                          <CardHeader>
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <CardTitle className="flex items-center gap-2 text-base">
                                  <Users className="h-4 w-4" />
                                  {account.user_full_name}
                                </CardTitle>
                                <CardDescription className="mt-1">
                                  @{account.user_username} • {account.account_name}
                                </CardDescription>
                                <CardDescription className="mt-1 text-xs">
                                  STK: {account.account_number}
                                </CardDescription>
                              </div>
                              <Badge variant={account.is_active ? "default" : "secondary"} className="text-xs">
                                {account.is_active ? "Hoạt động" : "Tạm khóa"}
                              </Badge>
                            </div>
                          </CardHeader>
                          <CardContent>
                            <div className="flex justify-between items-end">
                              <div>
                                <p className="text-sm text-muted-foreground">Số dư</p>
                                <p className="text-xl font-bold">
                                  {account.balance.toLocaleString("vi-VN")} {account.currency}
                                </p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Deposit/Withdraw/Transfer Forms */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold">Giao dịch</h2>

              {selectedAccount ? (
                <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
                  <TabsList className="grid w-full grid-cols-2 bg-linear-to-r from-blue-600 to-emerald-600 p-1">
                    <TabsTrigger
                      value="deposit"
                      className="data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=inactive]:text-white">
                      Nạp tiền
                    </TabsTrigger>
                    <TabsTrigger
                      value="transfer"
                      className="data-[state=active]:bg-white data-[state=active]:text-blue-600 data-[state=inactive]:text-white">
                      Chuyển tiền
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="deposit">
                    <DepositWithdrawForm
                      accountId={selectedAccount.id}
                      currentBalance={selectedAccount.balance}
                      onSuccess={handleSuccess}
                    />
                  </TabsContent>

                  <TabsContent value="transfer">
                    <TransferForm
                      accountId={selectedAccount.id}
                      currentBalance={selectedAccount.balance}
                      onSuccess={handleSuccess}
                    />
                  </TabsContent>
                </Tabs>
              ) : (
                <Card>
                  <CardContent className="pt-6 text-center text-muted-foreground">
                    <p>Chọn một tài khoản để thực hiện giao dịch</p>
                  </CardContent>
                </Card>
              )}

              {/* Transaction History */}
              <TransactionHistory key={transactionKey} accountId={selectedAccount?.id} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function AccountsPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-background flex items-center justify-center">
          <Skeleton className="h-96 w-full max-w-6xl" />
        </div>
      }>
      <AccountsPageContent />
    </Suspense>
  );
}
