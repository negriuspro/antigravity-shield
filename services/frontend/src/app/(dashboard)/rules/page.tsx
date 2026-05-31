"use client";
import useSWR from "swr";
import { useState } from "react";
import { Shield, Plus, Trash2, ToggleLeft, ToggleRight } from "lucide-react";
import clsx from "clsx";
import { fetcher, api } from "@/lib/api";
import type { Rule } from "@/types";

const ACTION_STYLE = {
  block: "text-red-400 bg-red-400/10",
  allow: "text-green-400 bg-green-400/10",
  redirect: "text-yellow-400 bg-yellow-400/10",
};

export default function RulesPage() {
  const { data: rules, isLoading, mutate } = useSWR<Rule[]>("/rules/", fetcher);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", pattern: "", action: "block", rule_type: "domain" });

  const createRule = async () => {
    await api.post("/rules/", form);
    setShowForm(false);
    setForm({ name: "", pattern: "", action: "block", rule_type: "domain" });
    mutate();
  };

  const toggleRule = async (rule: Rule) => {
    await api.patch(`/rules/${rule.id}`, { enabled: !rule.enabled });
    mutate();
  };

  const deleteRule = async (rule: Rule) => {
    if (!confirm(`Delete rule "${rule.name}"?`)) return;
    await api.delete(`/rules/${rule.id}`);
    mutate();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Rules</h1>
          <p className="text-surface-muted text-sm mt-1">Custom block and allow rules</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Rule
        </button>
      </div>

      {showForm && (
        <div className="rounded-xl border border-surface-border bg-surface-card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-white">New Rule</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <input
              placeholder="Rule name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white placeholder:text-surface-muted focus:outline-none focus:border-brand-500"
            />
            <input
              placeholder="Pattern (e.g. ads.example.com)"
              value={form.pattern}
              onChange={(e) => setForm({ ...form, pattern: e.target.value })}
              className="bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white placeholder:text-surface-muted font-mono focus:outline-none focus:border-brand-500"
            />
            <select
              value={form.action}
              onChange={(e) => setForm({ ...form, action: e.target.value })}
              className="bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
            >
              <option value="block">Block</option>
              <option value="allow">Allow</option>
            </select>
            <select
              value={form.rule_type}
              onChange={(e) => setForm({ ...form, rule_type: e.target.value })}
              className="bg-surface border border-surface-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-500"
            >
              <option value="domain">Domain</option>
              <option value="wildcard">Wildcard</option>
              <option value="regex">Regex</option>
            </select>
          </div>
          <div className="flex gap-2">
            <button onClick={createRule} className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium">Save</button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 rounded-lg bg-surface-border text-surface-muted text-sm hover:text-white">Cancel</button>
          </div>
        </div>
      )}

      <div className="rounded-xl border border-surface-border bg-surface-card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-border text-xs text-surface-muted uppercase tracking-wider">
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Pattern</th>
              <th className="px-4 py-3 text-left">Action</th>
              <th className="px-4 py-3 text-left">Hits</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {(rules ?? []).map((rule) => (
              <tr key={rule.id} className={clsx("hover:bg-surface-border/30 transition-colors", !rule.enabled && "opacity-50")}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Shield className="w-3.5 h-3.5 text-surface-muted" />
                    <span className="text-white font-medium">{rule.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <code className="text-xs text-brand-400 bg-brand-400/10 px-2 py-0.5 rounded">{rule.pattern}</code>
                </td>
                <td className="px-4 py-3">
                  <span className={clsx("text-xs px-2 py-0.5 rounded-full font-medium capitalize", ACTION_STYLE[rule.action])}>
                    {rule.action}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-surface-muted">{rule.hit_count.toLocaleString()}</span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => toggleRule(rule)} className="text-surface-muted hover:text-white transition-colors">
                      {rule.enabled ? <ToggleRight className="w-4 h-4 text-green-400" /> : <ToggleLeft className="w-4 h-4" />}
                    </button>
                    <button onClick={() => deleteRule(rule)} className="text-surface-muted hover:text-red-400 transition-colors">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && (
          <div className="py-16 flex justify-center">
            <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>
    </div>
  );
}
