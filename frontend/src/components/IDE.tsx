"use client";
import { useCallback, useRef } from "react";
import { Settings as SettingsIcon, Github, LayoutPanelLeft, Terminal as TermIcon, Zap } from "lucide-react";
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

  const resizeSidebar = useResize(sidebarWidth, setSidebarWidth, "x", 160, 480);
  const resizeChat = useResize(chatWidth, setChatWidth, "x", 260, 600);
  // Pass negated value so dragging up (negative delta) increases terminal height
  const resizeTerminal = useResize(-terminalHeight, (v) => setTerminalHeight(-v), "y", -400, -80);

  const modelInfo = MODELS[modelId];

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

        {/* Active model pill */}
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

        {/* Right buttons */}
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

        {/* Sidebar: File Tree */}
        {sidebarOpen && (
          <>
            <div style={{ width: sidebarWidth, flexShrink: 0, display: "flex", flexDirection: "column", borderRight: "1px solid #2d3748", overflow: "hidden", background: "#0f172a" }}>
              <FileTree />
            </div>

            {/* Resize handle: sidebar */}
            <div
              className="resize-handle resize-handle-x"
              onMouseDown={resizeSidebar}
            />
          </>
        )}

        {/* Center: Editor + Terminal */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", minWidth: 0 }}>
          {/* Editor */}
          <div style={{ flex: 1, overflow: "hidden" }}>
            <CodeEditor />
          </div>

          {/* Terminal */}
          {terminalOpen && (
            <>
              {/* Resize handle: terminal */}
              <div
                className="resize-handle resize-handle-y"
                onMouseDown={resizeTerminal}
              />
              <div style={{ height: terminalHeight, flexShrink: 0, overflow: "hidden", borderTop: "1px solid #2d3748" }}>
                <Terminal />
              </div>
            </>
          )}
        </div>

        {/* Resize handle: chat */}
        <div
          className="resize-handle resize-handle-x"
          onMouseDown={resizeChat}
        />

        {/* Right: AI Agent Chat */}
        <div style={{ width: chatWidth, flexShrink: 0, display: "flex", flexDirection: "column", borderLeft: "1px solid #2d3748", overflow: "hidden", background: "#0f172a" }}>
          <AgentChat />
        </div>
      </div>

      {/* Settings Modal */}
      {showSettings && <Settings />}
    </div>
  );
}
