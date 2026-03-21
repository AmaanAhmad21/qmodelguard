import { useEffect, useMemo, useRef, useState } from "react";
import { Routes, Route, Navigate, Link, useNavigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import { ApiError } from "./api";
import Mark from "./assets/qmodelguard-mark.svg";
import {
  getMe,
  listModels,
  listActivity,
  uploadModel,
  getPublicKeyById,
  getModel,
  deleteModel,
  signModel,
  decryptModel,
  encryptModel,
  verifyModel,
  listUsers,
} from "./api";

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "download";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function IconBadge({ children, tone = "neutral" }) {
  const cls =
    tone === "good"
      ? "border-green-700/60 bg-green-900/20 text-green-100"
      : tone === "warn"
        ? "border-yellow-700/60 bg-yellow-900/20 text-yellow-100"
        : tone === "bad"
          ? "border-red-700/60 bg-red-900/20 text-red-100"
          : "border-gray-700 bg-black/20 text-gray-200";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${cls}`}>
      {children}
    </span>
  );
}

function Brand({ size = "sm" }) {
  const isSm = size === "sm";
  return (
    <div className="flex items-center gap-3">
      <img src={Mark} alt="QModelGuard" className={isSm ? "h-9 w-9" : "h-10 w-10"} />
      <div className="leading-tight">
        <div className={`font-semibold tracking-tight text-gray-100 ${isSm ? "text-sm" : "text-lg"}`}>QModelGuard</div>
        <div className="text-xs text-gray-500">Quantum-safe model protection</div>
      </div>
    </div>
  );
}

function GlassCard({ className = "", children }) {
  return (
    <div className={`rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur ${className}`}>
      {children}
    </div>
  );
}

function Modal({ open, title, description, children, onClose }) {
  const closeBtnRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    const prev = document.activeElement;
    closeBtnRef.current?.focus();
    return () => prev?.focus?.();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e) => {
      if (e.key === "Escape") onClose?.();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-xl border border-gray-700 bg-[#151515] shadow-2xl">
        <div className="flex items-start justify-between gap-4 p-4 border-b border-gray-800">
          <div>
            <div className="text-base font-semibold text-gray-100">{title}</div>
            {description ? <div className="mt-1 text-sm text-gray-400">{description}</div> : null}
          </div>
          <button
            ref={closeBtnRef}
            onClick={onClose}
            className="rounded-md border border-gray-700 px-2 py-1 text-xs text-gray-200 hover:bg-gray-800"
          >
            Close
          </button>
        </div>
        <div className="p-4">{children}</div>
      </div>
    </div>
  );
}

function Dashboard({ me, token }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [activeSection, setActiveSection] = useState("models");
  const [toasts, setToasts] = useState([]);

  function toast(message, tone = "neutral") {
    const id = crypto?.randomUUID?.() || String(Date.now() + Math.random());
    setToasts((prev) => [{ id, message, tone }, ...prev].slice(0, 4));
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }

  // Users section state
  const [userLookupId, setUserLookupId] = useState("");
  const [userKeyLoading, setUserKeyLoading] = useState(false);
  const [userKeyError, setUserKeyError] = useState("");
  const [userKeyResult, setUserKeyResult] = useState(null);
  const [usersLoading, setUsersLoading] = useState(false);
  const [usersError, setUsersError] = useState("");
  const [users, setUsers] = useState([]);

  const [models, setModels] = useState([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState("");
  const [recentActivity, setRecentActivity] = useState([]);
  async function loadActivity() {
    try {
      const data = await listActivity(token);
      setRecentActivity(
        (data.items || []).map((a) => ({
          text: a.detail,
          time: a.created_at ? new Date(a.created_at).toLocaleString() : "",
        }))
      );
    } catch (_) { /* ignore */ }
  }
  const [actionLoading, setActionLoading] = useState(null);
  const [modelSearch, setModelSearch] = useState("");
  const [pageLimit, setPageLimit] = useState(25);
  const [pageOffset, setPageOffset] = useState(0);
  const [modelsTotal, setModelsTotal] = useState(0);

  const [modal, setModal] = useState(null);
  const [modalRecipient, setModalRecipient] = useState("");

  // Health banner (crypto mode)
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState("");

  async function loadModels() {
    setModelsError("");
    setModelsLoading(true);
    try {
      const data = await listModels(token, pageLimit, pageOffset);
      setModelsTotal(Number(data.total || 0));
      setModels(
        (data.items || []).map((m) => ({
          id: String(m.id),
          name: m.filename,
          type: m.is_encrypted ? "encrypted" : "plain",
          is_signed: m.is_signed,
          signer: m.signer,
          created_at: m.created_at,
        }))
      );
    } catch (e) {
      setModelsError(e.message || "Failed to load models");
      setModels([]);
    } finally {
      setModelsLoading(false);
    }
  }

  useEffect(() => {
    if (token) { loadModels(); loadActivity(); }
  }, [token, pageLimit, pageOffset]);

  useEffect(() => {
    if (!token) return;
    setHealthError("");
    (async () => {
      try {
        const res = await fetch("/health");
        const data = await res.json().catch(() => null);
        if (res.ok) setHealth(data);
        else setHealthError("Health check failed");
      } catch (e) {
        setHealthError(e?.message || "Health check failed");
      }
    })();
  }, [token]);

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) return;
    setErr("");
    setLoading(true);
    try {
      await uploadModel(file, token);
      toast("Model uploaded.", "good");
      setActiveSection("models");
      await loadModels();
      loadActivity();
    } catch (e) {
      setErr(e.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  const filteredModels = useMemo(() => {
    const q = modelSearch.trim().toLowerCase();
    if (!q) return models;
    return models.filter((m) => m.name.toLowerCase().includes(q) || m.id.includes(q));
  }, [models, modelSearch]);

  async function handleModelAction(id, action, modelName, modelType) {
    const key = `${id}-${action}`;
    setActionLoading(key);
    setErr("");
    const modelId = Number(id);
    try {
      if (action === "Encrypt") {
        setModal({ type: "encrypt", model: { id, name: modelName } });
        setModalRecipient("");
        return;
      } else if (action === "Decrypt") {
        await decryptModel(token, { model_id: modelId });
        toast("Decrypted model created.", "good");
        loadActivity();
      } else if (action === "Sign") {
        await signModel(token, { model_id: modelId });
        toast("Model signed.", "good");
        loadActivity();
      } else if (action === "Verify") {
        const res = await verifyModel(token, { model_id: modelId });
        toast(
          res?.valid
            ? `Signature valid (signed by ${res.signer})`
            : `Signature invalid`,
          res?.valid ? "good" : "bad"
        );
        loadActivity();
      } else if (action === "Download") {
        const blob = await getModel(modelId, token);
        downloadBlob(blob, modelName);
        toast("Download started.", "neutral");
      } else if (action === "Delete") {
        setModal({ type: "delete", model: { id, name: modelName } });
        return;
      }
      await loadModels();
    } catch (e) {
      setErr(e.message || `${action} failed`);
    } finally {
      setActionLoading(null);
    }
  }

  function getModelActions(m) {
    const actions = ["Download"];
    if (m.type === "plain") actions.push("Encrypt", "Sign");
    if (m.type === "encrypted") actions.push("Decrypt");
    if (m.is_signed) actions.push("Verify");
    actions.push("Delete");
    return actions;
  }

  return (
    <>
      <div className="w-full max-w-6xl">
      {err && (
        <div className="mb-4 p-3 rounded-xl bg-red-900/20 border border-red-600/40 text-red-200 text-sm">
          {err}
        </div>
      )}

      <div className="fixed right-4 bottom-4 z-40 space-y-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`min-w-64 max-w-sm rounded-lg border px-3 py-2 text-sm shadow-lg backdrop-blur ${
              t.tone === "good"
                ? "border-green-700/60 bg-green-900/30 text-green-100"
                : t.tone === "bad"
                  ? "border-red-700/60 bg-red-900/30 text-red-100"
                  : "border-gray-700 bg-black/40 text-gray-200"
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
        {/* Sidebar */}
        <div>
          <GlassCard className="p-4">
            <Brand />

            <div className="mt-4 space-y-2">
              <div className="text-xs text-gray-400">Session</div>
              <div className="flex flex-wrap items-center gap-2">
                <IconBadge>
                  <span className="text-gray-400">User</span>
                  <span className="text-gray-100 font-medium">{me?.username || "User"}</span>
                </IconBadge>
                {health ? (
                  <IconBadge tone={health.crypto === "real" ? "good" : "warn"}>
                    <span className="text-gray-300">Crypto</span>
                    <span className="font-medium">{health.crypto || "unknown"}</span>
                  </IconBadge>
                ) : (
                  <IconBadge tone="warn">{healthError ? "Health unavailable" : "Health…"}</IconBadge>
                )}
              </div>
              {health?.algorithms?.kem && health?.algorithms?.sig ? (
                <div className="text-xs text-gray-500 mt-1">
                  {health.algorithms.kem} • {health.algorithms.sig}
                </div>
              ) : null}
            </div>

            <div className="mt-6 space-y-2">
              <div className="text-xs text-gray-400">Navigation</div>
              {[
                { id: "models", label: "Models", sub: "Manage, encrypt, verify", icon: "🗂️" },
                { id: "upload", label: "Upload", sub: "Add a new model file", icon: "📤" },
                { id: "users", label: "Users", sub: "Recipients & public keys", icon: "👥" },
              ].map((x) => (
                <button
                  key={x.id}
                  onClick={() => setActiveSection(x.id)}
                  className={`w-full rounded-xl border px-3 py-3 text-left transition ${
                    activeSection === x.id
                      ? "border-white/15 bg-white/[0.06]"
                      : "border-white/10 bg-white/[0.02] hover:bg-white/[0.05]"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">{x.icon}</div>
                    <div>
                      <div className="text-sm font-medium text-gray-100">{x.label}</div>
                      <div className="text-xs text-gray-400">{x.sub}</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>

          </GlassCard>
        </div>

        {/* Main content */}
        <div className="space-y-6">
          {activeSection === "upload" && (
            <GlassCard className="p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-base font-semibold text-gray-100">Upload model</div>
                  <div className="text-sm text-gray-400">Allowed: .pt, .safetensors, .onnx, .h5</div>
                </div>
                <div className="hidden sm:block text-xs text-gray-500">Stored locally, tied to your account</div>
              </div>
              <form onSubmit={handleUpload} className="mt-4 flex flex-col sm:flex-row gap-3 sm:items-center">
                <input
                  type="file"
                  accept=".pt,.onnx,.h5,.safetensors"
                  onChange={(e) => setFile(e.target.files[0] || null)}
                  className="w-full text-sm text-gray-300 file:mr-3 file:rounded-lg file:border file:border-white/10 file:bg-white/[0.06] file:px-3 file:py-2 file:text-sm file:text-gray-100 hover:file:bg-white/[0.09]"
                />
                <button
                  type="submit"
                  disabled={loading || !file}
                  className="rounded-xl bg-cyan-500 text-gray-900 px-4 py-2 text-sm font-medium hover:bg-cyan-400 disabled:opacity-50 transition-colors"
                >
                  {loading ? "Uploading…" : "Upload"}
                </button>
              </form>
            </GlassCard>
          )}

          {activeSection === "models" && (
            <GlassCard className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-base font-semibold text-gray-100">Models</div>
                  <div className="text-sm text-gray-400">Download, encrypt, decrypt, sign and verify.</div>
                </div>
                <div className="flex flex-wrap gap-2 items-center">
                  <input
                    value={modelSearch}
                    onChange={(e) => setModelSearch(e.target.value)}
                    placeholder="Search by name or id…"
                    className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-gray-100 placeholder-gray-500"
                  />
                  <button
                    onClick={() => loadModels()}
                    className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm hover:bg-white/[0.07]"
                  >
                    Refresh
                  </button>
                </div>
              </div>

              <div className="mt-4 overflow-hidden rounded-xl border border-white/10">
                {modelsLoading ? (
                  <div className="p-4 text-sm text-gray-400">Loading models…</div>
                ) : filteredModels.length === 0 ? (
                  <div className="p-4 text-sm text-gray-400">No models yet. Upload one to get started.</div>
                ) : (
                  <table className="w-full text-sm">
                    <thead className="bg-white/[0.04] text-gray-300">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium">Name</th>
                        <th className="px-4 py-3 text-left font-medium">Type</th>
                        <th className="px-4 py-3 text-left font-medium">Created</th>
                        <th className="px-4 py-3 text-right font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                      {filteredModels.map((m) => (
                        <tr key={m.id} className="hover:bg-white/[0.03]">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <span className="text-gray-500">#{m.id}</span>
                              <span className="font-medium text-gray-100">{m.name}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap gap-1">
                              {m.type === "encrypted" ? (
                                <IconBadge tone="warn">Encrypted</IconBadge>
                              ) : (
                                <IconBadge tone="good">Plain</IconBadge>
                              )}
                              {m.is_signed && (
                                <IconBadge tone="good">Signed{m.signer ? ` by ${m.signer}` : ""}</IconBadge>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3 text-gray-400">
                            {m.created_at ? new Date(m.created_at).toLocaleString() : "—"}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex flex-wrap justify-end gap-2">
                              {getModelActions(m).map((action) => (
                                <button
                                  key={action}
                                  disabled={actionLoading === `${m.id}-${action}`}
                                  onClick={() => handleModelAction(m.id, action, m.name, m.type)}
                                  className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-gray-100 hover:bg-white/[0.08] disabled:opacity-50"
                                >
                                  {actionLoading === `${m.id}-${action}` ? "…" : action}
                                </button>
                              ))}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-gray-400">
                <div>
                  Showing <span className="text-gray-100">{Math.min(pageOffset + 1, modelsTotal || 0)}</span>–
                  <span className="text-gray-100">{Math.min(pageOffset + pageLimit, modelsTotal || 0)}</span> of{" "}
                  <span className="text-gray-100">{modelsTotal}</span>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={pageLimit}
                    onChange={(e) => {
                      setPageLimit(Number(e.target.value));
                      setPageOffset(0);
                    }}
                    className="rounded-lg border border-white/10 bg-white/[0.04] px-2 py-1 text-gray-100"
                  >
                    {[10, 25, 50, 100].map((n) => (
                      <option key={n} value={n}>
                        {n}/page
                      </option>
                    ))}
                  </select>
                  <button
                    disabled={pageOffset <= 0}
                    onClick={() => setPageOffset((o) => Math.max(0, o - pageLimit))}
                    className="rounded-lg border border-white/10 bg-white/[0.04] px-2 py-1 disabled:opacity-50 hover:bg-white/[0.08]"
                  >
                    Prev
                  </button>
                  <button
                    disabled={pageOffset + pageLimit >= modelsTotal}
                    onClick={() => setPageOffset((o) => o + pageLimit)}
                    className="rounded-lg border border-white/10 bg-white/[0.04] px-2 py-1 disabled:opacity-50 hover:bg-white/[0.08]"
                  >
                    Next
                  </button>
                </div>
              </div>
            </GlassCard>
          )}

          {activeSection === "users" && (
            <GlassCard className="p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="text-base font-semibold text-gray-100">Users</div>
                  <div className="text-sm text-gray-400">Find recipients and fetch public keys.</div>
                </div>
                <button
                  disabled={usersLoading}
                  onClick={async () => {
                    setUsersError("");
                    setUsersLoading(true);
                    try {
                      const data = await listUsers(token);
                      setUsers(Array.isArray(data?.items) ? data.items : []);
                      toast("Loaded users.", "neutral");
                    } catch (e) {
                      setUsersError(e.message || "Failed to load users");
                    } finally {
                      setUsersLoading(false);
                    }
                  }}
                  className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm hover:bg-white/[0.08] disabled:opacity-50"
                >
                  {usersLoading ? "Loading…" : "List users"}
                </button>
              </div>

              <div className="mt-4 grid grid-cols-1 xl:grid-cols-[1fr_1fr] gap-4">
                <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <div className="text-sm font-medium text-gray-100">Lookup public keys</div>
                  <div className="mt-2 flex flex-wrap gap-2 items-center">
                    <input
                      type="text"
                      placeholder="User id or username"
                      value={userLookupId}
                      onChange={(e) => setUserLookupId(e.target.value)}
                      className="w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-gray-100 placeholder-gray-500"
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
                          toast("Loaded public keys.", "neutral");
                        } catch (e) {
                          setUserKeyError(e.message || "Failed to load key");
                        } finally {
                          setUserKeyLoading(false);
                        }
                      }}
                      className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm hover:bg-white/[0.08] disabled:opacity-50"
                    >
                      {userKeyLoading ? "Loading…" : "Get key"}
                    </button>
                  </div>
                  {userKeyError ? <div className="mt-2 text-sm text-red-300">{userKeyError}</div> : null}
                  {userKeyResult ? (
                    <pre className="mt-3 overflow-auto rounded-xl border border-white/10 bg-black/30 p-3 text-xs text-gray-200">
                      {JSON.stringify(userKeyResult, null, 2)}
                    </pre>
                  ) : null}
                </div>

                <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
                  <div className="text-sm font-medium text-gray-100">Recipients</div>
                  {usersError ? <div className="mt-2 text-sm text-red-300">{usersError}</div> : null}
                  {users.length === 0 ? (
                    <div className="mt-2 text-sm text-gray-400">Click “List users” to load recipients.</div>
                  ) : (
                    <ul className="mt-2 max-h-64 overflow-auto divide-y divide-white/10">
                      {users.map((u) => (
                        <li key={u.id} className="py-2 flex items-center justify-between">
                          <div className="text-sm text-gray-100">{u.username}</div>
                          <div className="text-xs text-gray-500">id: {u.id}</div>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            </GlassCard>
          )}

          <GlassCard className="p-5">
            <div>
              <div className="text-base font-semibold text-gray-100">Activity</div>
              <div className="text-sm text-gray-400">Audit trail of all actions.</div>
            </div>
            <ul className="mt-3 space-y-2 text-sm text-gray-300">
              {recentActivity.length === 0 ? (
                <li className="text-gray-400">No activity yet.</li>
              ) : (
                recentActivity.map((a, i) => (
                  <li key={i} className="rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2">
                    {a.text} <span className="text-gray-500">— {a.time}</span>
                  </li>
                ))
              )}
            </ul>
          </GlassCard>
        </div>
      </div>
      </div>

      <Modal
        open={Boolean(modal)}
        title={
          modal?.type === "encrypt"
            ? "Encrypt for recipient"
            : modal?.type === "delete"
              ? "Delete model"
              : "Action"
        }
        description={modal?.model ? `${modal.model.name} (id ${modal.model.id})` : undefined}
        onClose={() => setModal(null)}
      >
        {modal?.type === "encrypt" ? (
          <div className="space-y-3">
            <div className="text-sm text-gray-300">
              Enter a recipient <span className="text-gray-200">username</span> (recommended) or numeric id.
            </div>
            <input
              value={modalRecipient}
              onChange={(e) => setModalRecipient(e.target.value)}
              placeholder="e.g. bob"
              className="w-full rounded-lg border border-gray-700 bg-black/20 px-3 py-2 text-gray-200 placeholder-gray-500"
            />
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setModal(null)}
                className="rounded-lg border border-gray-700 px-3 py-2 text-sm hover:bg-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  const recipient_id = modalRecipient.trim();
                  if (!recipient_id) return;
                  try {
                    await encryptModel(token, { model_id: Number(modal.model.id), recipient_id });
                    toast("Encrypted copy created for recipient.", "good");
                    setModal(null);
                    await loadModels();
                    loadActivity();
                  } catch (e) {
                    setErr(e.message || "Encrypt failed");
                  }
                }}
                className="rounded-lg border border-indigo-400/30 bg-indigo-600 px-3 py-2 text-sm text-white hover:bg-indigo-500"
              >
                Encrypt
              </button>
            </div>
          </div>
        ) : modal?.type === "delete" ? (
          <div className="space-y-3">
            <div className="text-sm text-gray-300">
              This will remove the file from storage and delete its record. This cannot be undone.
            </div>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setModal(null)}
                className="rounded-lg border border-gray-700 px-3 py-2 text-sm hover:bg-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  try {
                    await deleteModel(Number(modal.model.id), token);
                    toast("Model deleted.", "good");
                    setModal(null);
                    await loadModels();
                    loadActivity();
                  } catch (e) {
                    setErr(e.message || "Delete failed");
                  }
                }}
                className="rounded-lg border border-red-500/30 bg-red-600 px-3 py-2 text-sm text-white hover:bg-red-500"
              >
                Delete
              </button>
            </div>
          </div>
        ) : null}
      </Modal>
    </>
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
    } catch (e) {
      setMe(null);
      if (e instanceof ApiError && e.status === 401) {
        localStorage.removeItem("token");
        localStorage.removeItem("user_id");
        setToken("");
        navigate("/login", { state: { message: "Session expired. Please sign in again." } });
      }
    }
  })();
}, [token, navigate]);

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
    <div className="min-h-screen flex flex-col bg-ink-950 bg-grid">
      <header className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-ink-900/80 backdrop-blur">
        <Link to="/" className="flex items-center gap-2 text-gray-100 hover:text-white transition-colors">
          <Brand size={token ? "sm" : "md"} />
        </Link>

        <nav className="flex items-center gap-4 text-sm">
          {!token ? (
            <>
              <Link className="text-gray-400 hover:text-gray-100 transition-colors" to="/login">Sign in</Link>
              <Link
                className="rounded-xl bg-cyan-500 text-gray-900 px-4 py-2 font-medium hover:bg-cyan-400 transition-colors"
                to="/register"
              >
                Register
              </Link>
            </>
          ) : (
            <>
              <span className="text-gray-400">{me?.username || "User"}</span>
              <button
                onClick={logout}
                className="rounded-xl border border-white/10 px-3 py-2 text-gray-300 hover:bg-white/5 transition-colors"
              >
                Logout
              </button>
            </>
          )}
        </nav>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-8">
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