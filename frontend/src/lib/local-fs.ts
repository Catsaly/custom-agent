import type { FileNode } from "./types";

// File System Access API - TypeScript DOM lib eksik tip bildirimi
declare global {
  interface FileSystemDirectoryHandle {
    values(): AsyncIterableIterator<FileSystemHandle>;
  }
}

/** File System Access API (Chrome/Edge/Safari 15.2+) supported? */
export const hasLocalFSSupport =
  typeof window !== "undefined" && "showDirectoryPicker" in window;

/** Recursively build a FileNode tree from a directory handle. */
export async function buildLocalTree(
  dirHandle: FileSystemDirectoryHandle,
  basePath = "",
): Promise<FileNode[]> {
  const nodes: FileNode[] = [];
  for await (const entry of dirHandle.values()) {
    const path = basePath ? `${basePath}/${entry.name}` : entry.name;
    if (entry.kind === "file") {
      nodes.push({ name: entry.name, path, type: "file" });
    } else {
      const children = await buildLocalTree(
        entry as FileSystemDirectoryHandle,
        path,
      );
      nodes.push({ name: entry.name, path, type: "dir", children });
    }
  }
  return nodes.sort((a, b) => {
    if (a.type !== b.type) return a.type === "dir" ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
}

/** Navigate path segments and return the FileSystemFileHandle. */
async function resolveFileHandle(
  root: FileSystemDirectoryHandle,
  filePath: string,
): Promise<FileSystemFileHandle | null> {
  const parts = filePath.split("/").filter(Boolean);
  let dir: FileSystemDirectoryHandle = root;
  for (let i = 0; i < parts.length - 1; i++) {
    try {
      dir = await dir.getDirectoryHandle(parts[i]);
    } catch {
      return null;
    }
  }
  try {
    return await dir.getFileHandle(parts[parts.length - 1]);
  } catch {
    return null;
  }
}

/** Read a local file as text. */
export async function readLocalFile(
  root: FileSystemDirectoryHandle,
  filePath: string,
): Promise<string> {
  const fh = await resolveFileHandle(root, filePath);
  if (!fh) throw new Error(`Dosya bulunamadı: ${filePath}`);
  const file = await fh.getFile();
  return file.text();
}

/** Write content back to a local file. */
export async function writeLocalFile(
  root: FileSystemDirectoryHandle,
  filePath: string,
  content: string,
): Promise<void> {
  const fh = await resolveFileHandle(root, filePath);
  if (!fh) throw new Error(`Dosya bulunamadı: ${filePath}`);
  const writable = await fh.createWritable();
  await writable.write(content);
  await writable.close();
}

/** Parse a webkitdirectory FileList into a FileNode tree + content map. */
export function parseUploadedFileList(fileList: FileList): {
  tree: FileNode[];
  contents: Record<string, string>;
  promises: Promise<void>[];
} {
  const contents: Record<string, string> = {};
  const root: Record<string, FileNode> = {};
  const promises: Promise<void>[] = [];

  Array.from(fileList).forEach((file) => {
    const path = (file as File & { webkitRelativePath: string }).webkitRelativePath || file.name;
    const parts = path.split("/");

    // Build tree structure
    let current = root;
    parts.forEach((part, idx) => {
      if (!current[part]) {
        current[part] = {
          name: part,
          path: parts.slice(0, idx + 1).join("/"),
          type: idx === parts.length - 1 ? "file" : "dir",
          children: idx < parts.length - 1 ? [] : undefined,
        } as FileNode;
        if (idx < parts.length - 1) {
          current[part].children = [];
        }
      }
      if (idx < parts.length - 1) {
        const childMap: Record<string, FileNode> = {};
        (current[part].children ?? []).forEach((c) => (childMap[c.name] = c));
        current = childMap;
      }
    });

    // Read content
    const p = file.text().then((text) => {
      contents[path] = text;
    });
    promises.push(p);
  });

  // Convert root map to array (skip the root dir wrapper if present)
  const entries = Object.values(root);
  const tree = entries.length === 1 && entries[0].type === "dir"
    ? entries[0].children ?? entries
    : entries;

  return { tree, contents, promises };
}

/** Trigger a browser download of a file. */
export function downloadFile(filename: string, content: string): void {
  const blob = new Blob([content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename.split("/").pop() ?? filename;
  a.click();
  URL.revokeObjectURL(url);
}
