import { useState, useEffect, useRef, createContext, useContext } from "react";

const BASE_URL = "http://localhost:8070";

// ─────────────────────────────────────────────
// AUTH CONTEXT
// ─────────────────────────────────────────────
const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

// ─────────────────────────────────────────────
// MODAL CORE
// ─────────────────────────────────────────────
function Modal({ open, children, onClose }) {
  useEffect(() => {
    const esc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);

  if (!open) return null;

  return (
    <div
      onClick={(e) => e.target === e.currentTarget && onClose?.()}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(2,8,16,0.88)",
        backdropFilter: "blur(10px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 9999,
      }}
    >
      <div
        style={{
          width: 420,
          background: "rgba(6,15,28,0.95)",
          border: "1px solid rgba(0,200,255,0.2)",
          borderRadius: 14,
          boxShadow: "0 0 60px rgba(0,200,255,0.08)",
          overflow: "hidden",
        }}
      >
        {children}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// AUTH PROVIDER
// ─────────────────────────────────────────────
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [refreshToken, setRefreshToken] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshTimer = useRef(null);

  // ───────── restore session ─────────
  useEffect(() => {
    const at = localStorage.getItem("access_token");
    const rt = localStorage.getItem("refresh_token");

    if (at && rt) {
      setAccessToken(at);
      setRefreshToken(rt);
      scheduleRefresh(rt);
    }

    setLoading(false);
  }, []);

  // ───────── refresh scheduler ─────────
  const scheduleRefresh = (rt) => {
    clearTimeout(refreshTimer.current);

    refreshTimer.current = setTimeout(async () => {
      await refresh(rt);
    }, 1000 * 60 * 10); // refresh every 10 min
  };

  // ───────── login ─────────
  const login = async (email, password) => {
    const r = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await r.json();

    // MFA required
    if (data.mfa_required) return { mfa: true };

    setAccessToken(data.access_token);
    setRefreshToken(data.refresh_token);
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    scheduleRefresh(data.refresh_token);

    setUser({ email });

    return { ok: true };
  };

  // ───────── MFA verify ─────────
  const verifyMFA = async (email, code, rememberDevice) => {
    const r = await fetch(`${BASE_URL}/auth/verify-mfa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code, remember_device: rememberDevice }),
    });

    const data = await r.json();

    setAccessToken(data.access_token);
    setRefreshToken(data.refresh_token);

    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    scheduleRefresh(data.refresh_token);

    setUser({ email });

    return true;
  };

  // ───────── refresh rotation ─────────
  const refresh = async (rt) => {
    try {
      const r = await fetch(`${BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: rt }),
      });

      if (!r.ok) throw new Error("refresh failed");

      const data = await r.json();

      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);

      scheduleRefresh(data.refresh_token);
    } catch (e) {
      logout();
    }
  };

  // ───────── logout ─────────
  const logout = async () => {
    const rt = localStorage.getItem("refresh_token");

    try {
      await fetch(`${BASE_URL}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: rt }),
      });
    } catch {}

    setUser(null);
    setAccessToken(null);
    setRefreshToken(null);

    localStorage.clear();
    clearTimeout(refreshTimer.current);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        login,
        verifyMFA,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ─────────────────────────────────────────────
// AUTH MODAL (FULL UX FLOW)
// ─────────────────────────────────────────────
export function AuthModal({ open, onClose }) {
  const { login, verifyMFA } = useAuth();

  const [step, setStep] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [code, setCode] = useState("");
  const [remember, setRemember] = useState(true);

  const [loading, setLoading] = useState(false);
  const [lockout, setLockout] = useState(0);

  // ───────── rate limit simulation ─────────
  const handleRateLimit = (msg) => {
    if (msg.includes("429")) {
      setLockout(30);
      const t = setInterval(() => {
        setLockout((p) => {
          if (p <= 1) {
            clearInterval(t);
            return 0;
          }
          return p - 1;
        });
      }, 1000);
    }
  };

  const handleLogin = async () => {
    if (lockout) return;

    setLoading(true);
    try {
      const res = await login(email, password);

      if (res?.mfa) {
        setStep("mfa");
      }
    } catch (e) {
      handleRateLimit(e.message);
    }
    setLoading(false);
  };

  const handleMFA = async () => {
    setLoading(true);
    try {
      await verifyMFA(email, code, remember);
      onClose?.();
    } catch (e) {}
    setLoading(false);
  };

  return (
    <Modal open={open} onClose={onClose}>
      {/* HEADER */}
      <div style={{
        padding: 14,
        borderBottom: "1px solid rgba(0,200,255,0.12)",
        fontFamily: "monospace",
        color: "#00c8ff",
        fontSize: 11
      }}>
        PHANTOM AUTH SYSTEM
      </div>

      {/* BODY */}
      <div style={{ padding: 16 }}>
        {/* LOGIN */}
        {step === "login" && (
          <>
            <input
              placeholder="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={inputStyle}
            />

            <input
              placeholder="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={inputStyle}
            />

            {lockout > 0 && (
              <div style={{ color: "#ff4466", fontSize: 11, marginBottom: 8 }}>
                Rate limited. Try again in {lockout}s
              </div>
            )}

            <button
              onClick={handleLogin}
              disabled={loading || lockout}
              style={btnStyle}
            >
              {loading ? "AUTHORIZING…" : "LOGIN →"}
            </button>
          </>
        )}

        {/* MFA */}
        {step === "mfa" && (
          <>
            <div style={{ color: "#7a9ab8", fontSize: 11, marginBottom: 8 }}>
              Enter MFA Code
            </div>

            <input
              placeholder="6-digit code"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              style={inputStyle}
            />

            <label style={{ fontSize: 11, color: "#7a9ab8" }}>
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
              />
              {" "}Remember device
            </label>

            <button onClick={handleMFA} style={btnStyle}>
              VERIFY →
            </button>
          </>
        )}
      </div>
    </Modal>
  );
}

// ─────────────────────────────────────────────
// STYLES
// ─────────────────────────────────────────────
const inputStyle = {
  width: "100%",
  padding: 10,
  marginBottom: 8,
  background: "rgba(0,200,255,0.03)",
  border: "1px solid rgba(0,200,255,0.15)",
  borderRadius: 8,
  color: "#c8ddf0",
  outline: "none",
  fontFamily: "monospace",
};

const btnStyle = {
  width: "100%",
  padding: 10,
  marginTop: 8,
  background: "#00c8ff",
  border: "none",
  borderRadius: 8,
  color: "#020810",
  fontWeight: 700,
  cursor: "pointer",
  boxShadow: "0 0 14px rgba(0,200,255,0.25)",
};