"use client";
import { X, Key, ExternalLink } from "lucide-react";
import { useIDEStore } from "@/store/ide";
import { PROVIDER_KEY_LABELS } from "@/lib/types";

export default function Settings() {
  const { toggleSettings, apiKeys, setApiKey } = useIDEStore();

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 200, background: "rgba(0,0,0,0.7)",
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <div style={{
        background: "#1e293b", border: "1px solid #334155", borderRadius: 16,
        width: 480, maxHeight: "80vh", overflow: "hidden", display: "flex", flexDirection: "column",
        boxShadow: "0 24px 64px rgba(0,0,0,0.8)",
      }}>
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", padding: "16px 20px", borderBottom: "1px solid #334155" }}>
          <Key size={18} color="#6366f1" />
          <span style={{ fontWeight: 700, fontSize: 15, flex: 1, marginLeft: 10 }}>API Anahtarları</span>
          <button onClick={toggleSettings} style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", padding: 4 }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ overflowY: "auto", padding: "16px 20px", display: "flex", flexDirection: "column", gap: 16 }}>
          <p style={{ fontSize: 12, color: "#64748b", lineHeight: 1.6 }}>
            Anahtarlar yalnızca tarayıcınızda localStorage&apos;da saklanır. Sunucuya gönderilir ancak kaydedilmez.
          </p>

          {Object.entries(PROVIDER_KEY_LABELS).map(([provider, meta]) => (
            <div key={provider}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                <label style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{meta.label}</label>
                <a href={`https://${meta.hint}`} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: "#6366f1", display: "flex", alignItems: "center", gap: 3 }}>
                  {meta.hint} <ExternalLink size={10} />
                </a>
              </div>
              <input
                type="password"
                value={apiKeys[provider] ?? ""}
                onChange={(e) => setApiKey(provider, e.target.value)}
                placeholder={meta.placeholder}
                style={{
                  width: "100%", background: "#0f172a", border: "1px solid #334155",
                  borderRadius: 8, padding: "8px 12px", color: "#e2e8f0", fontSize: 13, outline: "none",
                }}
                onFocus={(e) => (e.target.style.borderColor = "#6366f1")}
                onBlur={(e) => (e.target.style.borderColor = "#334155")}
              />
            </div>
          ))}

          {/* Free models guide */}
          <div style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 10, padding: "14px 16px" }}>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 10, color: "#10b981" }}>✓ Ücretsiz Kullanım</div>
            <div style={{ fontSize: 12, color: "#64748b", lineHeight: 1.8 }}>
              <strong style={{ color: "#a78bfa" }}>Groq</strong> → Llama/Mixtral, console.groq.com → API Keys<br/>
              <strong style={{ color: "#34d399" }}>OpenRouter</strong> → 50+ ücretsiz model, openrouter.ai → Keys<br/>
              <strong style={{ color: "#60a5fa" }}>Gemini</strong> → aistudio.google.com → Get API Key (ücretsiz)<br/>
              <strong style={{ color: "#4dd0e1" }}>GLM Flash</strong> → open.bigmodel.cn → API Keys (ücretsiz)
            </div>
          </div>
        </div>

        <div style={{ padding: "12px 20px", borderTop: "1px solid #334155" }}>
          <button onClick={toggleSettings} style={{
            width: "100%", background: "#6366f1", border: "none", borderRadius: 10,
            padding: "10px", color: "white", fontWeight: 600, cursor: "pointer", fontSize: 14,
          }}>
            Kaydet & Kapat
          </button>
        </div>
      </div>
    </div>
  );
}
