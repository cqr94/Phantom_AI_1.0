import { useState, useRef, useEffect, useCallback } from "react";

const BASE_URL = "http://localhost:8070";

// ─── CSS ──────────────────────────────────────────────────────────────────────
const AUTH_STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;600;700;800&display=swap');

  .auth-overlay {
    position: fixed; inset: 0; z-index: 9999;
    background: rgba(1, 5, 12, 0.92);
    backdrop-filter: blur(12px) saturate(0.7);
    display: flex; align-items: center; justify-content: center;
    animation: authFadeIn 0.25s ease-out;
  }
  @keyframes authFadeIn { from { opacity:0; } to { opacity:1; } }
  @keyframes authSlideUp {
    from { opacity:0; transform: translateY(20px) scale(0.97); }
    to   { opacity:1; transform: translateY(0)   scale(1); }
  }
  @keyframes authGlitch {
    0%,100% { clip-path: inset(0 0 100% 0); transform: translateX(0); }
    10% { clip-path: inset(10% 0 85% 0); transform: translateX(-3px); }
    20% { clip-path: inset(40% 0 50% 0); transform: translateX(3px); }
    30% { clip-path: inset(70% 0 20% 0); transform: translateX(-2px); }
    40% { clip-path: inset(90% 0 5%  0); transform: translateX(0); }
  }
  @keyframes authSpin { to { transform: rotate(360deg); } }
  @keyframes authPulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(0,200,255,0.4); }
    50%      { box-shadow: 0 0 0 8px rgba(0,200,255,0); }
  }
  @keyframes authShake {
    0%,100% { transform: translateX(0); }
    20%     { transform: translateX(-6px); }
    40%     { transform: translateX(6px); }
    60%     { transform: translateX(-4px); }
    80%     { transform: translateX(4px); }
  }
  @keyframes authSuccessExpand {
    from { transform: scale(0.5); opacity:0; }
    to   { transform: scale(1);   opacity:1; }
  }
  @keyframes authScanline {
    0%   { top: -5%; }
    100% { top: 105%; }
  }
  @keyframes authDigitSlot {
    from { transform: translateY(-100%); opacity:0; }
    to   { transform: translateY(0);     opacity:1; }
  }
  @keyframes authQrReveal {
    from { opacity:0; filter: blur(6px) brightness(0.4); }
    to   { opacity:1; filter: blur(0)   brightness(1); }
  }
  @keyframes authBlink { 0%,100% { opacity:1; } 50% { opacity:0; } }
  @keyframes authProgressFill {
    from { width:0%; }
    to   { width:100%; }
  }
  @keyframes authTimerPulse {
    0%   { color: var(--a-cyan); }
    80%  { color: var(--a-cyan); }
    90%  { color: var(--a-amber); }
    100% { color: var(--a-red); }
  }

  .auth-panel {
    --a-bg:       #000000;
  --a-surf:     #020402;
  --a-surf2:    #06110a;

  --a-border:   rgba(0,255,136,0.10);
  --a-border2:  rgba(0,255,136,0.22);

  --a-cyan:     #00ff88; /* repurposed to primary green */
  --a-green:    #00ff88;

  --a-red:      #ff5577;
  --a-amber:    #7dffb2;

  --a-text:     #b6ffcf;
  --a-text2:    #4d7a5e;
  --a-text3:    #23412f;

  --a-mono:     'JetBrains Mono', monospace;
  --a-head:     'JetBrains Mono', monospace;

  font-family: var(--a-mono);

  width: 440px;
  max-width: 96vw;

  background:
    linear-gradient(
      180deg,
      rgba(0,255,136,0.03) 0%,
      rgba(0,0,0,0) 100%
    ),
    var(--a-surf);

  border: 1px solid var(--a-border2);
  border-radius: 16px;
  overflow: hidden;

  box-shadow:
    0 0 32px rgba(0,255,136,0.08),
    0 0 2px rgba(0,255,136,0.18),
    0 32px 64px rgba(0,0,0,0.78);

  animation: authSlideUp 0.3s cubic-bezier(0.16,1,0.3,1);
  position: relative;
}

  /* scanline effect */
  .auth-panel::before {
    content:''; position:absolute; left:0; right:0; height:8%;
    background: linear-gradient(transparent, rgba(0,200,255,0.04), transparent);
    pointer-events:none; z-index:10;
    animation: authScanline 3.5s linear infinite;
  }

  .auth-header {
    padding: 20px 24px 16px;
    border-bottom: 1px solid var(--a-border);
    background: rgba(0,200,255,0.02);
    position: relative; overflow: hidden;
  }
  .auth-header-noise {
    position:absolute; inset:0; opacity:0.03;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
    pointer-events:none;
  }
  .auth-logo-row {
    display: flex; align-items: center; gap: 12px; margin-bottom: 4px;
  }
  .auth-logo-icon {
    width: 36px; height: 36px; border-radius: 9px;
    background: rgba(0,200,255,0.08);
    border: 1px solid rgba(0,200,255,0.25);
    box-shadow: 0 0 16px rgba(0,200,255,0.2), inset 0 0 8px rgba(0,200,255,0.05);
    display:flex; align-items:center; justify-content:center;
    flex-shrink:0;
  }
  .auth-title {
    font-family: var(--a-head);
    font-size: 16px; font-weight: 800;
    color: var(--a-cyan);
    letter-spacing: 2px;
    text-transform: uppercase;
  }
  .auth-subtitle {
    font-size: 9px; color: var(--a-text3);
    letter-spacing: 1.5px; text-transform: uppercase;
    margin-top: 2px;
  }

  /* Step tabs */
  .auth-tabs {
    display: flex; gap: 2px;
    padding: 12px 24px 0;
    border-bottom: 1px solid var(--a-border);
    background: rgba(0,0,0,0.2);
  }
  .auth-tab {
    flex: 1; padding: 8px 0; text-align: center;
    font-size: 9px; letter-spacing: 1.5px; text-transform: uppercase;
    color: var(--a-text3); cursor: pointer;
    border: none; background: none;
    border-bottom: 2px solid transparent;
    transition: all 0.2s; font-family: var(--a-mono);
  }
  .auth-tab.active {
    color: var(--a-cyan);
    border-bottom-color: var(--a-cyan);
    text-shadow: 0 0 8px rgba(0,200,255,0.5);
  }
  .auth-tab:disabled {
    opacity: 0.3; cursor: default;
  }

  /* Body */
  .auth-body { padding: 24px; }

  /* Step indicator */
  .auth-steps {
    display: flex; align-items: center; gap: 0; margin-bottom: 24px;
  }
  .auth-step-dot {
    width: 24px; height: 24px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 9px; font-weight: 700; letter-spacing: 0;
    transition: all 0.3s; flex-shrink:0;
  }
  .auth-step-dot.done  { background: var(--a-green); color: #010810; box-shadow: 0 0 12px rgba(0,255,157,0.4); }
  .auth-step-dot.active { background: var(--a-cyan); color: #010810; box-shadow: 0 0 12px rgba(0,200,255,0.5), 0 0 24px rgba(0,200,255,0.2); animation: authPulse 1.8s ease-in-out infinite; }
  .auth-step-dot.pending { background: rgba(0,200,255,0.06); color: var(--a-text3); border: 1px solid var(--a-border2); }
  .auth-step-line {
    flex: 1; height: 1px;
    background: var(--a-border);
    transition: background 0.4s;
  }
  .auth-step-line.filled { background: var(--a-green); box-shadow: 0 0 6px rgba(0,255,157,0.3); }

  .auth-step-label {
    display: flex; justify-content: space-between;
    margin-top: 6px; margin-bottom: 20px;
  }
  .auth-step-label span {
    flex:1; text-align:center; font-size:8px; letter-spacing:1px;
    color: var(--a-text3); text-transform:uppercase;
  }
  .auth-step-label span.active-label { color: var(--a-cyan); }

  /* Form fields */
  .auth-field { margin-bottom: 14px; }
  .auth-label {
    display: block; font-size: 9px; letter-spacing: 1.5px;
    color: var(--a-text2); text-transform: uppercase;
    margin-bottom: 6px;
  }
  .auth-input-wrap { position: relative; }
  .auth-input {
    width: 100%; padding: 11px 14px;
    background: rgba(0,200,255,0.03);
    border: 1px solid var(--a-border2);
    border-radius: 8px; color: var(--a-text);
    font-size: 12px; font-family: var(--a-mono);
    outline: none; transition: all 0.2s;
    letter-spacing: 0.5px;
  }
  .auth-input:focus {
    border-color: rgba(0,200,255,0.45);
    background: rgba(0,200,255,0.05);
    box-shadow: 0 0 0 3px rgba(0,200,255,0.08), 0 0 16px rgba(0,200,255,0.1);
  }
  .auth-input.error { border-color: rgba(255,68,102,0.5); box-shadow: 0 0 0 3px rgba(255,68,102,0.06); }
  .auth-input::placeholder { color: var(--a-text3); }
  .auth-input-icon {
    position:absolute; right:12px; top:50%; transform:translateY(-50%);
    color: var(--a-text3); pointer-events:none;
  }

  /* OTP digit grid */
  .auth-otp-grid {
    display: flex; gap: 8px; justify-content: center; margin: 8px 0;
  }
  .auth-otp-digit {
    width: 48px; height: 56px;
    background: rgba(0,200,255,0.04);
    border: 1px solid var(--a-border2);
    border-radius: 10px;
    font-size: 22px; font-weight: 700; font-family: var(--a-head);
    color: var(--a-cyan); text-align: center;
    outline: none; caret-color: var(--a-cyan);
    transition: all 0.15s;
    letter-spacing: 0;
    -moz-appearance: textfield;
  }
  .auth-otp-digit:focus {
    border-color: var(--a-cyan);
    background: rgba(0,200,255,0.08);
    box-shadow: 0 0 0 3px rgba(0,200,255,0.1), 0 0 20px rgba(0,200,255,0.15);
  }
  .auth-otp-digit.filled {
    border-color: rgba(0,200,255,0.4);
    animation: authDigitSlot 0.15s ease-out;
  }
  .auth-otp-digit.shake { animation: authShake 0.4s ease-out; }
  .auth-otp-digit::-webkit-outer-spin-button,
  .auth-otp-digit::-webkit-inner-spin-button { -webkit-appearance:none; }

  /* QR Code */
  .auth-qr-wrap {
    display: flex; flex-direction:column; align-items:center;
    gap: 16px; padding: 16px 0;
  }
  .auth-qr-frame {
    position: relative; padding: 12px;
    background: #fff; border-radius: 12px;
    box-shadow: 0 0 40px rgba(0,200,255,0.2), 0 0 80px rgba(0,200,255,0.06);
    animation: authQrReveal 0.5s ease-out;
  }
  .auth-qr-corner {
    position:absolute; width:16px; height:16px;
    border-color: var(--a-cyan); border-style:solid;
    border-width: 0;
  }
  .auth-qr-corner.tl { top:-2px; left:-2px; border-top-width:3px; border-left-width:3px; border-radius:3px 0 0 0; }
  .auth-qr-corner.tr { top:-2px; right:-2px; border-top-width:3px; border-right-width:3px; border-radius:0 3px 0 0; }
  .auth-qr-corner.bl { bottom:-2px; left:-2px; border-bottom-width:3px; border-left-width:3px; border-radius:0 0 0 3px; }
  .auth-qr-corner.br { bottom:-2px; right:-2px; border-bottom-width:3px; border-right-width:3px; border-radius:0 0 3px 0; }

  /* Buttons */
  .auth-btn {
    width: 100%; padding: 12px;
    border-radius: 9px; border: none; cursor: pointer;
    font-family: var(--a-mono); font-size: 11px;
    font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; transition: all 0.2s;
    display: flex; align-items: center; justify-content: center; gap: 8px;
    position: relative; overflow: hidden;
  }
  .auth-btn-primary {
    background: var(--a-cyan); color: #010810;
    box-shadow: 0 0 20px rgba(0,200,255,0.3), 0 4px 12px rgba(0,0,0,0.4);
  }
  .auth-btn-primary:hover:not(:disabled) {
    background: #1fd8ff;
    box-shadow: 0 0 30px rgba(0,200,255,0.5), 0 4px 20px rgba(0,0,0,0.4);
    transform: translateY(-1px);
  }
  .auth-btn-primary:disabled { background: rgba(0,200,255,0.15); color: var(--a-text3); box-shadow:none; cursor:default; }
  .auth-btn-ghost {
    background: transparent; color: var(--a-text2);
    border: 1px solid var(--a-border2);
  }
  .auth-btn-ghost:hover { border-color: rgba(0,200,255,0.3); color: var(--a-cyan); }
  .auth-btn-success {
    background: var(--a-green); color: #010810;
    box-shadow: 0 0 20px rgba(0,255,157,0.3);
    animation: authSuccessExpand 0.3s cubic-bezier(0.34,1.56,0.64,1);
  }

  /* Alert */
  .auth-alert {
    padding: 10px 14px; border-radius: 7px; font-size: 10px;
    letter-spacing: 0.5px; margin-bottom: 14px;
    display: flex; align-items: center; gap: 8px; line-height: 1.5;
  }
  .auth-alert.error   { background: rgba(255,68,102,0.08); border:1px solid rgba(255,68,102,0.25); color: #ff6680; }
  .auth-alert.success { background: rgba(0,255,157,0.08); border:1px solid rgba(0,255,157,0.2);  color: var(--a-green); }
  .auth-alert.info    { background: rgba(0,200,255,0.06); border:1px solid rgba(0,200,255,0.2);  color: var(--a-cyan); }

  /* Timer bar */
  .auth-timer-bar {
    height: 2px; border-radius: 1px; margin-top: 12px;
    background: rgba(0,200,255,0.1); overflow: hidden;
  }
  .auth-timer-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--a-cyan), var(--a-green));
    transition: width 1s linear;
  }

  /* Footer */
  .auth-footer {
    padding: 12px 24px;
    border-top: 1px solid var(--a-border);
    background: rgba(0,0,0,0.3);
    display: flex; align-items:center; justify-content:space-between;
    font-size: 9px; letter-spacing: 1px; color: var(--a-text3);
    text-transform: uppercase;
  }
  .auth-footer-dot {
    width:5px; height:5px; border-radius:50%;
    background: var(--a-green);
    box-shadow: 0 0 6px var(--a-green);
    animation: authBlink 2.5s ease-in-out infinite;
  }

  /* Spinner */
  .auth-spinner {
    width:14px; height:14px;
    border: 2px solid rgba(1,8,16,0.3);
    border-top-color: #010810;
    border-radius: 50%;
    animation: authSpin 0.7s linear infinite;
  }

  /* Close btn */
  .auth-close {
    position:absolute; top:16px; right:20px;
    width:28px; height:28px; border-radius:6px;
    background:rgba(255,68,102,0.05); border:1px solid rgba(255,68,102,0.15);
    cursor:pointer; color:var(--a-red); font-size:14px;
    display:flex; align-items:center; justify-content:center;
    transition:all 0.15s; font-family:var(--a-mono);
  }
  .auth-close:hover { background:rgba(255,68,102,0.15); }

  .auth-divider {
    display:flex; align-items:center; gap:10; margin:14px 0;
    font-size:9px; color:var(--a-text3); letter-spacing:1px;
  }
  .auth-divider::before,.auth-divider::after {
    content:''; flex:1; height:1px; background:var(--a-border);
  }

  .auth-switch-link {
    background:none; border:none; cursor:pointer;
    color:var(--a-cyan); font-family:var(--a-mono);
    font-size:10px; text-decoration:underline; letter-spacing:0.5px;
    transition:opacity 0.15s;
  }
  .auth-switch-link:hover { opacity:0.7; }

  .auth-info-row {
    font-size:9px; color:var(--a-text3); letter-spacing:0.8px;
    margin-bottom:8px; line-height:1.6;
  }
  .auth-info-row strong { color:var(--a-text2); }

  .auth-secret-box {
    background:rgba(0,200,255,0.04); border:1px solid var(--a-border2);
    border-radius:6px; padding:8px 12px;
    font-size:11px; letter-spacing:3px; color:var(--a-cyan);
    text-align:center; margin:8px 0; font-family:var(--a-mono);
    user-select:all; cursor:text;
    word-break: break-all;
  }
