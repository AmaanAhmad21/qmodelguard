import { useState } from "react";
import { register } from "../api";

export default function Register({ onSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setErr("");
    setLoading(true);

    try {
      const data = await register(username, password); // { token, user_id }
      localStorage.setItem("token", data.token);
      onSuccess?.();
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-2xl border bg-white p-6 shadow-sm">
        <h1 className="text-2xl font-bold">Register</h1>
        <p className="text-sm opacity-70 mt-1">Create an account.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-sm mb-1">Username</label>
            <input
              className="w-full rounded-xl border px-3 py-2 outline-none focus:ring"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-sm mb-1">Password</label>
            <input
              className="w-full rounded-xl border px-3 py-2 outline-none focus:ring"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          {err && <div className="text-sm text-red-600">{err}</div>}

          <button
            disabled={loading}
            className="w-full rounded-xl bg-black text-white py-2 disabled:opacity-60"
            type="submit"
          >
            {loading ? "Creating..." : "Register"}
          </button>

          <a className="block text-sm underline opacity-80" href="/login">
            Already have an account? Login
          </a>
        </form>
      </div>
    </div>
  );
}