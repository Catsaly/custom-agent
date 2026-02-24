"use client";
import { useState } from "react";
import { ChevronDown, Check } from "lucide-react";
import { useIDEStore } from "@/store/ide";
import { MODELS } from "@/lib/types";

// Group models
const GROUPS: Record<string, string[]> = {};
Object.entries(MODELS).forEach(([id, info]) => {
  if (!GROUPS[info.group]) GROUPS[info.group] = [];
  GROUPS[info.group].push(id);
});

export default function ModelSelector() {
  const { modelId, setModelId } = useIDEStore();
  const [open, setOpen] = useState(false);
  const [filter, setFilter] = useState<"all" | "free" | "paid">("all");
  const current = MODELS[modelId];

  return (
    <div style={{ position: "relative", padding: "6px 10px", borderBottom: "1px solid #1e293b" }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          width: "100%", display: "flex", alignItems: "center", gap: 6,
          background: "#1e293b", border: "1px solid #334155", borderRadius: 8,
          padding: "6px 10px", color: "#e2e8f0", cursor: "pointer", fontSize: 12,
        }}
      >
        <span>{current?.icon ?? "🤖"}</span>
        <span style={{ flex: 1, textAlign: "left", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {current?.short ?? modelId}
        </span>
        {current?.free && <span style={{ fontSize: 10, color: "#10b981", fontWeight: 600 }}>FREE</span>}
        <ChevronDown size={12} color="#94a3b8" />
      </button>

      {open && (
        <div style={{
          position: "absolute", top: "100%", left: 8, right: 8, zIndex: 100,
          background: "#1e293b", border: "1px solid #334155", borderRadius: 10,
          boxShadow: "0 8px 32px rgba(0,0,0,0.5)", overflow: "hidden",
          maxHeight: 360, display: "flex", flexDirection: "column",
        }}>
          {/* Filter pills */}
          <div style={{ display: "flex", gap: 4, padding: "8px 10px", borderBottom: "1px solid #334155", flexShrink: 0 }}>
            {(["all", "free", "paid"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  padding: "3px 10px", borderRadius: 9999, border: "none", cursor: "pointer", fontSize: 11,
                  background: filter === f ? "#6366f1" : "#0f172a",
                  color: filter === f ? "white" : "#94a3b8",
                }}
              >
                {f === "all" ? "Tümü" : f === "free" ? "✓ Ücretsiz" : "Ücretli"}
              </button>
            ))}
          </div>

          {/* Model list */}
          <div style={{ overflowY: "auto" }}>
            {Object.entries(GROUPS).map(([group, ids]) => {
              const filtered = ids.filter((id) => {
                const info = MODELS[id];
                if (filter === "free") return info.free;
                if (filter === "paid") return !info.free;
                return true;
              });
              if (!filtered.length) return null;
              return (
                <div key={group}>
                  <div style={{ padding: "6px 12px 2px", fontSize: 10, color: "#4b5563", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.8px" }}>
                    {group}
                  </div>
                  {filtered.map((id) => {
                    const info = MODELS[id];
                    const isSelected = id === modelId;
                    return (
                      <div
                        key={id}
                        onClick={() => { setModelId(id); setOpen(false); }}
                        style={{
                          display: "flex", alignItems: "center", gap: 8,
                          padding: "7px 12px", cursor: "pointer", fontSize: 12,
                          background: isSelected ? "rgba(99,102,241,0.15)" : "transparent",
                          color: isSelected ? "#a5b4fc" : "#e2e8f0",
                        }}
                        onMouseEnter={(e) => { if (!isSelected) (e.currentTarget as HTMLDivElement).style.background = "rgba(255,255,255,0.04)"; }}
                        onMouseLeave={(e) => { if (!isSelected) (e.currentTarget as HTMLDivElement).style.background = "transparent"; }}
                      >
                        <span>{info.icon}</span>
                        <span style={{ flex: 1 }}>{info.short}</span>
                        {info.free && <span style={{ fontSize: 10, color: "#10b981" }}>FREE</span>}
                        {isSelected && <Check size={12} color="#6366f1" />}
                      </div>
                    );
                  })}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
