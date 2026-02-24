"use client";
import { useCallback, useRef, useEffect, useState } from "react";
import { Settings as SettingsIcon, LayoutPanelLeft, Terminal as TermIcon, Zap, MessageSquare, Code2, FolderOpen } from "lucide-react";
import { useIDEStore } from "@/store/ide";
import { MODELS } from "@/lib/types";
import FileTree from "./FileTree";
import CodeEditor from "./CodeEditor";
import AgentChat from "./AgentChat";
import Terminal from "./Terminal";
import Settings from "./Settings";

function useResize(
  currentValue: number,
  setter: (v: number) => void,
  direction: "x" | "y",
  min: number,
  max: number
) {
  const dragging = useRef(false);
  const startPos = useRef(0);
  const valRef = useRef(currentValue);
  valRef.current = currentValue;

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    dragging.current = true;
    startPos.current = direction === "x" ? e.clientX : e.clientY;
    document.body.style.cursor = direction === "x" ? "col-resize" : "row-resize";
    document.body.style.userSelect = "none";

    const onMouseMove = (ev: MouseEvent) => {
      if (!dragging.current) return;
      const delta = (direction === "x" ? ev.clientX : ev.clientY) - startPos.current;
      const next = Math.max(min, Math.min(max, valRef.current + delta));
      valRef.current = next;
      setter(next);
      startPos.current = direction === "x" ? ev.clientX : ev.clientY;
    };
    const onMouseUp = () => {
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  }, [setter, direction, min, max]);

  return onMouseDown;
}

type MobileTab = "chat" | "editor" | "files" | "terminal";

