import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { FileNode, ChatMessage, ApiKeys } from "@/lib/types";

interface IDEState {
  // Workspace
  workspace: string;
  setWorkspace: (w: string) => void;

  // Files
  files: FileNode[];
  setFiles: (f: FileNode[]) => void;
  openFiles: string[];          // açık tab'lar
  activeFile: string | null;    // aktif dosya yolu
  fileContents: Record<string, string>;
  openFile: (path: string, content: string) => void;
  closeFile: (path: string) => void;
  setFileContent: (path: string, content: string) => void;
  setActiveFile: (path: string) => void;

  // Editor
  unsavedFiles: Set<string>;
  markUnsaved: (path: string) => void;
  markSaved: (path: string) => void;

  // Chat
  messages: ChatMessage[];
  addMessage: (msg: ChatMessage) => void;
  updateLastMessage: (updater: (msg: ChatMessage) => ChatMessage) => void;
  clearMessages: () => void;

  // Model & Keys
  modelId: string;
  setModelId: (id: string) => void;
  apiKeys: ApiKeys;
  setApiKey: (provider: string, key: string) => void;

  // UI panels
  showSettings: boolean;
  toggleSettings: () => void;
  terminalHeight: number;
  setTerminalHeight: (h: number) => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  sidebarWidth: number;
  setSidebarWidth: (w: number) => void;
  chatWidth: number;
  setChatWidth: (w: number) => void;
  terminalOpen: boolean;
  toggleTerminal: () => void;
}

export const useIDEStore = create<IDEState>()(
  persist(
    (set, get) => ({
      workspace: "default",
      setWorkspace: (workspace) => set({ workspace }),

      files: [],
      setFiles: (files) => set({ files }),
      openFiles: [],
      activeFile: null,
      fileContents: {},
      openFile: (path, content) => {
        const { openFiles, fileContents } = get();
        const newOpen = openFiles.includes(path) ? openFiles : [...openFiles, path];
        set({
          openFiles: newOpen,
          activeFile: path,
          fileContents: { ...fileContents, [path]: content },
        });
      },
      closeFile: (path) => {
        const { openFiles, activeFile } = get();
        const idx = openFiles.indexOf(path);
        const newOpen = openFiles.filter((p) => p !== path);
        let newActive = activeFile;
        if (activeFile === path) {
          newActive = newOpen[Math.max(0, idx - 1)] ?? null;
        }
        set({ openFiles: newOpen, activeFile: newActive });
      },
      setFileContent: (path, content) => {
        set((s) => ({ fileContents: { ...s.fileContents, [path]: content } }));
      },
      setActiveFile: (path) => set({ activeFile: path }),

      unsavedFiles: new Set(),
      markUnsaved: (path) => set((s) => ({ unsavedFiles: new Set([...s.unsavedFiles, path]) })),
      markSaved: (path) => set((s) => {
        const n = new Set(s.unsavedFiles); n.delete(path); return { unsavedFiles: n };
      }),

      messages: [],
      addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
      updateLastMessage: (updater) => set((s) => {
        if (!s.messages.length) return s;
        const msgs = [...s.messages];
        msgs[msgs.length - 1] = updater(msgs[msgs.length - 1]);
        return { messages: msgs };
      }),
      clearMessages: () => set({ messages: [] }),

      modelId: "llama-3.3-70b-versatile",
      setModelId: (modelId) => set({ modelId }),
      apiKeys: {},
      setApiKey: (provider, key) => set((s) => ({
        apiKeys: { ...s.apiKeys, [provider]: key },
      })),

      showSettings: false,
      toggleSettings: () => set((s) => ({ showSettings: !s.showSettings })),
      sidebarOpen: true,
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      terminalHeight: 200,
      setTerminalHeight: (terminalHeight) => set({ terminalHeight }),
      sidebarWidth: 240,
      setSidebarWidth: (sidebarWidth) => set({ sidebarWidth }),
      chatWidth: 380,
      setChatWidth: (chatWidth) => set({ chatWidth }),
      terminalOpen: true,
      toggleTerminal: () => set((s) => ({ terminalOpen: !s.terminalOpen })),
    }),
    {
      name: "ai-ide-state",
      partialize: (s) => ({
        workspace: s.workspace,
        modelId: s.modelId,
        apiKeys: s.apiKeys,
        sidebarOpen: s.sidebarOpen,
        sidebarWidth: s.sidebarWidth,
        chatWidth: s.chatWidth,
        terminalHeight: s.terminalHeight,
        terminalOpen: s.terminalOpen,
      }),
    }
  )
);
