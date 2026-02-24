import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI IDE — Milli Yapay Zeka",
  description: "LangGraph + AI Agent + GitHub API ile Akıllı Kodlama Ortamı",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr" suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
