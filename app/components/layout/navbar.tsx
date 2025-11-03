"use client";

import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { LogOut, Home, Send, FileText, PiggyBank, Mic, Square, Settings, User, Wallet } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSpeech } from "@/lib/speech-context";
import { useSidebar } from "@/lib/sidebar-context";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function Navbar() {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const { isListening, isProcessing, startListening, stopListening } = useSpeech();
  const { isCollapsed, toggleSidebar } = useSidebar();

  if (!user) return null;

  const navItems = [
    { href: "/dashboard", icon: Home, label: "Trang chủ" },
    { href: "/accounts?action=transfer", icon: Send, label: "Chuyển tiền" },
    { href: "/dashboard?tab=bills", icon: FileText, label: "Hóa đơn" },
    { href: "/funds", icon: PiggyBank, label: "Tiết kiệm" },
  ];

  const isActive = (href: string) => pathname === href || pathname.startsWith(href);

  const handleSpeechClick = async () => {
    if (isListening) {
      await stopListening();
    } else {
      await startListening();
    }
  };

  return (
    <>
      {/* Desktop Sidebar - Collapsible */}
      <aside
        className={`hidden md:fixed md:left-0 md:top-0 md:h-screen md:border-r md:border-border md:bg-linear-to-b md:from-slate-50 md:to-white dark:md:from-slate-900 dark:md:to-slate-950 md:backdrop-blur md:flex md:flex-col md:z-50 md:shadow-lg transition-all duration-300 ${
          isCollapsed ? "md:w-20" : "md:w-64"
        }`}>
        {/* Header */}
        <div className="p-6 border-b border-border/50 bg-linear-to-r from-blue-600 to-emerald-600 relative">
          <div className={`flex items-center ${isCollapsed ? "justify-start" : "gap-3"} transition-all duration-300`}>
            {/* Logo - Click to toggle sidebar */}
            <button
              onClick={toggleSidebar}
              className="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-lg flex items-center justify-center ring-2 ring-white/30 shrink-0 hover:bg-white/30 hover:ring-white/50 transition-all hover:scale-110 cursor-pointer"
              title={isCollapsed ? "Mở rộng thanh bên" : "Thu gọn thanh bên"}>
              <span className="text-white font-bold">FF</span>
            </button>

            {/* Text - Click to go home */}
            {!isCollapsed && (
              <Link
                href="/dashboard"
                className="font-bold text-lg text-white whitespace-nowrap overflow-hidden text-ellipsis hover:text-white/90 transition-colors">
                FinFlow
              </Link>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2 overflow-hidden">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center h-12 ${
                isCollapsed ? "justify-start px-3" : "gap-3 px-4"
              } rounded-lg transition-all shadow-sm ${
                isActive(item.href)
                  ? "bg-linear-to-r from-blue-600 to-emerald-600 text-white shadow-md scale-105"
                  : "text-muted-foreground hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-foreground hover:shadow-md hover:scale-102"
              }`}
              title={isCollapsed ? item.label : undefined}>
              <item.icon className="h-5 w-5 shrink-0" />
              {!isCollapsed && (
                <span className="font-medium whitespace-nowrap overflow-hidden text-ellipsis">{item.label}</span>
              )}
            </Link>
          ))}
        </nav>

        {/* Settings & Logout */}
        <div className="p-4 border-t border-border/50 space-y-2 bg-slate-50/50 dark:bg-slate-900/50">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className={`w-full h-12 flex items-center justify-start ${
                  isCollapsed ? "px-3" : "gap-2 px-4"
                } rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-muted-foreground hover:text-foreground`}>
                <Settings className="h-4 w-4 shrink-0" />
                {!isCollapsed && (
                  <span className="font-medium whitespace-nowrap overflow-hidden text-ellipsis">Cài đặt</span>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Cài đặt</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User className="mr-2 h-4 w-4" />
                <span>Tài khoản</span>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                <span>Khác</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Button
            onClick={logout}
            variant="outline"
            className={`w-full h-12 justify-start ${
              isCollapsed ? "px-3" : "gap-2 px-4"
            } bg-white dark:bg-slate-800 hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-600 dark:hover:text-red-400 hover:border-red-300`}
            title={isCollapsed ? "Đăng xuất" : undefined}>
            <LogOut className="h-4 w-4 shrink-0" />
            {!isCollapsed && <span className="whitespace-nowrap overflow-hidden text-ellipsis">Đăng xuất</span>}
          </Button>
        </div>
      </aside>

      {/* Desktop Floating Voice Command Button - Fixed Bottom Right */}
      <button
        onClick={handleSpeechClick}
        disabled={isProcessing}
        className="hidden md:flex fixed bottom-6 right-6 z-50 items-center justify-center w-16 h-16 rounded-full bg-linear-to-r from-orange-500 to-pink-500 text-white shadow-2xl hover:shadow-[0_10px_40px_rgba(251,113,133,0.4)] transition-all hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed">
        {isListening ? (
          <>
            <Square className="h-7 w-7" />
            <span className="absolute inset-0 rounded-full animate-pulse bg-red-500/30 ring-4 ring-red-400/50" />
          </>
        ) : (
          <Mic className="h-7 w-7" />
        )}
      </button>

      {/* Mobile Bottom Navigation with Convex Speech Button */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 border-t-2 border-border/70 bg-linear-to-t from-slate-50 to-white dark:from-slate-900 dark:to-slate-950 backdrop-blur supports-backdrop-filter:bg-background/80 shadow-[0_-8px_24px_rgba(0,0,0,0.15)] dark:shadow-[0_-8px_24px_rgba(0,0,0,0.5)]">
        <div className="relative">
          {/* Convex bump for speech button - centered between 5 items */}
          <div
            className="absolute left-1/2 -translate-x-1/2 -top-8 w-24 h-16"
            style={{
              clipPath: "ellipse(50% 100% at 50% 100%)",
            }}>
            <div className="w-full h-full bg-white rounded-t-[100%]" />
          </div>

          {/* Navigation items - 5 items with center one being speech button */}
          <div className="grid grid-cols-5 items-center h-16 px-2 bg-white">
            {/* First two nav items */}
            {navItems.slice(0, 2).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center gap-1 py-2 px-1 rounded-lg transition-all ${
                  isActive(item.href)
                    ? "text-blue-600 scale-110"
                    : "text-muted-foreground hover:text-foreground hover:scale-105"
                }`}>
                <item.icon className="h-6 w-6 shrink-0" />
                <span className="text-xs font-medium whitespace-nowrap overflow-hidden text-ellipsis max-w-full px-1">
                  {item.label}
                </span>
              </Link>
            ))}

            {/* Center - Speech Button */}
            <div className="flex items-center justify-center">
              <button
                onClick={handleSpeechClick}
                disabled={isProcessing}
                className="relative -top-6 flex items-center justify-center w-16 h-16 rounded-full bg-linear-to-r from-orange-500 to-pink-500 text-white shadow-2xl hover:shadow-[0_8px_30px_rgba(251,113,133,0.5)] transition-all hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed ring-4 ring-white dark:ring-slate-950">
                {isListening ? (
                  <>
                    <Square className="h-7 w-7" />
                    <span className="absolute inset-0 rounded-full animate-pulse bg-red-500/30 ring-2 ring-red-400" />
                  </>
                ) : (
                  <Mic className="h-7 w-7" />
                )}
              </button>
            </div>

            {/* Last two nav items */}
            {navItems.slice(2, 4).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center gap-1 py-2 px-1 rounded-lg transition-all ${
                  isActive(item.href)
                    ? "text-blue-600 scale-110"
                    : "text-muted-foreground hover:text-foreground hover:scale-105"
                }`}>
                <item.icon className="h-6 w-6 shrink-0" />
                <span className="text-xs font-medium whitespace-nowrap overflow-hidden text-ellipsis max-w-full px-1">
                  {item.label}
                </span>
              </Link>
            ))}
          </div>
        </div>
      </nav>
    </>
  );
}
