import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { login } from "../api";

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
      const data = await login(username, password); // { token, user_id }
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
    <div className="min-h-[calc(100vh-64px)] w-full flex items-center justify-center px-6 bg-gray-50">
      <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-8 shadow-md text-left">
        <h1 className="text-2xl font-bold text-gray-900">Login</h1>
        <p className="text-sm text-gray-600 mt-1">Sign in to your account.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
            <input
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {err && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700" role="alert">
              {err}
            </div>
          )}

          <button
            disabled={loading}
            className="w-full rounded-lg bg-indigo-600 text-white py-2.5 font-medium hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-60 transition-colors"
            type="submit"
          >
            {loading ? "Logging in..." : "Login"}
          </button>

          <div className="text-sm text-center opacity-80">
            <Link className="underline" to="/register">
              Don’t have an account? Register
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}