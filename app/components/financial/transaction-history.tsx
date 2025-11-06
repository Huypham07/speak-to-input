"use client";

import React, { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ArrowDownIcon, ArrowUpIcon, ArrowRightIcon } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { fetchWithAuth } from "@/lib/fetch-auth";

interface Transaction {
  id: number;
  user_id: number;
  from_account_id?: number;
  to_account_id?: number;
  transaction_type: "deposit" | "withdraw" | "transfer";
  amount: number;
  currency: string;
  status: string;
  message?: string;
  recipient_account_number?: string;
  recipient_name?: string;
  recipient_bank?: string;
  created_at: string;
  updated_at?: string;
}

interface TransactionHistoryProps {
  accountId?: number;
}

export default function TransactionHistory({ accountId }: TransactionHistoryProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"all" | "in" | "out">("all");

  useEffect(() => {
    fetchTransactions();
  }, [accountId]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetchWithAuth("/api/accounts/transactions");
      if (!response.ok) {
        throw new Error("Không thể tải lịch sử giao dịch");
      }

      const data = await response.json();
      setTransactions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tải lịch sử giao dịch");
    } finally {
      setLoading(false);
    }
  };

  const getFilteredTransactions = () => {
    if (activeTab === "all") {
      return transactions;
    }

    return transactions.filter((txn) => {
      if (activeTab === "in") {
        // Tiền vào: deposit hoặc transfer đến account này
        return (
          txn.transaction_type === "deposit" || (txn.transaction_type === "transfer" && txn.to_account_id === accountId)
        );
      } else {
        // Tiền ra: withdraw hoặc transfer từ account này
        return (
          txn.transaction_type === "withdraw" ||
          (txn.transaction_type === "transfer" && txn.from_account_id === accountId)
        );
      }
    });
  };

  const getTransactionIcon = (type: string) => {
    switch (type) {
      case "deposit":
        return <ArrowDownIcon className="h-4 w-4 text-green-600" />;
      case "withdraw":
        return <ArrowUpIcon className="h-4 w-4 text-red-600" />;
      case "transfer":
        return <ArrowRightIcon className="h-4 w-4 text-blue-600" />;
      default:
        return null;
    }
  };

  const getTransactionColor = (txn: Transaction) => {
    if (txn.transaction_type === "deposit") return "text-green-600";
    if (txn.transaction_type === "withdraw") return "text-red-600";
    if (txn.transaction_type === "transfer") {
      // Nếu transfer từ account này = tiền ra
      if (txn.from_account_id === accountId) return "text-red-600";
      // Nếu transfer đến account này = tiền vào
      if (txn.to_account_id === accountId) return "text-green-600";
    }
    return "text-blue-600";
  };

  const formatAmount = (txn: Transaction) => {
    let prefix = "";
    if (txn.transaction_type === "deposit") prefix = "+";
    else if (txn.transaction_type === "withdraw") prefix = "-";
    else if (txn.transaction_type === "transfer") {
      // Transfer từ account này = tiền ra (-)
      if (txn.from_account_id === accountId) prefix = "-";
      // Transfer đến account này = tiền vào (+)
      else if (txn.to_account_id === accountId) prefix = "+";
      else prefix = "-"; // Default
    }
    return `${prefix}${txn.amount.toLocaleString("vi-VN")} ₫`;
  };

  const getTransactionLabel = (txn: Transaction) => {
    switch (txn.transaction_type) {
      case "deposit":
        return "Nạp tiền";
      case "withdraw":
        return "Rút tiền";
      case "transfer":
        if (txn.from_account_id === accountId) {
          return txn.recipient_name ? `Chuyển đến ${txn.recipient_name}` : "Chuyển tiền";
        } else if (txn.to_account_id === accountId) {
          return "Nhận tiền";
        }
        return "Chuyển tiền";
      default:
        return txn.transaction_type;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("vi-VN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  };

  const renderTransactionList = (txns: Transaction[]) => {
    if (txns.length === 0) {
      return <p className="text-sm text-gray-500 text-center py-4">Chưa có giao dịch nào</p>;
    }

    return (
      <div className="space-y-4">
        {txns.map((txn) => (
          <div key={txn.id} className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0">
            <div className="flex items-center space-x-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                {getTransactionIcon(txn.transaction_type)}
              </div>
              <div>
                <p className="font-medium">{getTransactionLabel(txn)}</p>
                <p className="text-xs text-gray-500">{formatDate(txn.created_at)}</p>
                {txn.message && <p className="text-xs text-gray-400 mt-1">{txn.message}</p>}
              </div>
            </div>
            <div className="text-right">
              <p className={`font-semibold ${getTransactionColor(txn)}`}>{formatAmount(txn)}</p>
              <Badge variant={txn.status === "completed" ? "default" : "secondary"} className="mt-1">
                {txn.status === "completed" ? "Hoàn thành" : txn.status}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Lịch sử giao dịch</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-3 w-24" />
                </div>
              </div>
              <Skeleton className="h-4 w-24" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Lịch sử giao dịch</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-600">{error}</p>
        </CardContent>
      </Card>
    );
  }

  const filteredTransactions = getFilteredTransactions();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Lịch sử giao dịch</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "all" | "in" | "out")}>
          <TabsList className="grid w-full grid-cols-3 mb-4">
            <TabsTrigger value="all">Tất cả</TabsTrigger>
            <TabsTrigger value="in">Tiền vào</TabsTrigger>
            <TabsTrigger value="out">Tiền ra</TabsTrigger>
          </TabsList>

          <TabsContent value="all">{renderTransactionList(filteredTransactions)}</TabsContent>

          <TabsContent value="in">{renderTransactionList(filteredTransactions)}</TabsContent>

          <TabsContent value="out">{renderTransactionList(filteredTransactions)}</TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
