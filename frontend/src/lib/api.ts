const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function listFiles(workspace = "default") {
  const r = await fetch(`${API_BASE}/api/ide/files?workspace=${encodeURIComponent(workspace)}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function readFile(path: string, workspace = "default") {
  const r = await fetch(`${API_BASE}/api/ide/files/read?path=${encodeURIComponent(path)}&workspace=${encodeURIComponent(workspace)}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function writeFile(path: string, content: string, workspace = "default") {
  const r = await fetch(`${API_BASE}/api/ide/files/write`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, content, workspace }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function deleteFile(path: string, workspace = "default") {
  const r = await fetch(`${API_BASE}/api/ide/files/delete?path=${encodeURIComponent(path)}&workspace=${encodeURIComponent(workspace)}`, {
    method: "DELETE",
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function renameFile(oldPath: string, newPath: string, workspace = "default") {
  const r = await fetch(`${API_BASE}/api/ide/files/rename`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ old_path: oldPath, new_path: newPath, workspace }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function runCommand(command: string, workspace = "default", timeout = 60) {
  const r = await fetch(`${API_BASE}/api/ide/terminal/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command, workspace, timeout }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export function streamAgent(
  messages: Array<{ role: string; content: string }>,
  modelId: string,
  apiKey: string | null,
  workspace: string,
  onEvent: (event: Record<string, unknown>) => void,
  onError: (err: string) => void,
  onDone: () => void,
): AbortController {
  const ctrl = new AbortController();
  (async () => {
    try {
      const r = await fetch(`${API_BASE}/api/ide/agent/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages, model_id: modelId, api_key: apiKey, workspace }),
        signal: ctrl.signal,
      });
      if (!r.ok) {
        onError(await r.text());
        return;
      }
      const reader = r.body!.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const ev = JSON.parse(line.slice(6));
              if (ev.type === "error") { onError(ev.content ?? String(ev)); onDone(); return; }
              onEvent(ev);
              if (ev.type === "end" || ev.type === "done") { onDone(); return; }
            } catch {}
          }
        }
      }
      onDone();
    } catch (e: unknown) {
      if ((e as Error).name !== "AbortError") onError(String(e));
    }
  })();
  return ctrl;
}

export function streamTerminal(
  command: string,
  workspace: string,
  onLine: (line: string) => void,
  onDone: (code: number) => void,
): AbortController {
  const ctrl = new AbortController();
  (async () => {
    try {
      const r = await fetch(`${API_BASE}/api/ide/terminal/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command, workspace }),
        signal: ctrl.signal,
      });
      const reader = r.body!.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split("\n");
        buf = lines.pop() ?? "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const ev = JSON.parse(line.slice(6));
              if (ev.type === "output") onLine(ev.content);
              if (ev.type === "done") onDone(ev.code ?? 0);
            } catch {}
          }
        }
      }
    } catch {}
  })();
  return ctrl;
}
