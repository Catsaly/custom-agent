"use client";
import { useState } from "react";
import { ChevronRight, ChevronDown, CheckCircle, Loader, AlertCircle, Terminal, FileText, Search, Globe, Trash, FolderOpen, Edit } from "lucide-react";
import type { ToolCall } from "@/lib/types";

const TOOL_META: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  read_file:   { icon: <FileText size={13} />,    label: "Dosya Oku",    color: "#60a5fa" },
  write_file:  { icon: <Edit size={13} />,         label: "Dosya Yaz",   color: "#34d399" },
  delete_file: { icon: <Trash size={13} />,        label: "Dosya Sil",   color: "#f87171" },
  list_files:  { icon: <FolderOpen size={13} />,   label: "Listele",     color: "#fbbf24" },
  run_command: { icon: <Terminal size={13} />,     label: "Komut Çalıştır", color: "#a78bfa" },
  web_search:  { icon: <Search size={13} />,       label: "Web Araması", color: "#f59e0b" },
  fetch_url:   { icon: <Globe size={13} />,        label: "URL Oku",     color: "#38bdf8" },
};

export function ToolCallCard({ call }: { call: ToolCall }) {
  const [expanded, setExpanded] = useState(true);
  const meta = TOOL_META[call.tool] ?? { icon: <Terminal size={13} />, label: call.tool, color: "#94a3b8" };

  const StatusIcon = call.status === "running"
    ? () => <Loader size={12} className="animate-spin" color="#6366f1" />
    : call.status === "error"
    ? () => <AlertCircle size={12} color="#ef4444" />
    : () => <CheckCircle size={12} color="#10b981" />;

  // Format input for display
  const inputStr = (() => {
    const inp = call.input as Record<string, unknown>;
    if (call.tool === "write_file") {
      const { path, content } = inp;
      const lines = String(content ?? "").split("\n").length;
      return `path: "${path}"\ncontent: (${lines} satır)`;
    }
    return Object.entries(inp)
      .map(([k, v]) => `${k}: ${String(v).slice(0, 200)}`)
      .join("\n");
  })();

  return (
    <div className="tool-card animate-fade">
      <div className="tool-card-header" onClick={() => setExpanded((v) => !v)}>
        <span style={{ color: meta.color }}>{meta.icon}</span>
        <span style={{ color: meta.color, fontSize: 12, fontWeight: 600 }}>{meta.label}</span>
        {call.tool === "write_file" && (
          <span style={{ color: "#94a3b8", fontSize: 11, flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>
            {String((call.input as Record<string, unknown>).path ?? "")}
          </span>
        )}
        {call.tool === "run_command" && (
          <span style={{ color: "#94a3b8", fontSize: 11, flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>
            {String((call.input as Record<string, unknown>).command ?? "").slice(0, 50)}
          </span>
        )}
        {call.tool !== "write_file" && call.tool !== "run_command" && (
          <span style={{ flex: 1 }} />
        )}
        <StatusIcon />
        {expanded ? <ChevronDown size={12} color="#94a3b8" /> : <ChevronRight size={12} color="#94a3b8" />}
      </div>
      {expanded && (
        <div className="tool-card-body">
          <div style={{ color: "#94a3b8", fontSize: 11, marginBottom: 6 }}>INPUT:</div>
          <pre style={{ color: "#e2e8f0", marginBottom: 8 }}>{inputStr}</pre>
          {call.output && (
            <>
              <div style={{ color: "#94a3b8", fontSize: 11, marginBottom: 6, borderTop: "1px solid #334155", paddingTop: 6 }}>OUTPUT:</div>
              <pre style={{ color: call.status === "error" ? "#f87171" : "#86efac" }}>
                {call.output.slice(0, 1000)}{call.output.length > 1000 ? "\n...(kesildi)" : ""}
              </pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}