`;

// ─── OTP Input Component ──────────────────────────────────────────────────────
function OtpInput({ value, onChange, onComplete, shake }) {
  const inputs = useRef([]);
  const digits = value.split("").concat(Array(6).fill("")).slice(0,6);

  const handleKey = (e, idx) => {
    if (e.key === "Backspace") {
      e.preventDefault();
      const next = value.slice(0, idx) + value.slice(idx+1);
      onChange(next);
      if (idx > 0) inputs.current[idx-1]?.focus();
    } else if (e.key === "ArrowLeft" && idx > 0) {
      inputs.current[idx-1]?.focus();
    } else if (e.key === "ArrowRight" && idx < 5) {
      inputs.current[idx+1]?.focus();
    }
  };

  const handleInput = (e, idx) => {
    const raw = e.target.value.replace(/\D/g,"").slice(-1);
    if (!raw) return;
    const arr = value.split("").concat(Array(6).fill("")).slice(0,6);
    arr[idx] = raw;
    const next = arr.join("").replace(/\s/g,"").slice(0,6);
    onChange(next);
    if (idx < 5) inputs.current[idx+1]?.focus();
    if (next.length === 6) onComplete?.(next);
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData("text").replace(/\D/g,"").slice(0,6);
    if (pasted) { onChange(pasted); if (pasted.length === 6) onComplete?.(pasted); }
    e.preventDefault();
  };

  return (
    <div className="auth-otp-grid">
      {digits.map((d, i) => (
        <input
          key={i}
          ref={el => inputs.current[i] = el}
          className={`auth-otp-digit${d ? " filled" : ""}${shake ? " shake" : ""}`}
          type="text" inputMode="numeric" maxLength={1}
          value={d} onPaste={handlePaste}
          onChange={e => handleInput(e, i)}
          onKeyDown={e => handleKey(e, i)}
          onFocus={e => e.target.select()}
          autoComplete="one-time-code"
        />
      ))}
    </div>
  );
}

// ─── Steps Component ──────────────────────────────────────────────────────────
function StepIndicator({ step, mode }) {
  const steps = mode === "register"
    ? ["CREDENTIALS","MFA SETUP","VERIFY"]
    : ["CREDENTIALS","MFA CODE"];
  const total = steps.length;
  return (
    <>
      <div className="auth-steps">
        {steps.map((_, i) => {
          const s = i < step ? "done" : i === step ? "active" : "pending";
          return (
            <>
              <div key={i} className={`auth-step-dot ${s}`}>
                {s === "done" ? "✓" : i+1}
              </div>
              {i < total-1 && <div className={`auth-step-line${i < step ? " filled" : ""}`} />}
            </>
          );
        })}
      </div>
      <div className="auth-step-label">
        {steps.map((l,i) => (
          <span key={i} className={i === step ? "active-label" : ""}>{l}</span>
        ))}
      </div>
    </>
  );
}

// ─── Main AuthModal ───────────────────────────────────────────────────────────
export default function AuthModal({ open, onClose, onSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [step, setStep] = useState(0);

  // Shared fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);

  // Register
  const [qrCode, setQrCode] = useState(null);

  // MFA
  const [otp, setOtp] = useState("");
  const [otpShake, setOtpShake] = useState(false);

  // UI state
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState(null); // { type, msg }
  const [success, setSuccess] = useState(false);
  const [timer, setTimer] = useState(30);

  // Timer for TOTP window
  useEffect(() => {
    if (step === (mode === "register" ? 2 : 1)) {
      setTimer(30 - (Math.floor(Date.now()/1000) % 30));
      const t = setInterval(() => {
        setTimer(30 - (Math.floor(Date.now()/1000) % 30));
      }, 1000);
      return () => clearInterval(t);
    }
  }, [step, mode]);

  const clearAlert = () => setAlert(null);

  const switchMode = (m) => {
    setMode(m); setStep(0); setAlert(null);
    setEmail(""); setPassword(""); setOtp("");
    setQrCode(null); setSuccess(false);
  };

  // ── REGISTER STEP 0: submit credentials ──────────────────────────────────
  const handleRegister = async () => {
    if (!email || !password) { setAlert({ type:"error", msg:"Email and password required." }); return; }
    if (password.length < 8) { setAlert({ type:"error", msg:"Password must be at least 8 characters." }); return; }
    setLoading(true); clearAlert();
    try {
      const r = await fetch(`${BASE_URL}/register`, {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ email, password }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Registration failed");
      setQrCode(d.qr_code_base64);
      setStep(1);
      setAlert({ type:"success", msg:"Account created! Scan the QR code with your authenticator app." });
    } catch(e) {
      setAlert({ type:"error", msg: e.message });
    } finally { setLoading(false); }
  };

  // ── LOGIN STEP 0: submit credentials ─────────────────────────────────────
  const handleLogin = async () => {
    if (!email || !password) { setAlert({ type:"error", msg:"Email and password required." }); return; }
    setLoading(true); clearAlert();
    try {
      const r = await fetch(`${BASE_URL}/login`, {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ email, password }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Login failed");
      if (d.mfa_required) {
        setStep(1);
        setAlert({ type:"info", msg:"Enter the 6-digit code from your authenticator app." });
      } else {
        localStorage.setItem("access_token", d.access_token);
        setSuccess(true);
        setTimeout(() => { onSuccess?.({ email, token: d.access_token }); onClose?.(); }, 1400);
      }
    } catch(e) {
      setAlert({ type:"error", msg: e.message });
    } finally { setLoading(false); }
  };

  // ── VERIFY MFA ────────────────────────────────────────────────────────────
  const handleVerifyMFA = useCallback(async (code) => {
    const c = code || otp;
    if (c.length < 6) return;
    setLoading(true); clearAlert();
    try {
      const r = await fetch(`${BASE_URL}/verify-mfa`, {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({ email, code: c }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || "Invalid MFA code");
      localStorage.setItem("access_token", d.access_token);
      setSuccess(true);
      setTimeout(() => { onSuccess?.({ email, token: d.access_token }); onClose?.(); }, 1400);
    } catch(e) {
      setAlert({ type:"error", msg: e.message });
      setOtpShake(true); setOtp("");
      setTimeout(() => setOtpShake(false), 500);
    } finally { setLoading(false); }
  }, [email, otp, onSuccess, onClose]);

  // Auto-verify when 6 digits entered
  const handleOtpComplete = (val) => { handleVerifyMFA(val); };

  if (!open) return null;

  const isRegister = mode === "register";
  const mfaStep = isRegister ? 2 : 1;

  const renderStep = () => {
    // ── CREDENTIALS ──────────────────────────────────────────────────────────
    if (step === 0) return (
      <>
        {alert && (
          <div className={`auth-alert ${alert.type}`}>
            <span>{alert.type === "error" ? "⚠" : alert.type === "success" ? "✓" : "ℹ"}</span>
            {alert.msg}
          </div>
        )}
        <div className="auth-field">
          <label className="auth-label">Email address</label>
          <div className="auth-input-wrap">
            <input
              className={`auth-input${alert?.type==="error" ? " error" : ""}`}
              type="email" placeholder="operator@domain.mil"
              value={email} onChange={e => { setEmail(e.target.value); clearAlert(); }}
              onKeyDown={e => e.key==="Enter" && (isRegister ? handleRegister() : handleLogin())}
              autoFocus
            />
            <span className="auth-input-icon">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                <polyline points="22,6 12,13 2,6"/>
              </svg>
            </span>
          </div>
        </div>
        <div className="auth-field">
          <label className="auth-label">Password{isRegister ? " (min 8 chars)" : ""}</label>
          <div className="auth-input-wrap">
            <input
              className={`auth-input${alert?.type==="error" ? " error" : ""}`}
              type={showPass ? "text" : "password"}
              placeholder={isRegister ? "Create a strong password" : "Enter password"}
              value={password} onChange={e => { setPassword(e.target.value); clearAlert(); }}
              onKeyDown={e => e.key==="Enter" && (isRegister ? handleRegister() : handleLogin())}
              style={{ paddingRight: 40 }}
            />
            <button
              className="auth-input-icon"
              onClick={() => setShowPass(p => !p)}
              style={{ background:"none",border:"none",cursor:"pointer",right:12,pointerEvents:"all" }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                {showPass
                  ? <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>
                  : <><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></>
                }
              </svg>
            </button>
          </div>
        </div>

        <button
          className={`auth-btn ${success ? "auth-btn-success" : "auth-btn-primary"}`}
          style={{ marginTop: 8 }}
          onClick={isRegister ? handleRegister : handleLogin}
          disabled={loading || success}
        >
          {loading ? <><div className="auth-spinner"/> AUTHENTICATING…</>
           : success ? "✓ ACCESS GRANTED"
           : isRegister ? "REGISTER & SETUP MFA →" : "LOGIN →"}
        </button>

        <div style={{ textAlign:"center", marginTop:14, fontSize:10, color:"var(--a-text3)" }}>
          {isRegister ? "Already have an account? " : "Need an account? "}
          <button className="auth-switch-link" onClick={() => switchMode(isRegister ? "login" : "register")}>
            {isRegister ? "Sign in" : "Register"}
          </button>
        </div>
      </>
    );

    // ── QR / MFA SETUP (register step 1) ─────────────────────────────────────
    if (isRegister && step === 1) return (
      <>
        {alert && <div className={`auth-alert ${alert.type}`}><span>✓</span>{alert.msg}</div>}
        <div className="auth-qr-wrap">
          {qrCode && (
            <div className="auth-qr-frame">
              <div className="auth-qr-corner tl"/><div className="auth-qr-corner tr"/>
              <div className="auth-qr-corner bl"/><div className="auth-qr-corner br"/>
              <img src={`data:image/png;base64,${qrCode}`} alt="MFA QR Code" width={168} height={168} style={{ display:"block" }}/>
            </div>
          )}
        </div>
        <div className="auth-info-row">
          <strong>Step 1.</strong> Open Google Authenticator, Authy, or any TOTP app.
        </div>
        <div className="auth-info-row">
          <strong>Step 2.</strong> Tap <strong>+</strong> → <strong>Scan QR code</strong> and point it at the code above.
        </div>
        <div className="auth-info-row">
          <strong>Step 3.</strong> Your app will show a 6-digit rotating code. Click continue to verify it.
        </div>

        <button className="auth-btn auth-btn-primary" style={{ marginTop:10 }} onClick={() => { setStep(2); clearAlert(); setAlert({ type:"info", msg:"Enter the 6-digit code shown in your authenticator." }); }}>
          CONTINUE — VERIFY CODE →
        </button>
        <button className="auth-btn auth-btn-ghost" style={{ marginTop:6, fontSize:9 }} onClick={() => setStep(0)}>
          ← BACK
        </button>
      </>
    );

    // ── MFA CODE ENTRY ────────────────────────────────────────────────────────
    if (step === mfaStep) return (
      <>
        {alert && (
          <div className={`auth-alert ${alert.type}`}>
            <span>{alert.type==="error"?"⚠":alert.type==="success"?"✓":"ℹ"}</span>
            {alert.msg}
          </div>
        )}

        <div style={{ textAlign:"center", marginBottom:10 }}>
          <div style={{ fontSize:9, letterSpacing:1.5, color:"var(--a-text3)", textTransform:"uppercase", marginBottom:4 }}>
            {isRegister ? "Verify your authenticator" : "Enter authenticator code"}
          </div>
          <div style={{ fontSize:9, color:"var(--a-text3)" }}>
            6-digit code · refreshes every 30s
          </div>
        </div>

        <OtpInput value={otp} onChange={setOtp} onComplete={handleOtpComplete} shake={otpShake} />

        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginTop:10, fontSize:9, color: timer <= 5 ? "var(--a-red)" : "var(--a-text3)" }}>
          <span>CODE EXPIRES IN</span>
          <span style={{ fontFamily:"var(--a-head)", fontSize:13, color: timer <= 5 ? "var(--a-red)" : timer <= 10 ? "var(--a-amber)" : "var(--a-cyan)", fontWeight:700 }}>
            {String(timer).padStart(2,"0")}s
          </span>
        </div>
        <div className="auth-timer-bar">
          <div className="auth-timer-fill" style={{ width:`${(timer/30)*100}%`, background: timer <= 5 ? "var(--a-red)" : timer <= 10 ? "var(--a-amber)" : "linear-gradient(90deg,var(--a-cyan),var(--a-green))" }}/>
        </div>

        <button
          className={`auth-btn ${success ? "auth-btn-success" : "auth-btn-primary"}`}
          style={{ marginTop:16 }}
          onClick={() => handleVerifyMFA()}
          disabled={otp.length < 6 || loading || success}
        >
          {loading ? <><div className="auth-spinner"/>VERIFYING…</>
           : success ? "✓ ACCESS GRANTED"
           : `VERIFY ${otp.length}/6 →`}
        </button>

        <button className="auth-btn auth-btn-ghost" style={{ marginTop:6, fontSize:9 }} onClick={() => { setStep(isRegister ? 1 : 0); setOtp(""); clearAlert(); }}>
          ← BACK
        </button>
      </>
    );
  };

  return (
    <>
      <style>{AUTH_STYLES}</style>
      <div className="auth-overlay" onClick={e => e.target === e.currentTarget && onClose?.()}>
        <div className="auth-panel">
          {/* Header */}
          <div className="auth-header">
            <div className="auth-header-noise"/>
            <div className="auth-logo-row">
              <div className="auth-logo-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--a-cyan)" strokeWidth="1.5">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0110 0v4"/>
                </svg>
              </div>
              <div>
                <div className="auth-title">PHANTOM AUTH</div>
                <div className="auth-subtitle">
                  {mode === "register" ? "New operator registration" : "Secure operator login"} · MFA enforced
                </div>
              </div>
            </div>
          </div>

          {/* Mode tabs */}
          <div className="auth-tabs">
            <button className={`auth-tab${mode==="login"?" active":""}`} onClick={() => switchMode("login")} disabled={loading}>LOGIN</button>
            <button className={`auth-tab${mode==="register"?" active":""}`} onClick={() => switchMode("register")} disabled={loading}>REGISTER</button>
          </div>

          {/* Body */}
          <div className="auth-body">
            <StepIndicator step={step} mode={mode} />
            {renderStep()}
          </div>

          {/* Footer */}
          <div className="auth-footer">
            <div style={{ display:"flex", alignItems:"center", gap:7 }}>
              <div className="auth-footer-dot"/>
              <span>TLS 1.3 ENCRYPTED</span>
            </div>
            <span>TOTP RFC-6238</span>
            <span>PHANTOM PLATFORM</span>
          </div>

          {/* Close */}
          <button className="auth-close" onClick={onClose}>✕</button>
        </div>
      </div>
    </>
  );
}
