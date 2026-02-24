"use client";
import dynamic from "next/dynamic";

// IDE ağır bileşenler içerdiği için dynamic import ile yükle
const IDE = dynamic(() => import("@/components/IDE"), {
  ssr: false,
  loading: () => (
    <div style={{
      height: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      background: "#0f172a", color: "#94a3b8", flexDirection: "column", gap: 16,
    }}>
      <div style={{ fontSize: 40 }}>⚡</div>
      <div style={{ fontSize: 16, fontWeight: 600 }}>AI IDE Yükleniyor...</div>
    </div>
  ),
});

export default function Home() {
  return <IDE />;
}
