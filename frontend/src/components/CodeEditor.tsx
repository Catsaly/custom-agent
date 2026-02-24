"use client";
import { useCallback, useRef } from "react";
import Editor, { type Monaco } from "@monaco-editor/react";
import { X, Save, Circle } from "lucide-react";
import { useIDEStore } from "@/store/ide";
import { writeFile } from "@/lib/api";

const LANG_MAP: Record<string, string> = {
  py: "python", js: "javascript", ts: "typescript", tsx: "typescript",
  jsx: "javascript", html: "html", css: "css", json: "json",
  md: "markdown", sh: "shell", yaml: "yaml", yml: "yaml",
  sql: "sql", go: "go", rs: "rust", java: "java", toml: "toml",
  dockerfile: "dockerfile", env: "plaintext",
};

function getLang(path: string) {
  const ext = path.split(".").pop()?.toLowerCase() ?? "";
  return LANG_MAP[ext] || "plaintext";
}

function getFileName(path: string) {
  return path.split("/").pop() ?? path;
}

export default function CodeEditor() {
  const {
    openFiles, activeFile, fileContents, closeFile, setActiveFile,
    setFileContent, markUnsaved, markSaved, unsavedFiles, workspace,
  } = useIDEStore();

  const monacoRef = useRef<Monaco | null>(null);

  const handleEditorMount = useCallback((_: unknown, monaco: Monaco) => {
    monacoRef.current = monaco;
    monaco.editor.defineTheme("ide-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "comment", foreground: "6b7a8d", fontStyle: "italic" },
        { token: "keyword", foreground: "c792ea" },
        { token: "string", foreground: "c3e88d" },
        { token: "number", foreground: "f78c6c" },
      ],
      colors: {
        "editor.background": "#0d1117",
        "editor.foreground": "#e2e8f0",
        "editorLineNumber.foreground": "#4b5563",
        "editorLineNumber.activeForeground": "#94a3b8",
        "editor.selectionBackground": "#2d3748",
        "editor.inactiveSelectionBackground": "#1e293b",
        "editorCursor.foreground": "#6366f1",
        "editorIndentGuide.background": "#1e293b",
        "editorBracketMatch.background": "#334155",
        "editorSuggestWidget.background": "#1e293b",
        "editorSuggestWidget.border": "#334155",
      },
    });
    monaco.editor.setTheme("ide-dark");
  }, []);

  const handleSave = useCallback(async (path: string) => {
    const content = fileContents[path] ?? "";
    try {
      await writeFile(path, content, workspace);
      markSaved(path);
    } catch (e) {
      console.error("Save error:", e);
    }
  }, [fileContents, workspace, markSaved]);

  if (!activeFile) {
    return (
      <div style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        background: "#0d1117", color: "#4b5563", flexDirection: "column", gap: 12,
      }}>
        <div style={{ fontSize: 48 }}>📝</div>
        <div style={{ fontSize: 14 }}>Dosya seç veya AI&apos;dan oluşturmasını iste</div>
        <div style={{ fontSize: 12, color: "#374151" }}>Ctrl+S: Kaydet &nbsp;·&nbsp; Sol panel: Dosya ağacı &nbsp;·&nbsp; Sağ panel: AI</div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Tabs */}
      <div style={{
        display: "flex", overflowX: "auto", background: "#0f172a",
        borderBottom: "1px solid #2d3748", flexShrink: 0, height: 36,
      }}>
        {openFiles.map((path) => {
          const isActive = path === activeFile;
          const isDirty = unsavedFiles.has(path);
          return (
            <div
              key={path}
              onClick={() => setActiveFile(path)}
              style={{
                display: "flex", alignItems: "center", gap: 6,
                padding: "0 12px", height: "100%", cursor: "pointer",
                minWidth: 100, maxWidth: 180, flexShrink: 0,
                background: isActive ? "#0d1117" : "transparent",
                borderRight: "1px solid #2d3748",
                borderTop: isActive ? "2px solid #6366f1" : "2px solid transparent",
                color: isActive ? "#e2e8f0" : "#94a3b8",
                fontSize: 12,
              }}
            >
              {isDirty ? (
                <Circle size={8} fill="#f59e0b" color="#f59e0b" />
              ) : null}
              <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {getFileName(path)}
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); closeFile(path); }}
                style={{ background: "none", border: "none", cursor: "pointer", color: "inherit", padding: 0, opacity: 0.6, display: "flex" }}
              >
                <X size={12} />
              </button>
            </div>
          );
        })}
      </div>

      {/* Save bar */}
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        padding: "3px 12px", background: "#0f172a", borderBottom: "1px solid #2d3748",
        flexShrink: 0, fontSize: 11, color: "#4b5563",
      }}>
        <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis" }}>{activeFile}</span>
        {unsavedFiles.has(activeFile) && (
          <button
            onClick={() => handleSave(activeFile)}
            style={{ display: "flex", alignItems: "center", gap: 4, background: "#1e293b", border: "1px solid #334155", borderRadius: 6, padding: "2px 8px", color: "#94a3b8", cursor: "pointer", fontSize: 11 }}
          >
            <Save size={11} /> Kaydet
          </button>
        )}
        <span style={{ color: "#374151" }}>{getLang(activeFile)}</span>
      </div>

      {/* Monaco */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        <Editor
          key={activeFile}
          language={getLang(activeFile)}
          value={fileContents[activeFile] ?? ""}
          theme="ide-dark"
          onChange={(val) => {
            if (val !== undefined) {
              setFileContent(activeFile, val);
              markUnsaved(activeFile);
            }
          }}
          onMount={handleEditorMount}
          options={{
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontLigatures: true,
            lineNumbers: "on",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: "on",
            automaticLayout: true,
            tabSize: 2,
            renderWhitespace: "boundary",
            smoothScrolling: true,
            cursorBlinking: "phase",
            bracketPairColorization: { enabled: true },
            suggest: { preview: true },
            padding: { top: 12 },
          }}
        />
      </div>
    </div>
  );
}
