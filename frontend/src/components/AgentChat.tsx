"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Square, Trash2, Bot, User, Paperclip, X, FileText } from "lucide-react";
import { useIDEStore } from "@/store/ide";
import { streamAgent } from "@/lib/api";
import { MODELS } from "@/lib/types";
import type { ChatMessage, ToolCall, Attachment } from "@/lib/types";
import { ToolCallCard } from "./ToolCallView";
import ModelSelector from "./ModelSelector";

const ACCEPTED_TYPES = [
  ".txt", ".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".json",
  ".yaml", ".yml", ".toml", ".csv", ".log", ".sh", ".sql",
  ".html", ".css", ".xml", ".rs", ".go", ".java", ".cpp", ".c", ".h",
  "text/*",
].join(",");

function AttachmentBadge({ att, onRemove }: { att: Attachment; onRemove?: () => void }) {
  const lines = att.content.split("\n").length;
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 5,
      background: "rgba(99,102,241,0.12)", border: "1px solid rgba(99,102,241,0.3)",
      borderRadius: 6, padding: "3px 8px", fontSize: 11, color: "#a5b4fc",
    }}>
      <FileText size={11} />
      <span style={{ maxWidth: 120, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {att.name}
      </span>
      <span style={{ color: "#4b5563" }}>{lines}s</span>
      {onRemove && (
        <button onClick={onRemove} style={{ background: "none", border: "none", cursor: "pointer", color: "#6b7280", padding: 0, display: "flex" }}>
          <X size={10} />
        </button>
      )}
    </div>
  );
}

function renderContent(content: string) {
  // Code blocks
  const parts = content.split(/(```[\s\S]*?```|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```") && part.endsWith("```")) {
      const lines = part.slice(3, -3).split("\n");
      const lang = lines[0].trim();
      const code = lines.slice(1).join("\n");
      return (
        <pre key={i} className="chat-pre">
          {lang && <div style={{ color: "#6366f1", fontSize: 10, marginBottom: 4 }}>{lang}</div>}
          <code style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 12 }}>{code}</code>
        </pre>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i} className="chat-code">{part.slice(1, -1)}</code>;
    }
    // Bold
    return (
      <span key={i} dangerouslySetInnerHTML={{
        __html: part
          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
          .replace(/\n/g, "<br/>"),
      }} />
    );
  });
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === "user";
  return (
    <div className="chat-msg" style={{ display: "flex", flexDirection: "column", alignItems: isUser ? "flex-end" : "flex-start", gap: 4, padding: "4px 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "#64748b", flexDirection: isUser ? "row-reverse" : "row" }}>
        {isUser ? <User size={12} /> : <Bot size={12} color="#6366f1" />}
        <span>{isUser ? "Sen" : "AI"}</span>
        <span>{new Date(msg.timestamp).toLocaleTimeString("tr", { hour: "2-digit", minute: "2-digit" })}</span>
      </div>

      {/* Eklenen dosyalar (kullanıcı mesajı) */}
      {isUser && msg.attachments && msg.attachments.length > 0 && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4, justifyContent: "flex-end" }}>
          {msg.attachments.map((att, i) => <AttachmentBadge key={i} att={att} />)}
        </div>
      )}

      {msg.role === "assistant" && msg.toolCalls && msg.toolCalls.length > 0 && (
        <div style={{ width: "100%", maxWidth: 360 }}>
          {msg.toolCalls.map((tc) => <ToolCallCard key={tc.id} call={tc} />)}
        </div>
      )}

      {msg.content && (
        <div className={isUser ? "chat-msg-user" : "chat-msg-ai"} style={{ fontSize: 13, lineHeight: 1.6 }}>
          {renderContent(msg.content)}
        </div>
      )}
    </div>
  );
}