export default function IDE() {
  const {
    sidebarOpen, toggleSidebar,
    sidebarWidth, setSidebarWidth,
    chatWidth, setChatWidth,
    terminalHeight, setTerminalHeight,
    terminalOpen, toggleTerminal,
    showSettings, toggleSettings,
    modelId,
  } = useIDEStore();

  const [isMobile, setIsMobile] = useState(false);
  const [mobileTab, setMobileTab] = useState<MobileTab>("chat");

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  const resizeSidebar = useResize(sidebarWidth, setSidebarWidth, "x", 160, 480);
  const resizeChat = useResize(chatWidth, setChatWidth, "x", 260, 600);
  const resizeTerminal = useResize(-terminalHeight, (v) => setTerminalHeight(-v), "y", -400, -80);

  const modelInfo = MODELS[modelId];

  /* ─── MOBILE LAYOUT ────────────────────────────────────────────────── */
  if (isMobile) {
    const TAB_H = 56;

    const tabs: { id: MobileTab; icon: React.ReactNode; label: string }[] = [
      { id: "chat",     icon: <MessageSquare size={20} />, label: "Chat" },
      { id: "editor",  icon: <Code2 size={20} />,         label: "Kod" },
      { id: "files",   icon: <FolderOpen size={20} />,    label: "Dosyalar" },
      { id: "terminal",icon: <TermIcon size={20} />,       label: "Terminal" },
    ];

    return (
      <div style={{ display: "flex", flexDirection: "column", height: "100dvh", overflow: "hidden", background: "#0f172a" }}>
        {/* Top bar — slim mobile version */}
        <div style={{
          display: "flex", alignItems: "center", gap: 8, padding: "0 12px",
          height: 44, borderBottom: "1px solid #2d3748", flexShrink: 0,
          background: "#0f172a",
        }}>
          <Zap size={16} color="#6366f1" />
          <span style={{ fontWeight: 700, fontSize: 14, color: "#f8fafc", flex: 1 }}>AI IDE</span>
          {modelInfo && (
            <div style={{
              display: "flex", alignItems: "center", gap: 4,
              background: "#1e293b", border: "1px solid #334155", borderRadius: 8,
              padding: "2px 8px", fontSize: 11,
            }}>
              <span>{modelInfo.icon}</span>
              <span style={{ color: "#e2e8f0" }}>{modelInfo.short}</span>
              {modelInfo.free && <span style={{ color: "#10b981", fontSize: 9, fontWeight: 700 }}>FREE</span>}
            </div>
          )}
          <button
            onClick={toggleSettings}
            style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", padding: 4 }}
          >
            <SettingsIcon size={16} />
          </button>
        </div>

        {/* Content — full height minus top + bottom bar */}
        <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>
          <div style={{ display: mobileTab === "chat"     ? "flex" : "none", flexDirection: "column", height: "100%", overflow: "hidden" }}>
            <AgentChat />
          </div>
          <div style={{ display: mobileTab === "editor"   ? "flex" : "none", flexDirection: "column", height: "100%", overflow: "hidden" }}>
            <CodeEditor />
          </div>
          <div style={{ display: mobileTab === "files"    ? "flex" : "none", flexDirection: "column", height: "100%", overflow: "hidden" }}>
            <FileTree />
          </div>
          <div style={{ display: mobileTab === "terminal" ? "flex" : "none", flexDirection: "column", height: "100%", overflow: "hidden" }}>
            <Terminal />
          </div>
        </div>

        {/* Bottom tab bar */}
        <div style={{
          display: "flex", height: TAB_H, flexShrink: 0,
          borderTop: "1px solid #2d3748", background: "#0f172a",
        }}>
          {tabs.map((tab) => {
            const active = mobileTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setMobileTab(tab.id)}
                style={{
                  flex: 1, display: "flex", flexDirection: "column",
                  alignItems: "center", justifyContent: "center", gap: 3,
                  background: active ? "rgba(99,102,241,0.12)" : "none",
                  border: "none", cursor: "pointer",
                  color: active ? "#a5b4fc" : "#4b5563",
                  borderTop: active ? "2px solid #6366f1" : "2px solid transparent",
                  fontSize: 10, fontWeight: active ? 700 : 400,
                  transition: "color 0.15s",
                }}
              >
                {tab.icon}
                {tab.label}
              </button>
            );
          })}
        </div>

        {showSettings && <Settings />}
      </div>
    );
  }

  /* ─── DESKTOP LAYOUT ───────────────────────────────────────────────── */
  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden", background: "#0f172a" }}>
      {/* ── Top Bar ─────────────────────────────────────────────────────────── */}
      <div style={{
        display: "flex", alignItems: "center", gap: 10, padding: "0 14px",
        height: 42, borderBottom: "1px solid #2d3748", flexShrink: 0,
        background: "#0f172a",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <Zap size={18} color="#6366f1" />
          <span style={{ fontWeight: 700, fontSize: 14, color: "#f8fafc" }}>AI IDE</span>
        </div>

        <div style={{ height: 20, width: 1, background: "#2d3748" }} />

        {modelInfo && (
          <div style={{
            display: "flex", alignItems: "center", gap: 5,
            background: "#1e293b", border: "1px solid #334155", borderRadius: 8,
            padding: "3px 10px", fontSize: 12,
          }}>
            <span>{modelInfo.icon}</span>
            <span style={{ color: "#e2e8f0" }}>{modelInfo.short}</span>
            {modelInfo.free && <span style={{ color: "#10b981", fontSize: 10, fontWeight: 700 }}>FREE</span>}
          </div>
        )}

        <div style={{ flex: 1 }} />

        <button
          onClick={toggleSidebar}
          title="Dosya Gezgini"
          style={{
            background: sidebarOpen ? "rgba(99,102,241,0.15)" : "none",
            border: "1px solid " + (sidebarOpen ? "#6366f1" : "transparent"),
            borderRadius: 8, padding: "4px 8px", cursor: "pointer",
            color: sidebarOpen ? "#a5b4fc" : "#94a3b8", display: "flex", alignItems: "center", gap: 4, fontSize: 12,
          }}
        >
          <LayoutPanelLeft size={14} /> Gezgin
        </button>

        <button
          onClick={toggleTerminal}
          title="Terminal"
          style={{
            background: terminalOpen ? "rgba(99,102,241,0.15)" : "none",
            border: "1px solid " + (terminalOpen ? "#6366f1" : "transparent"),
            borderRadius: 8, padding: "4px 8px", cursor: "pointer",
            color: terminalOpen ? "#a5b4fc" : "#94a3b8", display: "flex", alignItems: "center", gap: 4, fontSize: 12,
          }}
        >
          <TermIcon size={14} /> Terminal
        </button>

        <button
          onClick={toggleSettings}
          title="API Anahtarları & Ayarlar"
          style={{
            background: "none", border: "1px solid #334155", borderRadius: 8,
            padding: "4px 8px", cursor: "pointer", color: "#94a3b8",
            display: "flex", alignItems: "center", gap: 4, fontSize: 12,
          }}
        >
          <SettingsIcon size={14} /> Ayarlar
        </button>
      </div>

      {/* ── Main Layout ──────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>

        {sidebarOpen && (
          <>
            <div style={{ width: sidebarWidth, flexShrink: 0, display: "flex", flexDirection: "column", borderRight: "1px solid #2d3748", overflow: "hidden", background: "#0f172a" }}>
              <FileTree />
            </div>
            <div className="resize-handle resize-handle-x" onMouseDown={resizeSidebar} />
          </>
        )}

        {/* Center: Editor + Terminal */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
          <div style={{ flex: 1, overflow: "hidden" }}>
            <CodeEditor />
          </div>

          {terminalOpen && (
            <>
              <div className="resize-handle resize-handle-y" onMouseDown={resizeTerminal} />
              <div style={{ height: terminalHeight, flexShrink: 0, overflow: "hidden", borderTop: "1px solid #2d3748" }}>
                <Terminal />
              </div>
            </>
          )}
        </div>

        <div className="resize-handle resize-handle-x" onMouseDown={resizeChat} />

        <div style={{ width: chatWidth, flexShrink: 0, display: "flex", flexDirection: "column", borderLeft: "1px solid #2d3748", overflow: "hidden", background: "#0f172a" }}>
          <AgentChat />
        </div>
      </div>

      {showSettings && <Settings />}
    </div>
  );
}
