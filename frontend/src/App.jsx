import { useEffect, useState } from "react";
import { Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { checkHealth, getMe } from "./api";

function Dashboard({ me }) {
  return (
    <div className="w-full max-w-3xl p-6">
      <div className="text-lg font-semibold">Dashboard</div>
      <div className="mt-2 text-sm opacity-80">
        Logged in as <span className="font-medium">{me?.username}</span>
      </div>
    </div>
  );
}

export default function App() {
  const navigate = useNavigate();

  const [backendOk, setBackendOk] = useState(false);
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [me, setMe] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        await checkHealth();
        setBackendOk(true);
      } catch {
        setBackendOk(false);
      }
    })();
  }, []);

useEffect(() => {
  if (!token) {
    queueMicrotask(() => setMe(null));
    return;
  }

  (async () => {
    try {
      const data = await getMe(token);
      setMe(data);
    } catch {
      setMe(null);
    }
  })();
}, [token]);

  function handleAuthSuccess() {
    const t = localStorage.getItem("token") || "";
    setToken(t);
    navigate("/");
  }

  function logout() {
    localStorage.removeItem("token");
    setToken("");
    setMe(null);
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      
      {/* Header */}
      <header className="h-16 border-b bg-white flex items-center justify-between px-6">
        <div>
          <div className="text-xl font-bold">QModelGuard</div>
          <div className="text-xs opacity-70">
            Backend:{" "}
            <span className={backendOk ? "text-green-600" : "text-red-600"}>
              {backendOk ? "connected" : "not connected"}
            </span>
          </div>
        </div>

        <nav className="flex items-center gap-4 text-sm">
          {!token ? (
            <>
              <Link className="underline" to="/login">Login</Link>
              <Link className="underline" to="/register">Register</Link>
            </>
          ) : (
            <>
              <span>{me?.username}</span>
              <button
                onClick={logout}
                className="rounded-xl border px-3 py-1"
              >
                Logout
              </button>
            </>
          )}
        </nav>
      </header>

      {/* Centered Content */}
      <main className="flex-1 flex items-center justify-center px-4">
        <Routes>
          <Route
            path="/login"
            element={
              token ? <Navigate to="/" replace /> : <Login onSuccess={handleAuthSuccess} />
            }
          />

          <Route
            path="/register"
            element={
              token ? <Navigate to="/" replace /> : <Register onSuccess={handleAuthSuccess} />
            }
          />

          <Route
            path="/"
            element={
              token ? <Dashboard me={me} /> : <Navigate to="/login" replace />
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}