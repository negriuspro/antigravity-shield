"use client";
import useSWR from "swr";
import { Shield, Monitor, BarChart3, TrendingDown } from "lucide-react";
import { StatCard } from "@/components/ui/StatCard";
import { QueriesChart } from "@/components/charts/QueriesChart";
import { fetcher } from "@/lib/api";
import type { DashboardStats } from "@/types";

export default function DashboardPage() {
  const { data, isLoading } = useSWR<DashboardStats>("/dashboard/", fetcher, {
    refreshInterval: 15000,
  });

  if (isLoading || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-surface-muted text-sm mt-1">Real-time network protection overview</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <StatCard
          title="Blocked Today"
          value={data.blocked_today}
          subtitle={`${data.block_rate_today}% block rate`}
          icon={Shield}
          color="red"
        />
        <StatCard
          title="Queries Today"
          value={data.total_queries_today}
          subtitle="DNS queries processed"
          icon={BarChart3}
          color="blue"
        />
        <StatCard
          title="Active Devices"
          value={data.active_clients}
          subtitle={`${data.total_clients} total registered`}
          icon={Monitor}
          color="green"
        />
        <StatCard
          title="Blocked 30d"
          value={data.blocked_30d}
          subtitle={`of ${data.total_queries_30d} total`}
          icon={TrendingDown}
          color="yellow"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 rounded-xl border border-surface-border bg-surface-card p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Queries — Last 24 Hours</h2>
          <QueriesChart data={data.queries_per_hour} />
        </div>

        {/* Top blocked */}
        <div className="rounded-xl border border-surface-border bg-surface-card p-5">
          <h2 className="text-sm font-semibold text-white mb-4">Top Blocked Domains</h2>
          <div className="space-y-2">
            {data.top_blocked_domains.slice(0, 8).map((d, i) => (
              <div key={d.domain} className="flex items-center gap-3">
                <span className="text-xs text-surface-muted w-4">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white truncate font-mono">{d.domain}</p>
                  <div className="mt-1 h-1 bg-surface-border rounded-full overflow-hidden">
                    <div
                      className="h-full bg-red-500 rounded-full"
                      style={{
                        width: `${Math.min(100, (d.count / (data.top_blocked_domains[0]?.count || 1)) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
                <span className="text-xs text-surface-muted">{d.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
