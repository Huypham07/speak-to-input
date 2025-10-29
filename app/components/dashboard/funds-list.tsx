"use client";

import { useFinancial } from "@/lib/financial-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PiggyBank } from "lucide-react";

export function FundsList() {
  const { funds } = useFinancial();

  const getPriorityText = (priority: string) => {
    switch (priority) {
      case "high":
        return "Cao";
      case "medium":
        return "Trung bình";
      case "low":
        return "Thấp";
      default:
        return priority;
    }
  };

  if (funds.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Quỹ tiết kiệm</CardTitle>
          <CardDescription>Mục tiêu và tiến độ tiết kiệm</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <PiggyBank className="h-12 w-12 text-muted-foreground mx-auto mb-2 opacity-50" />
            <p className="text-muted-foreground">Chưa có quỹ tiết kiệm nào</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quỹ tiết kiệm</CardTitle>
        <CardDescription>Mục tiêu và tiến độ tiết kiệm</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {funds.slice(0, 5).map((fund) => {
            const progress = (fund.currentAmount / fund.targetAmount) * 100;
            return (
              <div key={fund.id} className="p-3 border border-border rounded-lg hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center shrink-0">
                      <PiggyBank className="h-4 w-4 text-emerald-600" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium truncate">{fund.name}</p>
                      <p className="text-xs text-muted-foreground">{fund.category}</p>
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={`text-xs shrink-0 ml-2 ${
                      fund.priority === "high"
                        ? "bg-red-50 text-red-700 border-red-200 dark:bg-red-950 dark:text-red-400"
                        : fund.priority === "medium"
                        ? "bg-yellow-50 text-yellow-700 border-yellow-200 dark:bg-yellow-950 dark:text-yellow-400"
                        : "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950 dark:text-blue-400"
                    }`}>
                    {getPriorityText(fund.priority)}
                  </Badge>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">
                      {fund.currentAmount.toLocaleString("vi-VN")} đ / {fund.targetAmount.toLocaleString("vi-VN")} đ
                    </span>
                    <span className="font-medium">{Math.round(progress)}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div
                      className="bg-linear-to-r from-emerald-500 to-emerald-600 h-2 rounded-full transition-all"
                      style={{ width: `${Math.min(progress, 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
