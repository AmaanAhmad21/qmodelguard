import { useEffect, useState } from "react";
import { Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import {
  getMe,
  uploadModel,
  generateKeys,
  getPublicKeys,
  getPublicKeyById,
  getModel,
  signModel,
  decryptModel,
  encryptModel,
  verifyModel,
} from "./api";

function Dashboard({ me, token }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [success, setSuccess] = useState("");
  const [activeSection, setActiveSection] = useState("models");

  // My Keys state
  const [keysLoading, setKeysLoading] = useState(false);
  const [keysError, setKeysError] = useState("");
  const [publicKeyInfo, setPublicKeyInfo] = useState(null);
  const [generateLoading, setGenerateLoading] = useState(false);

  // Users section state
  const [userLookupId, setUserLookupId] = useState("");
  const [userKeyLoading, setUserKeyLoading] = useState(false);
  const [userKeyError, setUserKeyError] = useState("");
  const [userKeyResult, setUserKeyResult] = useState(null);

  // Mocked list; backend can replace later. type: plain | encrypted | signed
  const [models, setModels] = useState([
    { id: "1", name: "sentiment_model.pt", size: "48 MB", type: "plain" },
    { id: "2", name: "fraud_detector.pt.enc", size: "52 MB", type: "encrypted" },
    { id: "3", name: "classifier.pt", size: "120 MB", type: "signed", label: "(signed)" },
  ]);
  const [recentActivity, setRecentActivity] = useState([
    { text: "Encrypted model for @bob", time: "2 hours ago" },
    { text: "Verified signature from @charlie", time: "yesterday" },
  ]);
  const [actionLoading, setActionLoading] = useState(null); // id+action e.g. "1-sign"

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setErr("");
    setSuccess("");
    setLoading(true);
    try {
      const res = await uploadModel(file, token);
      setSuccess("Model uploaded successfully");
      setRecentActivity((prev) => [
        { text: `Uploaded ${file.name}`, time: "just now" },
        ...prev,
      ]);
      console.log("Uploaded model:", res);
    } catch (e) {
      setErr(e.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleModelAction(id, action, modelName, modelType) {
    const key = `${id}-${action}`;
    setActionLoading(key);
    setErr("");
    try {
      const blob = await getModel(id, token);
      const fd = new FormData();
      fd.append("model", blob, modelName);
      if (action === "Encrypt") {
        const recipient = window.prompt("Recipient user id or username?");
        if (recipient) fd.append("recipient", recipient);
      }
      if (action === "Sign") await signModel(token, fd);
      else if (action === "Decrypt") await decryptModel(token, fd);
      else if (action === "Encrypt") await encryptModel(token, fd);
      else if (action === "Verify") {
        const signer = window.prompt("Signer user id or username?");
        if (signer) fd.append("signer", signer);
        await verifyModel(token, fd);
      }
      setRecentActivity((prev) => [
        { text: `${action} on ${modelName}`, time: "just now" },
        ...prev.slice(0, 4),
      ]);
    } catch (e) {
      setErr(e.message || `${action} failed`);
    } finally {
      setActionLoading(null);
    }
  }

  function getModelActions(m) {
    if (m.type === "plain") return ["Encrypt", "Sign"];
    if (m.type === "encrypted") return ["Decrypt", "Verify"];
    if (m.type === "signed") return ["Encrypt", "Share"];
    return ["Encrypt", "Sign", "Decrypt", "Verify"];
  }

  return (
    <div className="w-full max-w-4xl rounded-lg border border-gray-600 bg-[#1e1e1e] p-6 text-gray-100 overflow-y-auto">
      {err && (
        <div className="mb-4 p-2 rounded bg-red-900/30 border border-red-600 text-red-300 text-sm">
          {err}
        </div>
      )}
      {/* Nav buttons */}
      <div className="flex gap-4 mb-8">
        <button
          onClick={() => setActiveSection("upload")}
          className={`flex items-center gap-2 px-4 py-3 rounded border transition ${
            activeSection === "upload"
              ? "border-gray-400 bg-gray-700"
              : "border-gray-600 hover:border-gray-500"
          }`}
        >
          <span>📤</span>
          Upload Model
        </button>
        <button
          onClick={() => setActiveSection("keys")}
          className={`flex items-center gap-2 px-4 py-3 rounded border transition ${
            activeSection === "keys"
              ? "border-gray-400 bg-gray-700"
              : "border-gray-600 hover:border-gray-500"
          }`}
        >
          <span>🔑</span>
          My Keys
        </button>
        <button
          onClick={() => setActiveSection("users")}
          className={`flex items-center gap-2 px-4 py-3 rounded border transition ${
            activeSection === "users"
              ? "border-gray-400 bg-gray-700"
              : "border-gray-600 hover:border-gray-500"
          }`}
        >
          <span>👥</span>
          Users
        </button>
      </div>

      {/* Upload section (shown when Upload Model clicked) */}
      {activeSection === "upload" && (
        <form onSubmit={handleUpload} className="mb-8 space-y-3">
          <div className="text-sm font-medium text-gray-200">Upload Model</div>
          <input
            type="file"
            accept=".pt,.onnx,.h5,.safetensors"
            onChange={(e) => setFile(e.target.files[0] || null)}
            className="text-sm text-gray-300"
          />
          {err && <div className="text-sm text-red-400">{err}</div>}
          {success && <div className="text-sm text-green-400">{success}</div>}
          <button
            type="submit"
            disabled={loading || !file}
            className="rounded border border-gray-500 bg-gray-700 px-4 py-2 text-sm disabled:opacity-50 hover:bg-gray-600"
          >
            {loading ? "Uploading..." : "Upload"}
          </button>
        </form>
      )}

      {activeSection === "keys" && (
        <div className="mb-8 text-sm">
          <div className="font-medium text-gray-200 mb-2">My Keys</div>
          {keysError && <div className="text-red-400 mb-2">{keysError}</div>}
          <div className="flex flex-wrap gap-4 items-start">
            <button
              disabled={generateLoading}
              onClick={async () => {
                setKeysError("");
                setGenerateLoading(true);
                try {
                  await generateKeys(token);
                  const data = await getPublicKeys(token);
                  setPublicKeyInfo(data);
                  setRecentActivity((prev) => [
                    { text: "Generated new keypair", time: "just now" },
                    ...prev.slice(0, 4),
                  ]);
                } catch (e) {
                  setKeysError(e.message || "Failed to generate keys");
                } finally {
                  setGenerateLoading(false);
                }
              }}
              className="rounded border border-gray-500 bg-gray-700 px-4 py-2 hover:bg-gray-600 disabled:opacity-50"
            >
              {generateLoading ? "Generating…" : "Generate my keys"}
            </button>
            <button
              disabled={keysLoading}
              onClick={async () => {
                setKeysError("");
                setKeysLoading(true);
                try {
                  const data = await getPublicKeys(token);
                  setPublicKeyInfo(data);
                } catch (e) {
                  setKeysError(e.message || "Failed to load keys");
                } finally {
                  setKeysLoading(false);
                }
              }}
              className="rounded border border-gray-500 bg-gray-700 px-4 py-2 hover:bg-gray-600 disabled:opacity-50"
            >
              {keysLoading ? "Loading…" : "Refresh my public key"}
            </button>
          </div>
          {publicKeyInfo && (
            <div className="mt-4 p-3 rounded border border-gray-600 bg-black/30 text-gray-300 font-mono text-xs break-all">
              {typeof publicKeyInfo === "string"
                ? publicKeyInfo
                : JSON.stringify(publicKeyInfo, null, 2)}
            </div>
          )}
        </div>
      )}

      {activeSection === "users" && (
        <div className="mb-8 text-sm">
          <div className="font-medium text-gray-200 mb-2">Users</div>
          <p className="text-gray-400 mb-2">Get another user&apos;s public key by id or username.</p>
          {userKeyError && <div className="text-red-400 mb-2">{userKeyError}</div>}
          <div className="flex gap-2 items-center flex-wrap">
            <input
              type="text"
              placeholder="User id or username"
              value={userLookupId}
              onChange={(e) => setUserLookupId(e.target.value)}
              className="rounded border border-gray-600 bg-gray-800 px-3 py-2 text-gray-200 placeholder-gray-500 w-48"
            />
            <button
              disabled={userKeyLoading || !userLookupId.trim()}
              onClick={async () => {
                setUserKeyError("");
                setUserKeyResult(null);
                setUserKeyLoading(true);
                try {
                  const data = await getPublicKeyById(userLookupId.trim());
                  setUserKeyResult(data);
                } catch (e) {
                  setUserKeyError(e.message || "Failed to load key");
                } finally {
                  setUserKeyLoading(false);
                }
              }}
              className="rounded border border-gray-500 bg-gray-700 px-4 py-2 hover:bg-gray-600 disabled:opacity-50"
            >
              {userKeyLoading ? "Loading…" : "Get public key"}
            </button>
          </div>
          {userKeyResult && (
            <div className="mt-4 p-3 rounded border border-gray-600 bg-black/30 text-gray-300 font-mono text-xs break-all">
              {typeof userKeyResult === "string"
                ? userKeyResult
                : JSON.stringify(userKeyResult, null, 2)}
            </div>
          )}
        </div>
      )}

      {/* Your Models */}
      <div className="mb-8">
        <div className="text-sm font-medium text-gray-200 mb-3">Your Models</div>
        <ul className="space-y-3">
          {models.map((m) => (
            <li
              key={m.id}
              className="flex items-center justify-between py-2 border-b border-gray-600"
            >
              <div className="flex items-center gap-2">
                {m.type === "plain" && <span>📄</span>}
                {m.type === "encrypted" && <span>🔒</span>}
                {m.type === "signed" && <span>✅</span>}
                <span className="text-gray-200">{m.name}</span>
                {m.label && <span className="text-gray-500 text-xs">{m.label}</span>}
                <span className="text-gray-500 text-xs">{m.size}</span>
              </div>
              <div className="flex gap-2">
                {getModelActions(m).map((action) => (
                  <button
                    key={action}
                    disabled={actionLoading === `${m.id}-${action}`}
                    onClick={() => handleModelAction(m.id, action, m.name, m.type)}
                    className="px-2 py-1 rounded border border-gray-500 text-xs hover:bg-gray-700 disabled:opacity-50"
                  >
                    {actionLoading === `${m.id}-${action}` ? "…" : action}
                  </button>
                ))}
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Recent Activity */}
      <div>
        <div className="text-sm font-medium text-gray-200 mb-3">Recent Activity</div>
        <ul className="list-disc list-inside text-sm text-gray-400 space-y-1">
          {recentActivity.map((a, i) => (
            <li key={i}>
              {a.text} – {a.time}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default function App() {
  const navigate = useNavigate();

  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [me, setMe] = useState(null);

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
    localStorage.removeItem("user_id");
    setToken("");
    setMe(null);
    navigate("/login");
  }

  return (
    <div className={`min-h-screen flex flex-col ${token ? "bg-[#0d0d0d]" : "bg-gray-50"}`}>
      {/* Header */}
      <header className={`h-16 border-b flex items-center justify-between px-6 ${
        token ? "border-gray-700 bg-[#1a1a1a] text-gray-100" : "border-gray-200 bg-white"
      }`}>
        <div className="flex items-center gap-2">
          {token && <span>🔒</span>}
          <div className="text-xl font-bold">QModelGuard</div>
        </div>

        <nav className="flex items-center gap-4 text-sm">
          {!token ? (
            <>
              <Link className="underline" to="/login">Login</Link>
              <Link className="underline" to="/register">Register</Link>
            </>
          ) : (
            <>
              <span className="text-gray-400">[{me?.username || "User"} ▼]</span>
              <button
                onClick={logout}
                className="rounded border border-gray-500 px-3 py-1 hover:bg-gray-700"
              >
                Logout
              </button>
            </>
          )}
        </nav>
      </header>

      {/* Centered Content */}
      <main className={`flex-1 flex items-center justify-center px-4 py-6 ${
        token ? "bg-[#0d0d0d]" : ""
      }`}>
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
              token ? <Dashboard me={me} token={token} /> : <Navigate to="/login" replace />
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}