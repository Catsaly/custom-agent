"use client";
import { useState, useEffect, useCallback, useRef } from "react";
import {
  ChevronRight, ChevronDown, File, Folder, FolderOpen,
  Plus, Trash2, RefreshCw, HardDrive, Upload, X,
} from "lucide-react";
import { useIDEStore } from "@/store/ide";
import { listFiles, readFile, deleteFile } from "@/lib/api";
import {
  hasLocalFSSupport,
  buildLocalTree,
  readLocalFile,
  parseUploadedFileList,
  downloadFile,
} from "@/lib/local-fs";
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
  onLocalDelete?: (path: string) => void;
}

function TreeNode({ node, depth, onRefresh, onLocalDelete }: NodeProps) {
  const [expanded, setExpanded] = useState(depth < 2);
  const [hovering, setHovering] = useState(false);
  const { openFile, activeFile, workspace, unsavedFiles, localMode, localDirHandle } = useIDEStore();

  const handleClick = useCallback(async () => {
    if (node.type === "dir") {
      setExpanded((e) => !e);
    } else {
      try {
        if (localMode && localDirHandle) {
          const content = await readLocalFile(localDirHandle, node.path);
          openFile(node.path, content);
        } else {
          const data = await readFile(node.path, workspace);
          openFile(node.path, data.content ?? "");
        }
      } catch {
        openFile(node.path, "");
      }
    }
  }, [node, workspace, openFile, localMode, localDirHandle]);

  const handleDelete = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`"${node.name}" silinsin mi?`)) return;
    if (localMode) {
      onLocalDelete?.(node.path);
    } else {
      try {
        await deleteFile(node.path, workspace);
        onRefresh();
      } catch {}
    }
  }, [node, workspace, onRefresh, localMode, onLocalDelete]);

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
          <button
            onClick={handleDelete}
            style={{ background: "none", border: "none", cursor: "pointer", color: "#ef4444", padding: "0 2px", opacity: 0.7 }}
          >
            <Trash2 size={11} />
          </button>
        )}
      </div>
      {node.type === "dir" && expanded && node.children?.map((child) => (
        <TreeNode
          key={child.path}
          node={child}
          depth={depth + 1}
          onRefresh={onRefresh}
          onLocalDelete={onLocalDelete}
        />
      ))}
    </div>
  );
}

