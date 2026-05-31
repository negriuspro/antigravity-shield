"use client";
import useSWR from "swr";
import { Bell, CheckCircle, AlertTriangle, AlertOctagon, Info } from "lucide-react";
import clsx from "clsx";
import { fetcher, api } from "@/lib/api";
import type { AlertEvent } from "@/types";
import { formatDistanceToNow } from "date-fns";

const SEVERITY = {
  info: { icon: Info, cls: "text-blue-400 bg-blue-400/10" },
  warning: { icon: AlertTriangle, cls: "text-yellow-400 bg-yellow-400/10" },
  critical: { icon: AlertOctagon, cls: "text-red-400 bg-red-400/10" },
};

export default function AlertsPage() {
  const { data: alerts, isLoading, mutate } = useSWR<AlertEvent[]>("/alerts/?resolved=false", fetcher, { refreshInterval: 30000 });

  const resolve = async (id: number) => {
    await api.post(`/alerts/${id}/resolve`);
    mutate();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Alerts</h1>
        <p className="text-surface-muted text-sm mt-1">Active system notifications</p>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : alerts?.length === 0 ? (
        <div className="rounded-xl border border-surface-border bg-surface-card p-16 text-center">
          <Bell className="w-10 h-10 text-surface-muted mx-auto mb-3" />
          <p className="text-surface-muted text-sm">No active alerts</p>
        </div>
      ) : (
        <div className="space-y-3">
          {(alerts ?? []).map((alert) => {
            const { icon: Icon, cls } = SEVERITY[alert.severity];
            return (
              <div key={alert.id} className="rounded-xl border border-surface-border bg-surface-card p-4 flex items-start gap-4 animate-fade-in">
                <div className={clsx("p-2 rounded-lg flex-shrink-0", cls)}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-white">{alert.title}</p>
                    <span className={clsx("text-xs px-2 py-0.5 rounded-full capitalize font-medium", cls)}>{alert.severity}</span>
                  </div>
                  <p className="text-xs text-surface-muted mt-1">{alert.message}</p>
                  <p className="text-xs text-surface-muted mt-1">
                    {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                    {alert.source && ` · ${alert.source}`}
                  </p>
                </div>
                <button
                  onClick={() => resolve(alert.id)}
                  className="flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium text-green-400 bg-green-400/10 hover:bg-green-400/20 transition-colors flex-shrink-0"
                >
                  <CheckCircle className="w-3 h-3" />
                  Resolve
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
