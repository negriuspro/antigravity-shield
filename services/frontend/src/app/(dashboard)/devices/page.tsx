"use client";
import useSWR from "swr";
import { useState } from "react";
import { Monitor, Wifi, WifiOff, ShieldOff, Shield } from "lucide-react";
import clsx from "clsx";
import { fetcher, api } from "@/lib/api";
import type { Device } from "@/types";
import { formatDistanceToNow } from "date-fns";

const STATUS_ICON = {
  online: <Wifi className="w-3.5 h-3.5 text-green-400" />,
  offline: <WifiOff className="w-3.5 h-3.5 text-slate-500" />,
  unknown: <Wifi className="w-3.5 h-3.5 text-yellow-400" />,
};

export default function DevicesPage() {
  const { data: devices, isLoading, mutate } = useSWR<Device[]>("/devices/", fetcher, { refreshInterval: 30000 });
  const [filter, setFilter] = useState<string>("all");

  const filtered = devices?.filter((d) => filter === "all" || d.status === filter) ?? [];

  const toggleBlock = async (device: Device) => {
    const endpoint = device.is_blocked ? `/devices/${device.id}/unblock` : `/devices/${device.id}/block`;
    await api.post(endpoint);
    mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Devices</h1>
          <p className="text-surface-muted text-sm mt-1">Network inventory and device management</p>
        </div>
        <div className="flex gap-2">
          {["all", "online", "offline"].map((s) => (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className={clsx(
                "px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors",
                filter === s ? "bg-brand-600 text-white" : "bg-surface-border text-surface-muted hover:text-white"
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="rounded-xl border border-surface-border bg-surface-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-border text-xs text-surface-muted uppercase tracking-wider">
                <th className="px-4 py-3 text-left">Device</th>
                <th className="px-4 py-3 text-left">IP / MAC</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Group</th>
                <th className="px-4 py-3 text-left">Last Seen</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border">
              {filtered.map((device) => (
                <tr key={device.id} className="hover:bg-surface-border/30 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Monitor className="w-4 h-4 text-surface-muted" />
                      <div>
                        <p className="text-white font-medium">{device.hostname || "Unknown"}</p>
                        <p className="text-xs text-surface-muted">{device.manufacturer || "—"}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <p className="font-mono text-xs text-white">{device.ip}</p>
                    <p className="font-mono text-xs text-surface-muted">{device.mac}</p>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      {STATUS_ICON[device.status]}
                      <span className={clsx("text-xs capitalize", device.status === "online" ? "text-green-400" : "text-surface-muted")}>
                        {device.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-surface-muted">{device.group_name || "—"}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-surface-muted">
                      {device.last_seen ? formatDistanceToNow(new Date(device.last_seen), { addSuffix: true }) : "Never"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => toggleBlock(device)}
                      className={clsx(
                        "flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium ml-auto transition-colors",
                        device.is_blocked
                          ? "bg-green-500/10 text-green-400 hover:bg-green-500/20"
                          : "bg-red-500/10 text-red-400 hover:bg-red-500/20"
                      )}
                    >
                      {device.is_blocked ? <Shield className="w-3 h-3" /> : <ShieldOff className="w-3 h-3" />}
                      {device.is_blocked ? "Unblock" : "Block"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && (
            <div className="py-16 text-center text-surface-muted text-sm">No devices found</div>
          )}
        </div>
      )}
    </div>
  );
}
