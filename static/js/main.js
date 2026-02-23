/**
 * Milli Yapay Zeka — Frontend Utilities
 * Served via FastAPI /static/js/main.js
 */

"use strict";

// ── Theme ──────────────────────────────────────────────────────────────────────

const Theme = (() => {
  const ROOT = document.documentElement;

  const DARK = {
    "--primary":    "#6366f1",
    "--primary-dark": "#4f46e5",
    "--secondary":  "#8b5cf6",
    "--success":    "#10b981",
    "--danger":     "#ef4444",
    "--warning":    "#f59e0b",
    "--dark":       "#0f172a",
    "--surface":    "#1e293b",
    "--surface2":   "#334155",
    "--text":       "#f8fafc",
    "--text-muted": "#94a3b8",
    "--border":     "#334155",
    "--code-bg":    "#0d1117",
  };

  function apply(vars) {
    Object.entries(vars).forEach(([k, v]) => ROOT.style.setProperty(k, v));
  }

  function init() {
    apply(DARK);
  }

  return { init, apply, DARK };
})();

// ── Toast Notifications ────────────────────────────────────────────────────────

const Toast = (() => {
  let container = null;

  function _ensureContainer() {
    if (container) return container;
    container = document.createElement("div");
    container.id = "myz-toasts";
    Object.assign(container.style, {
      position: "fixed",
      top: "16px",
      right: "16px",
      zIndex: "9999",
      display: "flex",
      flexDirection: "column",
      gap: "8px",
      pointerEvents: "none",
    });
    document.body.appendChild(container);
    return container;
  }

  /**
   * @param {string} message
   * @param {"success"|"danger"|"warning"|"primary"} type
   * @param {number} duration  ms
   */
  function show(message, type = "primary", duration = 3000) {
    const c = _ensureContainer();
    const el = document.createElement("div");
    const colorMap = {
      success: "var(--success)",
      danger:  "var(--danger)",
      warning: "var(--warning)",
      primary: "var(--primary)",
    };
    const color = colorMap[type] || colorMap.primary;

    Object.assign(el.style, {
      background:   "var(--surface)",
      border:       `1px solid ${color}`,
      borderLeft:   `4px solid ${color}`,
      color:        "var(--text)",
      borderRadius: "8px",
      padding:      "10px 16px",
      fontSize:     "13px",
      fontFamily:   "'Inter', sans-serif",
      boxShadow:    "0 4px 16px rgba(0,0,0,0.4)",
      opacity:      "0",
      transform:    "translateX(20px)",
      transition:   "all 0.25s ease",
      pointerEvents:"auto",
      maxWidth:     "320px",
    });
    el.textContent = message;
    c.appendChild(el);

    // Animate in
    requestAnimationFrame(() => {
      el.style.opacity = "1";
      el.style.transform = "translateX(0)";
    });

    // Animate out and remove
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transform = "translateX(20px)";
      setTimeout(() => el.remove(), 250);
    }, duration);
  }

  return { show };
})();

// ── Clipboard ─────────────────────────────────────────────────────────────────

const Clipboard = (() => {
  /**
   * Copy text to clipboard and show a toast.
   * @param {string} text
   * @param {string} [label]
   */
  async function copy(text, label = "Kopyalandı!") {
    try {
      await navigator.clipboard.writeText(text);
      Toast.show(`✅ ${label}`, "success", 2000);
    } catch {
      // Fallback for older browsers / iframe restrictions
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      Toast.show(`✅ ${label}`, "success", 2000);
    }
  }

  return { copy };
})();

// ── Code Block Enhancements ───────────────────────────────────────────────────

