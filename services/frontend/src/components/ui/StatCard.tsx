"use client";
import clsx from "clsx";
import { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: "blue" | "red" | "green" | "yellow";
  trend?: number;
}

const colors = {
  blue: "text-blue-400 bg-blue-400/10",
  red: "text-red-400 bg-red-400/10",
  green: "text-green-400 bg-green-400/10",
  yellow: "text-yellow-400 bg-yellow-400/10",
};

export function StatCard({ title, value, subtitle, icon: Icon, color = "blue", trend }: Props) {
  return (
    <div className="rounded-xl border border-surface-border bg-surface-card p-5 flex items-start gap-4 animate-fade-in">
      <div className={clsx("p-2.5 rounded-lg", colors[color])}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-surface-muted uppercase tracking-wider font-medium">{title}</p>
        <p className="text-2xl font-bold text-white mt-1">{value.toLocaleString()}</p>
        {subtitle && <p className="text-xs text-surface-muted mt-0.5">{subtitle}</p>}
      </div>
      {trend !== undefined && (
        <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", trend >= 0 ? "text-red-400 bg-red-400/10" : "text-green-400 bg-green-400/10")}>
          {trend >= 0 ? "+" : ""}{trend}%
        </span>
      )}
    </div>
  );
}
