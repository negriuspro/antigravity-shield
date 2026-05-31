"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, Eye, EyeOff } from "lucide-react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const login = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const form = new FormData();
      form.append("username", username);
      form.append("password", password);
      const { data } = await api.post("/auth/token", form, { headers: { "Content-Type": "multipart/form-data" } });
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      router.push("/dashboard");
    } catch {
      setError("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 rounded-2xl bg-brand-600/20 border border-brand-600/30">
            <Activity className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="text-2xl font-bold text-white">AntiGravity Shield</h1>
          <p className="text-surface-muted text-sm">Network Protection Platform</p>
        </div>

        <form onSubmit={login} className="space-y-4">
          <div className="rounded-xl border border-surface-border bg-surface-card p-5 space-y-4">
            <div>
              <label className="text-xs text-surface-muted font-medium uppercase tracking-wider">Username</label>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="mt-1.5 w-full bg-surface border border-surface-border rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-surface-muted focus:outline-none focus:border-brand-500 transition-colors"
                placeholder="admin"
                required
              />
            </div>
            <div>
              <label className="text-xs text-surface-muted font-medium uppercase tracking-wider">Password</label>
              <div className="relative mt-1.5">
                <input
                  type={showPw ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-surface border border-surface-border rounded-lg px-3 py-2.5 text-sm text-white placeholder:text-surface-muted focus:outline-none focus:border-brand-500 transition-colors pr-10"
                  placeholder="••••••••"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-surface-muted hover:text-white"
                >
                  {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            {error && <p className="text-xs text-red-400">{error}</p>}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>
    </div>
  );
}
