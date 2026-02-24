"use client";
import { useState, useEffect, useCallback } from "react";
import { ChevronRight, ChevronDown, File, Folder, FolderOpen, Plus, Trash2, RefreshCw, Edit3 } from "lucide-react";
import { useIDEStore } from "@/store/ide";
import { listFiles, readFile, deleteFile } from "@/lib/api";
import type { FileNode } from "@/lib/types";

const FILE_ICONS: Record<string, string> = {
  py: "🐍", js: "🟨", ts: "💙", tsx: "⚛️", jsx: "⚛️",
  html: "🌐", css: "🎨", json: "📋", md: "📝",
  sh: "🔧", yaml: "⚙️", yml: "⚙️", sql: "🗄️",
  go: "🐹", rs: "🦀", java: "☕", toml: "📦",
  env: "🔑", txt: "📄", dockerfile: "🐳",
};

function getFileIcon(name: string) {
  const ext = name.split(".").pop()?.toLowerCase() ?? "";
  return FILE_ICONS[ext] || FILE_ICONS[name.toLowerCase()] || "📄";
}

interface NodeProps {
  node: FileNode;
  depth: number;
  onRefresh: () => void;
}

function TreeNode({ node, depth, onRefresh }: NodeProps) {
  const [expanded, setExpanded] = useState(depth < 2);
  const [hovering, setHovering] = useState(false);
  const { openFile, activeFile, workspace, unsavedFiles } = useIDEStore();

  const handleClick = useCallback(async () => {
    if (node.type === "dir") {
      setExpanded((e) => !e);
    } else {
      try {
        const data = await readFile(node.path, workspace);
        openFile(node.path, data.content ?? "");
      } catch (e) {
        openFile(node.path, "");
      }
    }
  }, [node, workspace, openFile]);

  const handleDelete = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`"${node.name}" silinsin mi?`)) return;
    try {
      await deleteFile(node.path, workspace);
      onRefresh();
    } catch {}
  }, [node, workspace, onRefresh]);

  const isActive = activeFile === node.path;
  const hasUnsaved = unsavedFiles.has(node.path);

  return (
    <div>
      <div
        onMouseEnter={() => setHovering(true)}
        onMouseLeave={() => setHovering(false)}
        onClick={handleClick}
        style={{
          display: "flex", alignItems: "center", gap: 4,
          paddingLeft: depth * 12 + 8, paddingRight: 8,
          height: 26, cursor: "pointer", borderRadius: 4,
          background: isActive ? "rgba(99,102,241,0.2)" : hovering ? "rgba(255,255,255,0.05)" : "transparent",
          color: isActive ? "#a5b4fc" : "#e2e8f0",
          userSelect: "none",
        }}
      >
        {node.type === "dir" ? (
          <>
            {expanded ? <ChevronDown size={12} color="#94a3b8" /> : <ChevronRight size={12} color="#94a3b8" />}
            {expanded ? <FolderOpen size={14} color="#fbbf24" /> : <Folder size={14} color="#fbbf24" />}
          </>
        ) : (
          <>
            <span style={{ width: 12 }} />
            <span style={{ fontSize: 13 }}>{getFileIcon(node.name)}</span>
          </>
        )}
        <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", fontSize: 12 }}>
          {node.name}
          {hasUnsaved && <span style={{ color: "#f59e0b", marginLeft: 4 }}>●</span>}
        </span>
        {hovering && node.type === "file" && (
          <button onClick={handleDelete} style={{ background: "none", border: "none", cursor: "pointer", color: "#ef4444", padding: "0 2px", opacity: 0.7 }}>
            <Trash2 size={11} />
          </button>
        )}
      </div>
      {node.type === "dir" && expanded && node.children?.map((child) => (
        <TreeNode key={child.path} node={child} depth={depth + 1} onRefresh={onRefresh} />
      ))}
    </div>
  );
}

export default function FileTree() {
  const { files, setFiles, workspace, setWorkspace } = useIDEStore();
  const [loading, setLoading] = useState(false);
  const [newFileName, setNewFileName] = useState("");
  const [showNewFile, setShowNewFile] = useState(false);
  const { openFile } = useIDEStore();

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listFiles(workspace);
      setFiles(data.tree ?? []);
    } catch {}
    finally { setLoading(false); }
  }, [workspace, setFiles]);

  useEffect(() => { refresh(); }, [refresh]);

  const handleCreateFile = useCallback(async () => {
    if (!newFileName.trim()) return;
    try {
      const { writeFile } = await import("@/lib/api");
      await writeFile(newFileName, "", workspace);
      openFile(newFileName, "");
      setNewFileName("");
      setShowNewFile(false);
      refresh();
    } catch {}
  }, [newFileName, workspace, openFile, refresh]);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", padding: "8px 10px", borderBottom: "1px solid #2d3748", gap: 6, flexShrink: 0 }}>
        <span style={{ flex: 1, fontSize: 11, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.8px" }}>
          Dosyalar
        </span>
        <button onClick={() => setShowNewFile((v) => !v)} title="Yeni dosya" style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", padding: 2 }}>
          <Plus size={14} />
        </button>
        <button onClick={refresh} title="Yenile" style={{ background: "none", border: "none", cursor: "pointer", color: loading ? "#6366f1" : "#94a3b8", padding: 2 }}>
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Workspace input */}
      <div style={{ padding: "6px 8px", borderBottom: "1px solid #2d3748", flexShrink: 0 }}>
        <input
          value={workspace}
          onChange={(e) => setWorkspace(e.target.value)}
          onBlur={refresh}
          placeholder="workspace adı"
          style={{
            width: "100%", background: "#0f172a", border: "1px solid #334155",
            borderRadius: 6, padding: "4px 8px", color: "#e2e8f0", fontSize: 11,
            outline: "none",
          }}
        />
      </div>

      {/* New file input */}
      {showNewFile && (
        <div style={{ padding: "6px 8px", borderBottom: "1px solid #2d3748", flexShrink: 0, display: "flex", gap: 4 }}>
          <input
            autoFocus
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleCreateFile(); if (e.key === "Escape") setShowNewFile(false); }}
            placeholder="dosya.py"
            style={{
              flex: 1, background: "#0f172a", border: "1px solid #6366f1",
              borderRadius: 6, padding: "4px 8px", color: "#e2e8f0", fontSize: 11, outline: "none",
            }}
          />
          <button onClick={handleCreateFile} style={{ background: "#6366f1", border: "none", borderRadius: 6, padding: "4px 8px", color: "white", cursor: "pointer", fontSize: 11 }}>
            Oluştur
          </button>
        </div>
      )}

      {/* Tree */}
      <div style={{ flex: 1, overflowY: "auto", padding: "4px 2px" }}>
        {files.length === 0 ? (
          <div style={{ padding: "20px 12px", color: "#4b5563", fontSize: 12, textAlign: "center" }}>
            Dosya yok.<br />AI&apos;dan proje üretmesini iste.
          </div>
        ) : (
          files.map((node) => (
            <TreeNode key={node.path} node={node} depth={0} onRefresh={refresh} />
          ))
        )}
      </div>
    </div>
  );
}
