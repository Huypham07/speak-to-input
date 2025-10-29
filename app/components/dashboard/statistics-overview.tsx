"use client";

import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, TrendingDown, DollarSign, Calendar } from "lucide-react";
import { useFinancial } from "@/lib/financial-context";

export function StatisticsOverview() {
  const { transfers, bills, funds } = useFinancial();

  // Calculate statistics
  const totalTransfers = transfers.reduce((sum, t) => sum + t.amount, 0);
  const pendingBills = bills.filter((b) => b.status === "pending");
  const totalPendingBills = pendingBills.reduce((sum, b) => sum + b.amount, 0);
  const totalFunds = funds.reduce((sum, f) => sum + f.currentAmount, 0);
  const totalFundTargets = funds.reduce((sum, f) => sum + f.targetAmount, 0);
  const savingsProgress = totalFundTargets > 0 ? (totalFunds / totalFundTargets) * 100 : 0;

  const stats = [
    {
      title: "Tổng đã chuyển",
      value: `${totalTransfers.toLocaleString("vi-VN")} đ`,
      icon: TrendingDown,
      color: "text-orange-600",
      bgColor: "bg-orange-50 dark:bg-orange-950/20",
      description: `${transfers.length} giao dịch`,
    },
    {
      title: "Hóa đơn chưa thanh toán",
      value: `${totalPendingBills.toLocaleString("vi-VN")} đ`,
      icon: Calendar,
      color: "text-red-600",
      bgColor: "bg-red-50 dark:bg-red-950/20",
      description: `${pendingBills.length} hóa đơn`,
    },
    {
      title: "Tiết kiệm hiện tại",
      value: `${totalFunds.toLocaleString("vi-VN")} đ`,
      icon: DollarSign,
      color: "text-green-600",
      bgColor: "bg-green-50 dark:bg-green-950/20",
      description: `${funds.length} quỹ tiết kiệm`,
    },
    {
      title: "Tiến độ tiết kiệm",
      value: `${savingsProgress.toFixed(1)}%`,
      icon: TrendingUp,
      color: "text-blue-600",
      bgColor: "bg-blue-50 dark:bg-blue-950/20",
      description: `Mục tiêu ${totalFundTargets.toLocaleString("vi-VN")} đ`,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <Card key={index} className="overflow-hidden hover:shadow-xl transition-all hover:scale-105">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-muted-foreground mb-1">{stat.title}</p>
                <h3 className="text-2xl font-bold text-foreground mb-1">{stat.value}</h3>
                <p className="text-xs text-muted-foreground">{stat.description}</p>
              </div>
              <div className={`${stat.bgColor} ${stat.color} p-3 rounded-lg`}>
                <stat.icon className="h-6 w-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
