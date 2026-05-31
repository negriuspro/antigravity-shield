"use client";
import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Monitor, Shield, ScrollText,
  Bell, Settings, ChevronLeft, Wifi, Activity
} from "lucide-react";
import clsx from "clsx";

const NAV = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/devices", icon: Monitor, label: "Devices" },
  { href: "/rules", icon: Shield, label: "Rules" },
  { href: "/logs", icon: ScrollText, label: "Query Logs" },
  { href: "/alerts", icon: Bell, label: "Alerts" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className={clsx(
        "flex flex-col border-r border-surface-border bg-surface-card transition-all duration-300",
        collapsed ? "w-16" : "w-56"
      )}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-surface-border">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center">
            <Activity className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <span className="font-semibold text-sm text-white tracking-wide">AG Shield</span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 space-y-1 px-2">
          {NAV.map(({ href, icon: Icon, label }) => {
            const active = pathname === href || pathname.startsWith(href + "/");
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  active
                    ? "bg-brand-600 text-white"
                    : "text-surface-muted hover:text-white hover:bg-surface-border"
                )}
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                {!collapsed && label}
              </Link>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="px-2 pb-4 space-y-1">
          <Link
            href="/settings"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-surface-muted hover:text-white hover:bg-surface-border transition-colors"
          >
            <Settings className="w-4 h-4 flex-shrink-0" />
            {!collapsed && "Settings"}
          </Link>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-surface-muted hover:text-white hover:bg-surface-border transition-colors"
          >
            <ChevronLeft className={clsx("w-4 h-4 flex-shrink-0 transition-transform", collapsed && "rotate-180")} />
            {!collapsed && "Collapse"}
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto bg-surface">
        {/* Top bar */}
        <header className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-surface-border bg-surface/80 backdrop-blur">
          <div className="flex items-center gap-2 text-sm text-surface-muted">
            <Wifi className="w-4 h-4 text-green-400" />
            <span className="text-green-400 font-medium">Shield Active</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse-slow" />
            <span className="text-xs text-surface-muted">Live</span>
          </div>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
