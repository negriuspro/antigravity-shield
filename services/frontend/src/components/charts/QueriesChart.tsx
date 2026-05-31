"use client";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend
} from "recharts";
import { format, parseISO } from "date-fns";

interface Props {
  data: { hour: string; total: number; blocked: number }[];
}

export function QueriesChart({ data }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    label: format(parseISO(d.hour), "HH:mm"),
    allowed: d.total - d.blocked,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={formatted} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="gradAllowed" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gradBlocked" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2740" />
        <XAxis dataKey="label" tick={{ fill: "#8892a4", fontSize: 11 }} />
        <YAxis tick={{ fill: "#8892a4", fontSize: 11 }} />
        <Tooltip
          contentStyle={{ background: "#161b2c", border: "1px solid #1e2740", borderRadius: 8 }}
          labelStyle={{ color: "#e2e8f0" }}
        />
        <Legend wrapperStyle={{ color: "#8892a4", fontSize: 12 }} />
        <Area type="monotone" dataKey="allowed" name="Allowed" stroke="#3b82f6" fill="url(#gradAllowed)" strokeWidth={2} />
        <Area type="monotone" dataKey="blocked" name="Blocked" stroke="#ef4444" fill="url(#gradBlocked)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
