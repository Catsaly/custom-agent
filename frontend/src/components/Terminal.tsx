"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { Terminal as TermIcon, Trash2, ChevronDown, ChevronUp } from "lucide-react";
import { useIDEStore } from "@/store/ide";
import { streamTerminal } from "@/lib/api";

export default function Terminal() {
  const {
    workspace, terminalOpen, toggleTerminal,
    terminalLines, pushTerminalLine, clearTerminalLines,
  } = useIDEStore();

  const [input, setInput] = useState("");
  const [running, setRunning] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [histIdx, setHistIdx] = useState(-1);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [terminalLines]);

  const run = useCallback((cmd: string) => {
    if (!cmd.trim() || running) return;
    setInput("");
    setRunning(true);
    setHistory((h) => [cmd, ...h.slice(0, 49)]);
    setHistIdx(-1);
    pushTerminalLine({ text: `$ ${cmd}`, type: "cmd" });

    abortRef.current = streamTerminal(
      cmd,
      workspace,
      (line) => pushTerminalLine({ text: line, type: "output" }),
      (code) => {
        if (code !== 0) pushTerminalLine({ text: `Exit code: ${code}`, type: "error" });
        setRunning(false);
      },
    );
  }, [running, workspace, pushTerminalLine]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") { run(input); return; }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      const idx = Math.min(histIdx + 1, history.length - 1);
      setHistIdx(idx);
      setInput(history[idx] ?? "");
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      const idx = Math.max(histIdx - 1, -1);
      setHistIdx(idx);
      setInput(idx === -1 ? "" : history[idx] ?? "");
    }
    if (e.key === "c" && e.ctrlKey) {
      abortRef.current?.abort();
      pushTerminalLine({ text: "^C", type: "error" });
      setRunning(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#020817" }}>
      {/* Header */}
      <div style={{
        display: "flex", alignItems: "center", gap: 6, padding: "4px 10px",
        borderBottom: "1px solid #2d3748", flexShrink: 0, background: "#0f172a",
      }}>
        <TermIcon size={14} color="#94a3b8" />
        <span style={{ fontSize: 12, color: "#94a3b8", fontWeight: 600, flex: 1 }}>Terminal</span>
        <span style={{ fontSize: 11, color: "#4b5563" }}>{workspace}</span>
        <button
          onClick={clearTerminalLines}
          title="Temizle"
          style={{ background: "none", border: "none", cursor: "pointer", color: "#4b5563", padding: 2 }}
        >
          <Trash2 size={12} />
        </button>
        <button
          onClick={toggleTerminal}
          style={{ background: "none", border: "none", cursor: "pointer", color: "#4b5563", padding: 2 }}
        >
          {terminalOpen ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>
      </div>

      {terminalOpen && (
        <>
          {/* Output */}
          <div
            ref={scrollRef}
            style={{ flex: 1, overflowY: "auto", padding: "6px 12px", fontFamily: "JetBrains Mono, monospace", fontSize: 12 }}
          >
            {terminalLines.map((line, i) => (
              <div
                key={i}
                style={{
                  color: line.type === "cmd" ? "#a5b4fc"
                    : line.type === "error" ? "#f87171"
                    : line.type === "info" ? "#6b7280"
                    : "#d1fae5",
                  whiteSpace: "pre-wrap", wordBreak: "break-all", lineHeight: 1.5,
                }}
              >
                {line.text}
              </div>
            ))}
            {running && (
              <div className="animate-pulse" style={{ color: "#6366f1", fontSize: 12 }}>▊</div>
            )}
          </div>

          {/* Input */}
          <div style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "4px 10px", borderTop: "1px solid #1e293b", flexShrink: 0,
          }}>
            <span style={{ color: "#10b981", fontFamily: "monospace", fontSize: 12, flexShrink: 0 }}>
              {workspace} $
            </span>
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={running ? "çalışıyor... (Ctrl+C ile durdur)" : "komut gir..."}
              disabled={running}
              style={{
                flex: 1, background: "transparent", border: "none",
                outline: "none", color: "#e2e8f0",
                fontFamily: "JetBrains Mono, monospace", fontSize: 12,
              }}
            />
          </div>
        </>
      )}
    </div>
  );
}
