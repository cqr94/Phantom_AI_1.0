import { useState, useEffect, createContext, useContext } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Box from "@mui/material/Box";
import PhantomTerminalUI from "./components/green_2_api";
import AuthModal from "./components/AuthModal";

// ─────────────────────────────────────────────────────────────
// Auth Context — available to any child component
// ─────────────────────────────────────────────────────────────
export const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

function AuthProvider({ children }) {
  const [user, setUser] = useState(null);       // { email, token }
  const [ready, setReady] = useState(false);    // hydration done

  // Rehydrate from localStorage on first load
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const email = localStorage.getItem("user_email");
    if (token && email) setUser({ email, token });
    setReady(true);
  }, []);

  const login = ({ email, token }) => {
    localStorage.setItem("access_token", token);
    localStorage.setItem("user_email", email);
    setUser({ email, token });
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_email");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, ready }}>
      {children}
    </AuthContext.Provider>
  );
}

// ─────────────────────────────────────────────────────────────
// Auth Gate — renders children only when authenticated,
// otherwise shows the full-screen MFA modal
// ─────────────────────────────────────────────────────────────
function AuthGate({ children }) {
  const { user, login, ready } = useAuth();

  // Don't flash the modal while rehydrating from localStorage
  if (!ready) return <BootSplash />;

  if (!user) {
    return (
      <>
        {/* Blurred/locked background so the app feels present but inaccessible */}
        <div style={{
          position: "fixed", inset: 0,
          background: "#020912",
          display: "flex", alignItems: "center", justifyContent: "center",
          overflow: "hidden",
        }}>
          <LockedBackground />
        </div>
        {/* Auth modal — open=true, no onClose (can't dismiss without auth) */}
        <AuthModal
          open={true}
          onClose={null}          // intentionally locked — must authenticate
          onSuccess={login}
        />
      </>
    );
  }

  return children;
}

// ─────────────────────────────────────────────────────────────
// Boot splash — shown for the ~50 ms localStorage hydration
// ─────────────────────────────────────────────────────────────
function BootSplash() {
  return (
    <div style={{
      position: "fixed", inset: 0,
      background: "#020912",
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center", gap: 16,
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@800&display=swap');
        @keyframes bootPulse { 0%,100%{opacity:.3;transform:scale(.9)} 50%{opacity:1;transform:scale(1)} }
        @keyframes bootSpin  { to{transform:rotate(360deg)} }
      `}</style>
      <div style={{
        fontFamily:"'Syne',sans-serif", fontWeight:800,
        fontSize:22, letterSpacing:6, color:"#00c8ff",
        textShadow:"0 0 24px rgba(0,200,255,0.5)",
        textTransform:"uppercase",
        animation:"bootPulse 1.4s ease-in-out infinite",
      }}>
        PHANTOM
      </div>
      <div style={{
        width:20, height:20,
        border:"2px solid rgba(0,200,255,0.2)",
        borderTop:"2px solid #00c8ff",
        borderRadius:"50%",
        animation:"bootSpin 0.8s linear infinite",
      }}/>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// Locked background — decorative grid shown behind the modal
// ─────────────────────────────────────────────────────────────
function LockedBackground() {
  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono&display=swap');
        @keyframes bgScan {
          0%   { top: -10%; opacity:.6; }
          100% { top: 110%; opacity:.2; }
        }
        @keyframes bgBlink { 0%,100%{opacity:.15} 50%{opacity:.4} }
        @keyframes bgPulseRing {
          0%   { transform:scale(.95); box-shadow:0 0 0 0 rgba(0,200,255,.25); }
          70%  { transform:scale(1);   box-shadow:0 0 0 18px rgba(0,200,255,0); }
          100% { transform:scale(.95); box-shadow:0 0 0 0 rgba(0,200,255,0); }
        }
      `}</style>

      {/* Grid lines */}
      <svg width="100%" height="100%" style={{ position:"absolute", inset:0, opacity:0.04 }}>
        <defs>
          <pattern id="bgGrid" width="48" height="48" patternUnits="userSpaceOnUse">
            <path d="M 48 0 L 0 0 0 48" fill="none" stroke="#00c8ff" strokeWidth="0.5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#bgGrid)"/>
      </svg>

      {/* Scanline */}
      <div style={{
        position:"absolute", left:0, right:0, height:"3%",
        background:"linear-gradient(transparent,rgba(0,200,255,0.05),transparent)",
        animation:"bgScan 4s linear infinite",
        pointerEvents:"none",
      }}/>

      {/* Center lock icon */}
      <div style={{
        width:80, height:80, borderRadius:"50%",
        background:"rgba(0,200,255,0.04)",
        border:"1px solid rgba(0,200,255,0.15)",
        display:"flex", alignItems:"center", justifyContent:"center",
        animation:"bgPulseRing 2.5s ease-in-out infinite",
      }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgba(0,200,255,0.35)" strokeWidth="1.5">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
          <path d="M7 11V7a5 5 0 0110 0v4"/>
        </svg>
      </div>

      {/* Corner labels */}
      {["TOP-LEFT","TOP-RIGHT","BTM-LEFT","BTM-RIGHT"].map((pos,i) => (
        <div key={i} style={{
          position:"absolute",
          top:    i < 2 ? 20 : "auto",
          bottom: i >= 2 ? 20 : "auto",
          left:   i%2===0 ? 20 : "auto",
          right:  i%2===1 ? 20 : "auto",
          fontFamily:"'Space Mono',monospace",
          fontSize:9, letterSpacing:2, color:"rgba(0,200,255,0.2)",
          textTransform:"uppercase",
          animation:`bgBlink ${1.8+i*0.3}s ease-in-out infinite`,
        }}>
          {i===0?"PHANTOM·PLATFORM":i===1?"ACCESS·RESTRICTED":i===2?"MFA·REQUIRED":"TLS·1.3·ACTIVE"}
        </div>
      ))}
    </>
  );
}

// ─────────────────────────────────────────────────────────────
// App — Router + Auth gate wrapping the terminal UI
// ─────────────────────────────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route
            path="/*"
            element={
              <AuthGate>
                <Box sx={{ width:"100vw", height:"100vh", overflow:"hidden" }}>
                  <PhantomTerminalUI />
                </Box>
              </AuthGate>
            }
          />
          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}