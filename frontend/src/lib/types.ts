export interface FileNode {
  type: "file" | "dir";
  name: string;
  path: string;
  size?: number;
  children?: FileNode[];
}

export interface Attachment {
  name: string;
  content: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCall[];
  attachments?: Attachment[];
  timestamp: Date;
}

export interface ToolCall {
  id: string;
  tool: string;
  input: Record<string, unknown>;
  output?: string;
  status: "running" | "done" | "error";
}

export interface ModelInfo {
  id: string;
  display: string;
  short: string;
  provider: string;
  free: boolean;
  icon: string;
  color: string;
  group: string;
}

export const MODELS: Record<string, ModelInfo> = {
  "claude-opus-4-6":       { id: "claude-opus-4-6",       display: "Claude Opus 4.6",         short: "Opus 4.6",       provider: "anthropic", free: false, icon: "🔶", color: "#ff6b35", group: "Claude" },
  "claude-sonnet-4-5":     { id: "claude-sonnet-4-5",     display: "Claude Sonnet 4.5",       short: "Sonnet 4.5",     provider: "anthropic", free: false, icon: "🔶", color: "#ff6b35", group: "Claude" },
  "claude-haiku-3-5-20241022": { id: "claude-haiku-3-5-20241022", display: "Claude Haiku 3.5", short: "Haiku 3.5",  provider: "anthropic", free: false, icon: "🔶", color: "#ff6b35", group: "Claude" },
  "gemini-2.0-flash-exp":  { id: "gemini-2.0-flash-exp",  display: "Gemini 2.0 Flash",        short: "Gemini 2.0",     provider: "gemini",    free: true,  icon: "💎", color: "#4285f4", group: "Gemini" },
  "gemini-1.5-flash":      { id: "gemini-1.5-flash",      display: "Gemini 1.5 Flash",        short: "Gemini 1.5",     provider: "gemini",    free: true,  icon: "💎", color: "#4285f4", group: "Gemini" },
  "glm-4-flash":           { id: "glm-4-flash",           display: "GLM-4 Flash (Ücretsiz)",  short: "GLM-4 Flash",    provider: "glm",       free: true,  icon: "🌊", color: "#00c4cc", group: "GLM" },
  "glm-4-plus":            { id: "glm-4-plus",            display: "GLM-4 Plus",              short: "GLM-4+",         provider: "glm",       free: false, icon: "🌊", color: "#00c4cc", group: "GLM" },
  "llama-3.3-70b-versatile":     { id: "llama-3.3-70b-versatile",     display: "Llama 3.3 70B (Groq)",    short: "Llama 3.3 70B",  provider: "groq",      free: true,  icon: "🦙", color: "#7c3aed", group: "Groq" },
  "llama-3.1-8b-instant":        { id: "llama-3.1-8b-instant",        display: "Llama 3.1 8B (Groq)",     short: "Llama 3.1 8B",   provider: "groq",      free: true,  icon: "🦙", color: "#7c3aed", group: "Groq" },
  "mixtral-8x7b-32768":          { id: "mixtral-8x7b-32768",          display: "Mixtral 8x7B (Groq)",     short: "Mixtral 8x7B",   provider: "groq",      free: true,  icon: "🦙", color: "#7c3aed", group: "Groq" },
  "deepseek-r1-distill-llama-70b": { id: "deepseek-r1-distill-llama-70b", display: "DeepSeek R1 70B (Groq)", short: "DeepSeek R1",  provider: "groq",      free: true,  icon: "🦙", color: "#7c3aed", group: "Groq" },
  "meta-llama/llama-3.2-11b-vision-instruct:free": { id: "meta-llama/llama-3.2-11b-vision-instruct:free", display: "Llama 3.2 11B (OR)", short: "Llama 3.2 11B", provider: "openrouter", free: true, icon: "🌐", color: "#059669", group: "OpenRouter" },
  "deepseek/deepseek-r1:free":    { id: "deepseek/deepseek-r1:free",    display: "DeepSeek R1 (OR)",        short: "DeepSeek R1",    provider: "openrouter", free: true,  icon: "🌐", color: "#059669", group: "OpenRouter" },
  "qwen/qwen-2.5-72b-instruct:free": { id: "qwen/qwen-2.5-72b-instruct:free", display: "Qwen 2.5 72B (OR)", short: "Qwen 2.5 72B", provider: "openrouter", free: true,  icon: "🌐", color: "#059669", group: "OpenRouter" },
  "mistralai/mistral-7b-instruct:free": { id: "mistralai/mistral-7b-instruct:free", display: "Mistral 7B (OR)", short: "Mistral 7B", provider: "openrouter", free: true, icon: "🌐", color: "#059669", group: "OpenRouter" },
};

export const PROVIDER_KEY_LABELS: Record<string, { label: string; placeholder: string; hint: string }> = {
  anthropic:   { label: "Anthropic API Key",   placeholder: "sk-ant-...",      hint: "console.anthropic.com" },
  google:      { label: "Google API Key",       placeholder: "AIza...",         hint: "aistudio.google.com" },
  zhipuai:     { label: "ZhipuAI API Key",      placeholder: "zhipuai_...",     hint: "open.bigmodel.cn" },
  groq:        { label: "Groq API Key (Ücretsiz)", placeholder: "gsk_...",      hint: "console.groq.com" },
  openrouter:  { label: "OpenRouter API Key (Ücretsiz)", placeholder: "sk-or-...", hint: "openrouter.ai" },
};

export type ApiKeys = Record<string, string>;
