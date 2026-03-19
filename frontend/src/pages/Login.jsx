import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { login } from "../api";
import Mark from "../assets/qmodelguard-mark.svg";

export default function Login({ onSuccess }) {
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const msg = location.state?.message;
    if (msg) {
      setErr(msg);
      window.history.replaceState({}, document.title, location.pathname);
    }
  }, [location.state?.message, location.pathname]);

  async function handleSubmit(e) {
    e.preventDefault();
    setErr("");
    setLoading(true);

    try {
      const data = await login(username, password);
      localStorage.setItem("token", data.token);
      localStorage.setItem("user_id", data.user_id);
      onSuccess?.();
    } catch (e) {
      setErr(e.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="w-full max-w-[420px] mx-auto text-left">
      <div className="flex items-center gap-3 mb-8">
        <img src={Mark} alt="QModelGuard" className="h-10 w-10" />
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-gray-100">Sign in</h1>
          <p className="text-sm text-gray-500">Quantum-safe model protection</p>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Username</label>
            <input
              className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-gray-100 placeholder-gray-500 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
            <input
              className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-gray-100 placeholder-gray-500 focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-colors"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
            />
          </div>

          {err && (
            <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-2.5 text-sm text-red-300" role="alert">
              {err}
            </div>
          )}

          <button
            disabled={loading}
            className="w-full rounded-xl bg-cyan-500 text-gray-900 py-3 font-medium hover:bg-cyan-400 focus:ring-2 focus:ring-cyan-500/40 disabled:opacity-50 transition-colors"
            type="submit"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-gray-500">
          Don’t have an account?{" "}
          <Link to="/register" className="text-cyan-400 hover:text-cyan-300">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