export default function FileTree() {
  const {
    files, setFiles, workspace, setWorkspace,
    localMode, setLocalMode, localDirHandle, setLocalDirHandle,
    openFile, fileContents, activeFile, unsavedFiles,
  } = useIDEStore();

  const [loading, setLoading] = useState(false);
  const [newFileName, setNewFileName] = useState("");
  const [showNewFile, setShowNewFile] = useState(false);
  const [localDirName, setLocalDirName] = useState<string>("");
  const uploadInputRef = useRef<HTMLInputElement>(null);

  /* ── Server mode refresh ─────────────────────────────────────────── */
  const refresh = useCallback(async () => {
    if (localMode) return;
    setLoading(true);
    try {
      const data = await listFiles(workspace);
      setFiles(data.tree ?? []);
    } catch {}
    finally { setLoading(false); }
  }, [workspace, setFiles, localMode]);

  useEffect(() => { refresh(); }, [refresh]);

  /* ── Local mode: File System Access API ─────────────────────────── */
  const openLocalFolder = useCallback(async () => {
    try {
      // @ts-expect-error - TS may not know showDirectoryPicker
      const handle: FileSystemDirectoryHandle = await window.showDirectoryPicker({ mode: "readwrite" });
      setLocalDirHandle(handle);
      setLocalDirName(handle.name);
      setLocalMode(true);
      setLoading(true);
      const tree = await buildLocalTree(handle);
      setFiles(tree);
    } catch (e: unknown) {
      if ((e as Error).name !== "AbortError") {
        alert("Klasör açılamadı: " + (e as Error).message);
      }
    } finally {
      setLoading(false);
    }
  }, [setLocalDirHandle, setLocalMode, setFiles]);

  /* ── Local mode: webkitdirectory fallback (mobile/Firefox) ───────── */
  const handleFolderUpload = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const fl = e.target.files;
    if (!fl || fl.length === 0) return;
    setLoading(true);
    const { tree, contents, promises } = parseUploadedFileList(fl);
    await Promise.all(promises);
    // Load contents into store
    Object.entries(contents).forEach(([path, content]) => {
      openFile(path, content);
    });
    setFiles(tree);
    setLocalMode(true);
    setLocalDirHandle(null); // no writable handle in this mode
    const firstFile = (fl[0] as File & { webkitRelativePath: string }).webkitRelativePath;
    setLocalDirName(firstFile.split("/")[0] ?? "upload");
    setLoading(false);
    e.target.value = "";
  }, [setFiles, setLocalMode, setLocalDirHandle, openFile]);

  /* ── Exit local mode ────────────────────────────────────────────── */
  const exitLocalMode = useCallback(() => {
    setLocalMode(false);
    setLocalDirHandle(null);
    setLocalDirName("");
    setFiles([]);
    refresh();
  }, [setLocalMode, setLocalDirHandle, setFiles, refresh]);

  /* ── Remove node from local tree (in-memory only) ───────────────── */
  const removeLocalNode = useCallback((path: string) => {
    function removeFromTree(nodes: FileNode[]): FileNode[] {
      return nodes
        .filter((n) => n.path !== path)
        .map((n) => ({ ...n, children: n.children ? removeFromTree(n.children) : undefined }));
    }
    setFiles(removeFromTree(files));
  }, [files, setFiles]);

  /* ── Create new file (server mode only) ─────────────────────────── */
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

  /* ── Download current file (local read-only fallback) ───────────── */
  const handleDownload = useCallback(() => {
    if (!activeFile) return;
    const content = fileContents[activeFile] ?? "";
    downloadFile(activeFile, content);
  }, [activeFile, fileContents]);

  /* ── Render ─────────────────────────────────────────────────────── */
  const isReadonlyLocal = localMode && !localDirHandle; // webkitdirectory mode

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", padding: "8px 10px", borderBottom: "1px solid #2d3748", gap: 6, flexShrink: 0 }}>
        {localMode ? (
          <>
            <HardDrive size={13} color="#10b981" />
            <span style={{ flex: 1, fontSize: 11, fontWeight: 700, color: "#10b981", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              {localDirName || "Yerel"}
            </span>
            {isReadonlyLocal && activeFile && unsavedFiles.has(activeFile) && (
              <button
                onClick={handleDownload}
                title="İndir"
                style={{ background: "none", border: "none", cursor: "pointer", color: "#f59e0b", padding: 2, fontSize: 10 }}
              >
                ⬇
              </button>
            )}
            <button
              onClick={exitLocalMode}
              title="Yerel moddan çık"
              style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", padding: 2 }}
            >
              <X size={13} />
            </button>
          </>
        ) : (
          <>
            <span style={{ flex: 1, fontSize: 11, fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.8px" }}>
              Dosyalar
            </span>
            <button onClick={() => setShowNewFile((v) => !v)} title="Yeni dosya" style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", padding: 2 }}>
              <Plus size={14} />
            </button>
            <button onClick={refresh} title="Yenile" style={{ background: "none", border: "none", cursor: "pointer", color: loading ? "#6366f1" : "#94a3b8", padding: 2 }}>
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            </button>
          </>
        )}
      </div>

      {/* Local folder open buttons (shown when not in local mode) */}
      {!localMode && (
        <div style={{ padding: "6px 8px", borderBottom: "1px solid #2d3748", flexShrink: 0, display: "flex", flexDirection: "column", gap: 4 }}>
          {hasLocalFSSupport ? (
            <button
              onClick={openLocalFolder}
              style={{
                width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.3)",
                borderRadius: 6, padding: "5px 8px", color: "#10b981", cursor: "pointer", fontSize: 11, fontWeight: 600,
              }}
            >
              <HardDrive size={12} /> Yerel Klasör Aç
            </button>
          ) : (
            <>
              <button
                onClick={() => uploadInputRef.current?.click()}
                style={{
                  width: "100%", display: "flex", alignItems: "center", justifyContent: "center", gap: 6,
                  background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.3)",
                  borderRadius: 6, padding: "5px 8px", color: "#a5b4fc", cursor: "pointer", fontSize: 11, fontWeight: 600,
                }}
              >
                <Upload size={12} /> Klasör Yükle
              </button>
              <input
                ref={uploadInputRef}
                type="file"
                // @ts-expect-error - webkitdirectory not in standard types
                webkitdirectory=""
                multiple
                style={{ display: "none" }}
                onChange={handleFolderUpload}
              />
            </>
          )}
        </div>
      )}

      {/* Workspace input (server mode only) */}
      {!localMode && (
        <div style={{ padding: "6px 8px", borderBottom: "1px solid #2d3748", flexShrink: 0 }}>
          <input
            value={workspace}
            onChange={(e) => setWorkspace(e.target.value)}
            onBlur={refresh}
            placeholder="workspace adı"
            style={{
              width: "100%", background: "#0f172a", border: "1px solid #334155",
              borderRadius: 6, padding: "4px 8px", color: "#e2e8f0", fontSize: 11,
              outline: "none", boxSizing: "border-box",
            }}
          />
        </div>
      )}

      {/* Read-only badge for upload mode */}
      {isReadonlyLocal && (
        <div style={{ padding: "4px 10px", background: "rgba(245,158,11,0.08)", borderBottom: "1px solid #2d3748", flexShrink: 0 }}>
          <span style={{ fontSize: 10, color: "#f59e0b" }}>
            ⚠ Sadece okunur — değişiklikleri indirin
          </span>
        </div>
      )}

      {/* New file input (server mode only) */}
      {!localMode && showNewFile && (
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
        {loading ? (
          <div style={{ padding: "20px 12px", color: "#6366f1", fontSize: 12, textAlign: "center" }}>
            Yükleniyor…
          </div>
        ) : files.length === 0 ? (
          <div style={{ padding: "20px 12px", color: "#4b5563", fontSize: 12, textAlign: "center" }}>
            {localMode ? "Klasör boş." : "Dosya yok.\nAI'dan proje üretmesini iste."}
          </div>
        ) : (
          files.map((node) => (
            <TreeNode
              key={node.path}
              node={node}
              depth={0}
              onRefresh={refresh}
              onLocalDelete={removeLocalNode}
            />
          ))
        )}
      </div>
    </div>
  );
}
