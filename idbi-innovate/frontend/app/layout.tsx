import "./globals.css";
import type { Metadata } from "next";
import Link from "next/link";
import { Landmark, LayoutDashboard, CreditCard, ShieldCheck } from "lucide-react";

export const metadata: Metadata = {
  title: "MSME Financial Health Card — IDBI Innovate 2026",
  description:
    "Alternate-data credit decisioning for New-to-Credit / New-to-Bank MSMEs.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand text-white">
                <Landmark size={18} />
              </div>
              <div>
                <div className="text-sm font-semibold leading-tight">
                  MSME Financial Health Card
                </div>
                <div className="text-xs text-slate-500 leading-tight">
                  IDBI Innovate 2026 · Alternate-data credit decisioning
                </div>
              </div>
            </div>
            <nav className="flex items-center gap-1">
              <Link href="/" className="btn">
                <CreditCard size={16} /> Underwriter Cockpit
              </Link>
              <Link href="/portfolio" className="btn">
                <LayoutDashboard size={16} /> Portfolio Impact
              </Link>
              <Link href="/governance" className="btn">
                <ShieldCheck size={16} /> Governance
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
        <footer className="mx-auto max-w-7xl px-4 py-6 text-xs text-slate-400">
          Decision-support prototype · synthetic data · final credit decision rests with the
          human underwriter.
        </footer>
      </body>
    </html>
  );
}