const CodeBlocks = (() => {
  /**
   * Add a "Copy" button to every <pre><code> block on the page.
   */
  function enhanceAll() {
    document.querySelectorAll("pre").forEach((pre) => {
      if (pre.dataset.enhanced) return;
      pre.dataset.enhanced = "1";

      pre.style.position = "relative";

      const btn = document.createElement("button");
      btn.textContent = "Kopyala";
      Object.assign(btn.style, {
        position:     "absolute",
        top:          "8px",
        right:        "8px",
        background:   "var(--surface2)",
        color:        "var(--text-muted)",
        border:       "1px solid var(--border)",
        borderRadius: "6px",
        padding:      "3px 10px",
        fontSize:     "11px",
        cursor:       "pointer",
        fontFamily:   "'Inter', sans-serif",
        transition:   "all 0.15s",
        zIndex:       "1",
      });

      btn.addEventListener("mouseenter", () => {
        btn.style.color = "var(--text)";
        btn.style.borderColor = "var(--primary)";
      });
      btn.addEventListener("mouseleave", () => {
        btn.style.color = "var(--text-muted)";
        btn.style.borderColor = "var(--border)";
      });
      btn.addEventListener("click", () => {
        const code = pre.querySelector("code");
        const text = code ? code.innerText : pre.innerText;
        Clipboard.copy(text, "Kod kopyalandı!");
        btn.textContent = "✅ Kopyalandı";
        setTimeout(() => { btn.textContent = "Kopyala"; }, 1800);
      });

      pre.appendChild(btn);
    });
  }

  return { enhanceAll };
})();

// ── Chat Helpers ──────────────────────────────────────────────────────────────

const Chat = (() => {
  /**
   * Scroll the given container (or window) to the bottom smoothly.
   * @param {HTMLElement|null} el
   */
  function scrollToBottom(el = null) {
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    } else {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    }
  }

  /**
   * Auto-grow a textarea as the user types.
   * @param {HTMLTextAreaElement} textarea
   * @param {number} maxRows
   */
  function autoGrow(textarea, maxRows = 8) {
    textarea.style.overflowY = "hidden";
    textarea.style.height = "auto";
    const lineHeight = parseInt(getComputedStyle(textarea).lineHeight) || 20;
    const maxHeight  = lineHeight * maxRows;
    const newHeight  = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = newHeight + "px";
    textarea.style.overflowY = newHeight >= maxHeight ? "auto" : "hidden";
  }

  return { scrollToBottom, autoGrow };
})();

// ── Pomodoro Timer ────────────────────────────────────────────────────────────

const Pomodoro = (() => {
  const WORK  = 25 * 60;
  const BREAK =  5 * 60;

  let total   = WORK;
  let left    = WORK;
  let running = false;
  let timer   = null;
  let cycles  = 0;
  let isWork  = true;

  function _pad(n) { return String(n).padStart(2, "0"); }

  function _notify(msg) {
    if (typeof Notification !== "undefined" && Notification.permission === "granted") {
      new Notification(msg);
    }
  }

  function _tick() {
    if (left <= 0) {
      clearInterval(timer);
      running = false;
      if (isWork) cycles++;
      isWork = !isWork;
      total  = isWork ? WORK : BREAK;
      left   = total;
      _notify(isWork ? "🍅 Çalışma başlıyor!" : "☕ Mola zamanı!");
      _emit("phase-change", { isWork, cycles });
      return;
    }
    left--;
    _emit("tick", { left, total, isWork });
  }

  function _emit(name, detail) {
    document.dispatchEvent(new CustomEvent("pomodoro:" + name, { detail }));
  }

  function start() {
    if (running) return;
    if (typeof Notification !== "undefined") Notification.requestPermission();
    timer   = setInterval(_tick, 1000);
    running = true;
    _emit("start", { left, total, isWork });
  }

  function pause() {
    clearInterval(timer);
    running = false;
    _emit("pause", { left, total, isWork });
  }

  function toggle() { running ? pause() : start(); }

  function reset() {
    clearInterval(timer);
    running = false;
    isWork  = true;
    total   = WORK;
    left    = WORK;
    _emit("reset", { left, total, isWork });
  }

  function getState() {
    return {
      left, total, running, cycles, isWork,
      formatted: _pad(Math.floor(left / 60)) + ":" + _pad(left % 60),
    };
  }

  return { start, pause, toggle, reset, getState };
})();

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  Theme.init();
  CodeBlocks.enhanceAll();

  // Re-run code block enhancement when new content is added (e.g. after AI response)
  const observer = new MutationObserver(() => CodeBlocks.enhanceAll());
  observer.observe(document.body, { childList: true, subtree: true });
});

// Export for external use (non-module environments)
window.MYZ = { Theme, Toast, Clipboard, CodeBlocks, Chat, Pomodoro };