export default function AgentChat() {
  const {
    messages, addMessage, updateLastMessage, clearMessages,
    modelId, apiKeys, workspace,
  } = useIDEStore();

  const [input, setInput] = useState("");
  const [running, setRunning] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const getApiKey = useCallback(() => {
    const info = MODELS[modelId];
    if (!info) return null;
    return apiKeys[info.provider] || null;
  }, [modelId, apiKeys]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setRunning(false);
  }, []);

  /* ── File attachment ─────────────────────────────────────────────── */
  const handleFileAttach = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    const newAtts: Attachment[] = [];
    await Promise.all(files.map(async (file) => {
      try {
        const content = await file.text();
        newAtts.push({ name: file.name, content });
      } catch { /* binary dosyayı atla */ }
    }));
    setAttachments((prev) => [...prev, ...newAtts]);
    e.target.value = "";
  }, []);

  const removeAttachment = useCallback((idx: number) => {
    setAttachments((prev) => prev.filter((_, i) => i !== idx));
  }, []);

  const send = useCallback(async () => {
    const text = input.trim();
    if ((!text && attachments.length === 0) || running) return;
    setInput("");
    setRunning(true);

    // Dosya içeriklerini mesaja ekle
    let fullContent = text;
    if (attachments.length > 0) {
      const blocks = attachments.map((att) => {
        const ext = att.name.split(".").pop() ?? "";
        return `📎 **${att.name}**\n\`\`\`${ext}\n${att.content}\n\`\`\``;
      });
      fullContent = blocks.join("\n\n") + (text ? "\n\n" + text : "");
    }

    const currentAttachments = [...attachments];
    setAttachments([]);

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: fullContent,
      attachments: currentAttachments.length > 0 ? currentAttachments : undefined,
      timestamp: new Date(),
    };
    addMessage(userMsg);

    // Build AI message placeholder
    const aiMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
      toolCalls: [],
      timestamp: new Date(),
    };
    addMessage(aiMsg);

    // API messages history
    const apiMsgs = [...messages, userMsg].map((m) => ({
      role: m.role,
      content: m.content || "[tool operations]",
    }));

    const activeToolCallIds = new Map<string, string>(); // tool_id -> toolCall.id

    abortRef.current = streamAgent(
      apiMsgs,
      modelId,
      getApiKey(),
      workspace,
      (event) => {
        const ev = event as Record<string, unknown>;
        if (ev.type === "token") {
          updateLastMessage((msg) => ({
            ...msg,
            content: msg.content + (ev.content as string),
          }));
        } else if (ev.type === "tool_start") {
          const tcId = `${ev.id}-${Date.now()}`;
          activeToolCallIds.set(ev.id as string, tcId);
          const tc: ToolCall = {
            id: tcId,
            tool: ev.tool as string,
            input: (ev.input as Record<string, unknown>) ?? {},
            status: "running",
          };
          updateLastMessage((msg) => ({
            ...msg,
            toolCalls: [...(msg.toolCalls ?? []), tc],
          }));
        } else if (ev.type === "tool_result") {
          const tcId = activeToolCallIds.get(ev.id as string);
          updateLastMessage((msg) => ({
            ...msg,
            toolCalls: (msg.toolCalls ?? []).map((tc) =>
              tc.id === tcId
                ? { ...tc, output: ev.output as string, status: "done" as const }
                : tc
            ),
          }));
        } else if (ev.type === "done") {
          if (ev.content) {
            updateLastMessage((msg) => ({
              ...msg,
              content: msg.content || (ev.content as string),
            }));
          }
        }
      },
      (err) => {
        updateLastMessage((msg) => ({ ...msg, content: msg.content + `\n\n⚠️ Hata: ${err}` }));
        setRunning(false);
      },
      () => setRunning(false),
    );
  }, [input, attachments, running, messages, modelId, getApiKey, workspace, addMessage, updateLastMessage]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const modelInfo = MODELS[modelId];
  const hasKey = !!getApiKey();
  const canSend = (input.trim().length > 0 || attachments.length > 0) && !running;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}>
      {/* Header */}
      <div style={{ padding: "8px 12px", borderBottom: "1px solid #2d3748", flexShrink: 0, display: "flex", alignItems: "center", gap: 8 }}>
        <Bot size={16} color="#6366f1" />
        <span style={{ fontWeight: 600, fontSize: 13, flex: 1 }}>AI Agent</span>
        {modelInfo && (
          <span style={{
            fontSize: 11, padding: "2px 8px", borderRadius: 9999,
            background: "rgba(99,102,241,0.15)", color: "#a5b4fc",
          }}>
            {modelInfo.icon} {modelInfo.short}
            {modelInfo.free && " ✓"}
          </span>
        )}
        <span style={{ width: 8, height: 8, borderRadius: "50%", background: hasKey ? "#10b981" : "#ef4444", display: "inline-block" }} title={hasKey ? "API hazır" : "API anahtarı gerekli"} />
        <button onClick={clearMessages} title="Temizle" style={{ background: "none", border: "none", cursor: "pointer", color: "#4b5563", padding: 2 }}>
          <Trash2 size={13} />
        </button>
      </div>

      {/* Model Selector */}
      <ModelSelector />

      {/* Messages */}
      <div ref={scrollRef} style={{ flex: 1, overflowY: "auto", padding: "8px 10px", display: "flex", flexDirection: "column", gap: 2 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", padding: "40px 16px", color: "#374151" }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🤖</div>
            <div style={{ fontSize: 13, color: "#6b7280", marginBottom: 16 }}>
              14 araçla çalışan AI — 📎 dosya ekleyebilirsin:
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12, color: "#4b5563" }}>
              {[
                "📁 Dosya oku / yaz / ara / taşı",
                "🔧 Cerrahi patch (satır düzenleme)",
                "📦 Paket yükle & komut çalıştır",
                "🧪 Testleri otomatik algıla & çalıştır",
                "🔀 Git işlemleri",
                "🔍 Web araştır & URL oku",
                "📎 Dosya ekle — AI direkt analiz eder",
              ].map((t) => (
                <div key={t} style={{ background: "#1e293b", borderRadius: 8, padding: "6px 12px", textAlign: "left" }}>{t}</div>
              ))}
            </div>
          </div>
        )}
        {messages.map((msg) => <MessageBubble key={msg.id} msg={msg} />)}
        {running && (
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", color: "#6366f1", fontSize: 12 }}>
            <div className="animate-pulse" style={{ width: 8, height: 8, borderRadius: "50%", background: "#6366f1" }} />
            <span>AI düşünüyor...</span>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={{ padding: "8px 10px", borderTop: "1px solid #2d3748", flexShrink: 0 }}>
        {/* Attachment badges */}
        {attachments.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 6 }}>
            {attachments.map((att, i) => (
              <AttachmentBadge key={i} att={att} onRemove={() => removeAttachment(i)} />
            ))}
          </div>
        )}

        <div style={{ display: "flex", gap: 6, alignItems: "flex-end" }}>
          {/* Dosya ekleme butonu */}
          <button
            onClick={() => fileInputRef.current?.click()}
            title="Metin dosyası ekle (.txt, .py, .json, .md, …)"
            disabled={running}
            style={{
              background: "none", border: "1px solid #334155", borderRadius: 8,
              padding: "7px 8px", cursor: running ? "not-allowed" : "pointer",
              color: attachments.length > 0 ? "#6366f1" : "#64748b",
              display: "flex", alignItems: "center", flexShrink: 0,
              opacity: running ? 0.5 : 1,
            }}
          >
            <Paperclip size={15} />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED_TYPES}
            multiple
            style={{ display: "none" }}
            onChange={handleFileAttach}
          />

          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={attachments.length > 0 ? "Dosya hakkında görev ver… (Enter = gönder)" : "Ne yapalım? (Enter = gönder, Shift+Enter = yeni satır)"}
            rows={2}
            style={{
              flex: 1, background: "#1e293b", border: "1px solid #334155",
              borderRadius: 10, padding: "8px 12px", color: "#e2e8f0",
              fontSize: 13, resize: "none", outline: "none", fontFamily: "inherit",
              lineHeight: 1.5,
            }}
            onFocus={(e) => (e.target.style.borderColor = "#6366f1")}
            onBlur={(e) => (e.target.style.borderColor = "#334155")}
          />
          <button
            onClick={running ? stop : send}
            disabled={!canSend && !running}
            style={{
              background: running ? "#ef4444" : "#6366f1",
              border: "none", borderRadius: 10, padding: "8px 12px",
              color: "white", cursor: "pointer", display: "flex",
              alignItems: "center", gap: 4, fontSize: 13, fontWeight: 600,
              opacity: !canSend && !running ? 0.5 : 1,
            }}
          >
            {running ? <Square size={16} /> : <Send size={16} />}
          </button>
        </div>
        {!hasKey && modelInfo && !modelInfo.free && (
          <div style={{ marginTop: 6, fontSize: 11, color: "#f59e0b" }}>
            ⚠️ {modelInfo.group} için API anahtarı gerekli. ⚙️ Ayarlar&apos;dan gir.
          </div>
        )}
      </div>
    </div>
  );
}
