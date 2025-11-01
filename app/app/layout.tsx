import type React from "react";
import type { Metadata } from "next";

import { Analytics } from "@vercel/analytics/next";
import { AuthProvider } from "@/lib/auth-context";
import { FinancialProvider } from "@/lib/financial-context";
import { SpeechProvider } from "@/lib/speech-context";
import { SidebarProvider } from "@/lib/sidebar-context";
import { Toaster } from "@/components/ui/toaster";
import "./globals.css";

import {
  Geist,
  Geist_Mono,
  Geist as V0_Font_Geist,
  Geist_Mono as V0_Font_Geist_Mono,
  Source_Serif_4 as V0_Font_Source_Serif_4,
} from "next/font/google";

// Initialize fonts
const _geist = V0_Font_Geist({
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
});
const _geistMono = V0_Font_Geist_Mono({
  subsets: ["latin"],
  weight: ["100", "200", "300", "400", "500", "600", "700", "800", "900"],
});
const _sourceSerif_4 = V0_Font_Source_Serif_4({
  subsets: ["latin"],
  weight: ["200", "300", "400", "500", "600", "700", "800", "900"],
});

const geist = Geist({ subsets: ["latin"] });
const geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FinFlow - Smart Financial Management",
  description: "Manage your finances with voice commands and modern interface",
  generator: "v0.app",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geist.className} antialiased`}>
        <AuthProvider>
          <SidebarProvider>
            <FinancialProvider>
              <SpeechProvider>{children}</SpeechProvider>
            </FinancialProvider>
          </SidebarProvider>
        </AuthProvider>
        <Toaster />
        <Analytics />
      </body>
    </html>
  );
}
