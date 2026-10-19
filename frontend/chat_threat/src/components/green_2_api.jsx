import React, {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
  } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight"
import APTDashboard from './dash'

import { z } from "zod";

import "highlight.js/styles/github-dark.css";
import { ComposedChart } from "recharts";
  const API_BASE = "http://localhost:8070";
  
  const TERMINAL_THEME = `
  :root{
    --bg:#000000;
    --bg-soft:#020402;
    --bg-panel:rgba(0,255,136,.03);
    --green:#00ff88;
    --green-dim:#00aa55;
    --green-fade:rgba(0,255,136,.08);
    --green-fade-2:rgba(0,255,136,.14);
    --green-glow:0 0 18px rgba(0,255,136,.22);
    --green-strong:0 0 26px rgba(0,255,136,.45);
    --text:#b6ffcf;
    --muted:#4d7a5e;
    --danger:#ff5577;
    --amber:#ffcc66;
    --font:'JetBrains Mono','SFMono-Regular',Consolas,monospace;
  }
  
  *{
    box-sizing:border-box;
    margin:0;
    padding:0;
  }
  
  html,
  body,
  #root{
    width:100%;
    height:100%;
    background:#000;
    overflow:hidden;
  }
  
  body{
    font-family:var(--font);
    background:
      radial-gradient(circle at top, rgba(0,255,136,.06), transparent 40%),
      #000;
    color:var(--text);
  }
  
  ::-webkit-scrollbar{
    width:0;
    height:0;
  }
  
  ::selection{
    background:rgba(0,255,136,.2);
    color:#fff;
  }
  
  @keyframes blink{
    0%,100%{opacity:1;}
    50%{opacity:0;}
  }
  
  @keyframes fade{
    from{
      opacity:0;
      transform:translateY(8px);
    }
    to{
      opacity:1;
      transform:translateY(0);
    }
  }
  
  @keyframes pulse{
    0%,100%{opacity:.3;}
    50%{opacity:1;}
  }
  
  @keyframes scan{
    from{
      transform:translateY(-100%);
    }
    to{
      transform:translateY(100%);
    }
  }
  
  @keyframes noise{
    0%{transform:translateX(0)}
    20%{transform:translateX(-1%)}
    40%{transform:translateX(1%)}
    60%{transform:translateX(-.5%)}
    80%{transform:translateX(.5%)}
    100%{transform:translateX(0)}
  }
  
  @keyframes spin{
    to{
      transform:rotate(360deg);
    }
  }
  `;
  /*
  const BOOT_LINES = [
    "[init] phantom kernel booted",
    "[auth] quantum channel secured",
    "[mesh] vector nodes online",
    "[intel] mitre sync complete",
    "[rag] embeddings mounted",
    "[live] telemetry stream active",
  ];
  */
  
  function useInjectStyles() {
    useEffect(() => {
      const style = document.createElement("style");
      style.innerHTML = TERMINAL_THEME;
      document.head.appendChild(style);
  
      return () => document.head.removeChild(style);
    }, []);
  }
  
  function MatrixRain() {
    const chars =
      "01アイウエオカサタナABCDEFGHIJKLMNOPQRSTUVWXYZ";
  
    const columns = useMemo(() => {
      return new Array(80).fill(0).map((_, i) => ({
        id: i,
        left: `${(i / 80) * 100}%`,
        delay: Math.random() * 8,
        duration: 8 + Math.random() * 10,
        size: 10 + Math.random() * 4,
        content: new Array(30)
          .fill(0)
          .map(
            () =>
              chars[Math.floor(Math.random() * chars.length)]
          )
          .join(" "),
      }));
    }, []);
  
    return (
      <div
        style={{
          position: "absolute",
          inset: 0,
          overflow: "hidden",
          opacity: 0.06,
          pointerEvents: "none",
        }}
      >
        {columns.map((col) => (
          <div
            key={col.id}
            style={{
              position: "absolute",
              top: "-120%",
              left: col.left,
              color: "var(--green)",
              fontSize: col.size,
              lineHeight: 1.1,
              whiteSpace: "pre-wrap",
              animation: `scan ${col.duration}s linear infinite`,
              animationDelay: `${col.delay}s`,
              textShadow: "0 0 8px rgba(0,255,136,.5)",
            }}
          >
            {col.content}
          </div>
        ))}
      </div>
    );
  }
  

 

  function BootSequence() {
    const [visible, setVisible] = useState(0);
  
    useEffect(() => {
      const t = setInterval(() => {
        setVisible((v) => {
          if (v >= BOOT_LINES.length) {
            clearInterval(t);
            return v;
          }
  
          return v + 1;
        });
      }, 220);
  
      return () => clearInterval(t);
    }, []);
  
    
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 8,
          marginBottom: 24,
        }}
      >
        {BOOT_LINES.slice(0, visible).map((line, i) => (
          <div
            key={i}
            style={{
              color:
                i === BOOT_LINES.length - 1
                  ? "var(--green)"
                  : "var(--muted)",
              fontSize: 12,
              letterSpacing: 1.5,
              animation: "fade .3s ease forwards",
              textShadow: "0 0 10px rgba(0,255,136,.18)",
            }}
          >
            {line}
          </div>
        ))}
      </div>
    );
  }
  
  function StatusBar({ vectorCount }) {
    const [time, setTime] = useState("");
  
    useEffect(() => {
      const update = () => {
        setTime(
          new Date().toLocaleTimeString("en-GB", {
            hour12: false,
          })
        );
      };
  
      update();
  
      const t = setInterval(update, 1000);
  
      return () => clearInterval(t);
    }, []);
  
    return (
      <div
        style={{
          position: "absolute",
          top: 26,
          left: 42,
          right: 42,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: 11,
          color: "var(--muted)",
          letterSpacing: 2,
          zIndex: 20,
        }}
      >
        <div
          style={{
            display: "flex",
            gap: 18,
          }}
        >
          <span>PHANTOM_OS</span>
          <span>NODE::ACTIVE</span>
          <span>RAG::{vectorCount.toLocaleString()}</span>
        </div>
  
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 18,
          }}
        >
          <span>{time}</span>
  
          <div
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: "var(--green)",
              boxShadow: "var(--green-strong)",
              animation: "pulse 1.2s infinite",
            }}
          />
        </div>
      </div>
    );
  }
  
  function UploadButton({ onClick, vectorCount }) {
    return (
      <button
        onClick={onClick}
        style={{
          width: 52,
          height: 52,
          borderRadius: 10,
          border: "1px solid var(--green-fade-2)",
          background: "rgba(0,255,136,.04)",
          color: "var(--green)",
          cursor: "pointer",
          position: "relative",
          transition: ".2s",
          boxShadow: "var(--green-glow)",
        }}
      >
        📡
  
        {vectorCount > 0 && (
          <div
            style={{
              position: "absolute",
              top: -6,
              right: -6,
              minWidth: 18,
              height: 18,
              padding: "0 4px",
              borderRadius: 999,
              background: "var(--green)",
              color: "#000",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 9,
              fontWeight: 700,
            }}
          >
            {vectorCount > 99 ? "99+" : vectorCount}
          </div>
        )}
      </button>
    );
  }
  
  function UploadModal({
    open,
    onClose,
    onUploaded,
  }) {
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
  
    const inputRef = useRef(null);
  
    if (!open) return null;
  
    const uploadAll = async () => {
      if (!files.length) return;
  
      setUploading(true);
  
      for (const file of files) {
        try {
          const fd = new FormData();
  
          fd.append("file", file);
  
          const res = await fetch(
            `${API_BASE}/upload_pcap`,
            {
              method: "POST",
              body: fd,
            }
          );
  
          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
          }
  
          const data = await res.json();
  
          onUploaded({
            name: file.name,
            packets: data.packets || 0,
          });
        } catch (err) {
          console.error(err);
        }
      }
  
      setUploading(false);
      setFiles([]);
      onClose();
    };
  
    return (
      <div
        onClick={(e) => {
          if (e.target === e.currentTarget) onClose();
        }}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,.82)",
          backdropFilter: "blur(8px)",
          zIndex: 999,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div
          style={{
            width: 560,
            border: "1px solid var(--green-fade-2)",
            background: "#020402",
            borderRadius: 14,
            padding: 24,
            boxShadow: "0 0 60px rgba(0,255,136,.15)",
          }}
        >
          <div
            style={{
              fontSize: 14,
              color: "var(--green)",
              marginBottom: 22,
              letterSpacing: 2,
            }}
          >
            PCAP VECTOR INGEST
          </div>
  
          <div
            onClick={() => inputRef.current?.click()}
            style={{
              border: "1px dashed rgba(0,255,136,.35)",
              borderRadius: 12,
              padding: "46px 24px",
              textAlign: "center",
              cursor: "pointer",
              background: "rgba(0,255,136,.03)",
            }}
          >
            <input
              ref={inputRef}
              type="file"
              multiple
              accept=".pcap,.cap"
              style={{ display: "none" }}
              onChange={(e) =>
                setFiles(Array.from(e.target.files))
              }
            />
  
            <div
              style={{
                fontSize: 42,
                marginBottom: 12,
              }}
            >
              ⬆
            </div>
  
            <div
              style={{
                color: "var(--green)",
                fontSize: 13,
                letterSpacing: 2,
              }}
            >
              DROP OR SELECT PCAP FILES
            </div>
  
            <div
              style={{
                marginTop: 10,
                color: "var(--muted)",
                fontSize: 11,
              }}
            >
              FAISS · OLLAMA · RAG PIPELINE
            </div>
          </div>
  
          {!!files.length && (
            <div
              style={{
                marginTop: 18,
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }}
            >
              {files.map((f, i) => (
                <div
                  key={i}
                  style={{
                    padding: "10px 12px",
                    border: "1px solid var(--green-fade)",
                    borderRadius: 8,
                    background: "rgba(0,255,136,.03)",
                    color: "var(--text)",
                    fontSize: 12,
                  }}
                >
                  {f.name}
                </div>
              ))}
            </div>
          )}
  
          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              gap: 10,
              marginTop: 22,
            }}
          >
            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: "1px solid var(--green-fade)",
                color: "var(--muted)",
                padding: "10px 18px",
                borderRadius: 8,
                cursor: "pointer",
                fontFamily: "var(--font)",
              }}
            >
              CANCEL
            </button>
  
            <button
              onClick={uploadAll}
              disabled={uploading}
              style={{
                background: "var(--green)",
                border: "none",
                color: "#000",
                padding: "10px 22px",
                borderRadius: 8,
                cursor: "pointer",
                fontWeight: 700,
                fontFamily: "var(--font)",
                boxShadow: "var(--green-strong)",
              }}
            >
              {uploading
                ? "INGESTING..."
                : "INGEST"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  const UI_REGISTRY = {
    APTDashboard: {
      component: APTDashboard,
      schema: z.object({
        severity: z.string(),
        src_ip: z.string(),
        campaign: z.string(),
      }),
    },
  };
  
  function TerminalMessage({ role, content, toolCalls = [], }) {
    return (
      <div
        style={{
          display: "flex",
          gap: 18,
          width: "100%",
          alignItems: "flex-start",
          animation: "fade .25s ease",
        }}
      >
        <div
          style={{
            width: 82,
            flexShrink: 0,
            color: role === "user" ? "var(--muted)" : "var(--green)",
            letterSpacing: 2,
            fontSize: 10,
            paddingTop: 3,
            textTransform: "uppercase",
            textShadow:
              role === "assistant"
                ? "0 0 14px rgba(0,255,136,.35)"
                : "none",
          }}
        >
          {role === "user" ? "Operator" : "PHANTOM"}
        </div>
  
        <div
          style={{
            flex: 1,
            color:
              role === "assistant"
                ? "var(--text)"
                : "#d8ffe8",
            fontSize: 13,
            lineHeight: 1.85,
            wordBreak: "break-word",
            textAlign: "left",
            paddingBottom: 4,
            textShadow:
              role === "assistant"
                ? "0 0 10px rgba(0,255,136,.06)"
                : "0 0 10px rgba(255,255,255,.04)",
          }}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              p: ({ children }) => (
                <p
                  style={{
                    marginBottom: 12,
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {children}
                </p>
              ),
  
              h1: ({ children }) => (
                <h1
                  style={{
                    color: "var(--green)",
                    fontSize: 24,
                    margin: "18px 0 12px",
                  }}
                >
                  {children}
                </h1>
              ),
  
              h2: ({ children }) => (
                <h2
                  style={{
                    color: "var(--green)",
                    fontSize: 20,
                    margin: "16px 0 10px",
                  }}
                >
                  {children}
                </h2>
              ),
  
              h3: ({ children }) => (
                <h3
                  style={{
                    color: "var(--green)",
                    fontSize: 16,
                    margin: "14px 0 8px",
                  }}
                >
                  {children}
                </h3>
              ),
  
              code({
                inline,
                className,
                children,
                ...props
              }) {
                if (inline) {
                  return (
                    <code
                      style={{
                        background:
                          "rgba(0,255,136,.08)",
                        color: "#00ff88",
                        padding: "2px 6px",
                        borderRadius: 6,
                        fontSize: 12,
                      }}
                      {...props}
                    >
                      {children}
                    </code>
                  );
                }
  
                return (
                  <pre
                    style={{
                      background: "#050805",
                      border:
                        "1px solid rgba(0,255,136,.12)",
                      padding: 16,
                      borderRadius: 12,
                      overflowX: "auto",
                      margin: "14px 0",
                      boxShadow:
                        "0 0 20px rgba(0,255,136,.05)",
                    }}
                  >
                    <code
                      className={className}
                      {...props}
                    >
                      {children}
                    </code>
                  </pre>
                );
              },
  
              blockquote: ({ children }) => (
                <blockquote
                  style={{
                    borderLeft:
                      "3px solid var(--green)",
                    paddingLeft: 14,
                    margin: "12px 0",
                    color: "var(--muted)",
                  }}
                >
                  {children}
                </blockquote>
              ),
  
              ul: ({ children }) => (
                <ul
                  style={{
                    paddingLeft: 22,
                    marginBottom: 12,
                  }}
                >
                  {children}
                </ul>
              ),
  
              ol: ({ children }) => (
                <ol
                  style={{
                    paddingLeft: 22,
                    marginBottom: 12,
                  }}
                >
                  {children}
                </ol>
              ),
  
              li: ({ children }) => (
                <li
                  style={{
                    marginBottom: 6,
                  }}
                >
                  {children}
                </li>
              ),
  
              a: ({ href, children }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    color: "#00ffaa",
                    textDecoration: "none",
                  }}
                >
                  {children}
                </a>
              ),
  
              table: ({ children }) => (
                <table
                  style={{
                    width: "100%",
                    borderCollapse: "collapse",
                    margin: "14px 0",
                  }}
                >
                  {children}
                </table>
              ),
  
              th: ({ children }) => (
                <th
                  style={{
                    border:
                      "1px solid rgba(0,255,136,.15)",
                    padding: 10,
                    background:
                      "rgba(0,255,136,.05)",
                    color: "var(--green)",
                  }}
                >
                  {children}
                </th>
              ),
  
              td: ({ children }) => (
                <td
                  style={{
                    border:
                      "1px solid rgba(0,255,136,.08)",
                    padding: 10,
                  }}
                >
                  {children}
                </td>
              ),
            }}
          >
     
      
            {content}
          </ReactMarkdown>
          {toolCalls.map((tool, i) => {
    const Component =
      UI_REGISTRY[tool.component];

    if (!Component) return null;

    return (
      <div key={i}>
        <Component {...tool.props} />
      </div>
    );
  })}
  
    </div>
        </div>
  
    );
  }
  
  function TypeInput({
    value,
    setValue,
    onSend,
    loading,
    onUpload,
    vectorCount,
  }) {
    const textareaRef = useRef(null);
  
    useEffect(() => {
      if (!textareaRef.current) return;
  
      textareaRef.current.style.height = "0px";
      textareaRef.current.style.height =
        textareaRef.current.scrollHeight + "px";
    }, [value]);
  
    return (
      <div
        style={{
          borderTop: "1px solid rgba(0,255,136,.08)",
          paddingTop: 18,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "flex-end",
            gap: 14,
          }}
        >
          <UploadButton
            onClick={onUpload}
            vectorCount={vectorCount}
          />
  
          <div
            style={{
              flex: 1,
              border: "1px solid rgba(0,255,136,.12)",
              background: "rgba(0,255,136,.02)",
              borderRadius: 14,
              padding: "14px 18px",
              boxShadow: "var(--green-glow)",
            }}
          >
            <textarea
              ref={textareaRef}
              rows={1}
              spellCheck={false}
              value={value}
              onChange={(e) =>
                setValue(e.target.value)
              }
              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  !e.shiftKey
                ) {
                  e.preventDefault();
                  onSend();
                }
              }}
              placeholder={
                vectorCount > 0
                  ? `query ${vectorCount.toLocaleString()} indexed vectors...`
                  : "query intelligence stream..."
              }
              style={{
                width: "100%",
                background: "transparent",
                border: "none",
                outline: "none",
                resize: "none",
                overflow: "hidden",
                color: "var(--green)",
                fontFamily: "var(--font)",
                fontSize: 14,
                lineHeight: 1.8,
                maxHeight: 240,
                caretColor: "var(--green)",
              }}
            />
  
            <div
              style={{
                display: "flex",
                justifyContent:
                  "space-between",
                marginTop: 10,
                fontSize: 10,
                color: "var(--muted)",
                letterSpacing: 2,
              }}
            >
              <span>
                ENTER :: EXECUTE
              </span>
  
              <span>
                SHIFT+ENTER :: NEWLINE
              </span>
            </div>
          </div>
  
          <button
            disabled={!value.trim() || loading}
            onClick={onSend}
            style={{
              width: 56,
              height: 56,
              borderRadius: 12,
              border:
                "1px solid rgba(0,255,136,.18)",
              background:
                loading || !value.trim()
                  ? "rgba(0,255,136,.03)"
                  : "rgba(0,255,136,.1)",
              color: "var(--green)",
              cursor:
                loading || !value.trim()
                  ? "default"
                  : "pointer",
              boxShadow:
                loading || !value.trim()
                  ? "none"
                  : "var(--green-strong)",
            }}
          >
            {loading ? (
              <div
                style={{
                  width: 18,
                  height: 18,
                  border:
                    "2px solid rgba(0,255,136,.2)",
                  borderTop:
                    "2px solid var(--green)",
                  borderRadius: "50%",
                  animation:
                    "spin .7s linear infinite",
                  margin: "0 auto",
                }}
              />
            ) : (
              "➜"
            )}
          </button>
        </div>
      </div>
    );
  }
  function ModelSelector({
    models,
    selected,
    onChange,
  }) {
    return (
      <div style={{
        display: "flex",
        gap: 10,
        marginBottom: 14,
        alignItems: "center",
        color: "var(--muted)",
        fontSize: 11,
        letterSpacing: 2,
      }}>
        <span>MODEL::</span>
  
        <select
          value={selected || ""}
          onChange={(e) => onChange(e.target.value)}
          style={{
            background: "rgba(0,255,136,.05)",
            border: "1px solid rgba(0,255,136,.2)",
            color: "var(--green)",
            padding: "6px 10px",
            borderRadius: 6,
            fontFamily: "var(--font)",
            outline: "none",
          }}
        >
          {models.map((m) => (
            <option key={m.id} value={m.id}>
              {m.label || m.id} [{m.provider}]
            </option>
          ))}
        </select>
  
        {selected && (
          <span style={{ color: "var(--green)" }}>
            ACTIVE
          </span>
        )}
      </div>
    );
  }
  
  export default function PhantomTerminalUI({
    user,
    db,
  }) {
    useInjectStyles();
    const [generatedUi, setGeneratedUi] = useState(null);
    const [models, setModels] = useState([]);
    const [selectedModel, setSelectedModel] = useState(null);
    const [loading, setLoading] =
      useState(false);
  
    const [input, setInput] = useState("");
  
    const [showUpload, setShowUpload] =
      useState(false);
  
    const [vectorCount, setVectorCount] =
      useState(0);
  
    const sessionId = useMemo(() => {
      return `${
        user?.uid?.slice(0, 8) || "anon"
      }_${Date.now().toString(36)}`;
    }, [user]);
  
    const [messages, setMessages] = useState([
      {
        id: "boot",
        role: "assistant",
        content:
""
    },
    ]);
    const renderGenerativeUi = () => {
        if (!generatedUi || !UI_REGISTRY[generatedUi.component]) return null;
        
        // ✅ CORRECT: Resolve and instantiate dynamically during render
        const ComponentToRender = UI_REGISTRY[generatedUi.component];
        return <ComponentToRender {...generatedUi.props} />;
      };
    const containerRef = useRef(null);
  
    useEffect(() => {
      containerRef.current?.scrollTo({
        top:
          containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }, [messages]);
    useEffect(() => {
      const loadModels = async () => {
        try {
          const res = await fetch(`${API_BASE}/api/models`);
          const data = await res.json();
    
          setModels(data.models || []);
          setSelectedModel(data.default || data.models?.[0]?.id);
        } catch (err) {
          console.error("model fetch failed", err);
        }
      };
    
      loadModels();
    }, []);
    useEffect(() => {
      const poll = async () => {
        try {
          const res = await fetch(
            `${API_BASE}/health`
          );
  
          if (!res.ok) return;
  
          const data = await res.json();
  
          setVectorCount(
            data.vectors || 0
          );
        } catch {}
      };
  
      poll();
  
      const t = setInterval(poll, 10000);
  
      return () => clearInterval(t);
    }, []);
  
    const handleUploaded = useCallback(
      (result) => {
        setVectorCount(
          (prev) =>
            prev + (result.packets || 0)
        );
  
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            role: "assistant",
            content:
              `pcap ingested successfully.\n\n` +
              `file :: ${result.name}\n` +
              `vectors :: ${result.packets}\n\n` +
              `rag index updated.\n` +
              `telemetry query available.`,
          },
        ]);
      },
      []
    );
  
    const send = useCallback(async () => {
      const text = input.trim();
  
      if (!text || loading) return;
  
      setInput("");
  
      const userMessage = {
        id: Date.now().toString(),
        role: "user",
        content: text,
      };
  
      const botId =
        (Date.now() + 1).toString();
  
      setMessages((prev) => [
        ...prev,
        userMessage,
        {
          id: botId,
          role: "assistant",
          content: "",
          streaming: true,
          tool_calls: [],
        },
      ]);
  
      setLoading(true);
  
      try {
        if (db && user) {
          db.push(
            `users/${user.uid}/chat`,
            {
              role: "user",
              content: text,
              ts: new Date().toISOString(),
            }
          );
        }
  
        const response = await fetch(
          `${API_BASE}/chat`,
          {
            method: "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body: JSON.stringify({
              message: text,
              session_id: sessionId,
            }),
          }
        );
  
        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}`
          );
        }
  
        const reader =
          response.body.getReader();
  
        const decoder =
          new TextDecoder();
  
        let buffer = "";
  
        const updateMessage = (fn) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === botId ? fn(m) : m
            )
          );
        };
  
        while (true) {
          const {
            done,
            value,
          } = await reader.read();
  
          if (done) break;
  
          buffer += decoder.decode(value, {
            stream: true,
          });
  
          const chunks =
            buffer.split(/\n\n/);
  
          buffer = chunks.pop() || "";
  
          for (const chunk of chunks) {
            if (!chunk.trim()) continue;
  
            let eventType = "message";
  
            const dataLines = [];
  
            for (const line of chunk.split(
              "\n"
            )) {
              if (
                line.startsWith("event:")
              ) {
                eventType = line
                  .slice(6)
                  .trim();
              }
  
              if (
                line.startsWith("data:")
              ) {
                dataLines.push(
                  line.slice(5).trim()
                );
              }
            }
  
            if (!dataLines.length)
              continue;
  
            let payload = {};
  
            try {
              payload = JSON.parse(
                dataLines.join("\n")
              );
            } catch {
              continue;
            }
  
            if (
              eventType === "token"
            ) {
              updateMessage((m) => ({
                ...m,
                content:
                  m.content +
                  (payload.text || ""),
              }));
            }
  
            if (
              eventType === "tool_call"
            ) {
              updateMessage((m) => ({
                ...m,
                tool_calls: [
                  ...(m.tool_calls || []),
                  payload,
                ],
              }));
            }
  
            if (
              eventType === "done"
            ) {
              updateMessage((m) => ({
                ...m,
                streaming: false,
                content:
                  payload.content ||
                  m.content,
              }));
            }
  
            if (
              eventType === "error"
            ) {
              updateMessage((m) => ({
                ...m,
                streaming: false,
                content: `error :: ${payload.message}`,
              }));
            }
          }
        }
  
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botId
              ? {
                  ...m,
                  streaming: false,
                }
              : m
          )
        );
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === botId
              ? {
                  ...m,
                  streaming: false,
                  content: `connection failure :: ${err.message}`,
                }
              : m
          )
        );
      } finally {
        setLoading(false);
      }
    }, [
      input,
      loading,
      sessionId,
      db,
      user,
    ]);
  
    return (
      <div
        style={{
          width: "100%",
          height: "100vh",
          background: "#000",
          position: "relative",
          overflow: "hidden",
        }}
      >
        <MatrixRain />
  
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "linear-gradient(rgba(0,255,136,.025) 1px, transparent 1px)",
            backgroundSize: "100% 4px",
            mixBlendMode: "screen",
            opacity: 0.18,
            pointerEvents: "none",
            animation:
              "noise .18s infinite",
          }}
        />
  
        <StatusBar
          vectorCount={vectorCount}
        />
  
        <UploadModal
          open={showUpload}
          onClose={() =>
            setShowUpload(false)
          }
          onUploaded={handleUploaded}
        />
  
        <div
          style={{
            position: "relative",
            zIndex: 2,
            width: "100%",
            height: "100%",
            padding:
              "82px 42px 34px",
            display: "flex",
            flexDirection: "column",
          }}
        >
          
  
          <div
  ref={containerRef}
  style={{
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: 28,
    padding: "28px",
    border: "1px solid rgba(0,255,136,.08)",
    background: "rgba(0,255,136,.015)",
    boxShadow: "inset 0 0 80px rgba(0,255,136,.02)",
    backdropFilter: "blur(10px)",
    borderRadius: 18,
    position: "relative",
  }}
>
            {messages.map((message) => (
              <TerminalMessage
                key={message.id}
                role={message.role}
                content={
                  message.content
                }
                toolCalls={
                  message.tool_calls
                }
              />
            ))}
  
            {loading && (
              <div
                style={{
                  display: "flex",
                  gap: 18,
                  animation:
                    "fade .25s ease",
                }}
              >
                <div
                  style={{
                    width: 84,
                    color:
                      "var(--green)",
                    fontSize: 11,
                    letterSpacing: 2,
                  }}
                >
                  PHANTOM
                </div>
  
                <div
                  style={{
                    display: "flex",
                    alignItems:
                      "left-align",
                    gap: 8,
                    color:
                      "var(--green)",
                  }}
                >
                  {[0, 1, 2].map(
                    (i) => (
                      <div
                        key={i}
                        style={{
                          width: 4,
                          height: 4,
                          borderRadius:
                            "50%",
                          background:
                            "var(--green)",
                          boxShadow:
                            "0 0 10px rgba(0,255,136,.7)",
                          animation: `pulse 1s infinite ${
                            i * 0.2
                          }s`,
                        }}
                      />
                    )
                  )}
  
                  <span
                    style={{
                      fontSize: 12,
                      letterSpacing: 2,
                      color:
                        "var(--muted)",
                      marginLeft: 10,
                    }}
                  >
                    STREAMING
                  </span>
                </div>
              </div>
            )}
          </div>

          <ModelSelector
  models={models}
  selected={selectedModel}
  onChange={setSelectedModel}
/>
  
          <TypeInput
            value={input}
            setValue={setInput}
            onSend={send}
            loading={loading}
            onUpload={() =>
              setShowUpload(true)
            }
            vectorCount={vectorCount}
          />
        </div>
      </div>
    );
  }