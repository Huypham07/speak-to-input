"use client";

import { useAuth } from "@/lib/auth-context";
import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp } from "lucide-react";

export function BalanceCard() {
  const { user } = useAuth();

  if (!user) return null;

  // TODO: Fetch account balance from backend
  const balance = 0;

  return (
    <Card className="bg-linear-to-br from-blue-600 to-emerald-600 border-0 text-white">
      <CardContent className="pt-6">
        <div className="space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-blue-100 text-sm">Số dư tổng</p>
              <p className="text-4xl font-bold mt-2">{balance.toLocaleString("vi-VN")} đ</p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-100" />
          </div>
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
