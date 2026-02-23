"""
Milli Yapay Zeka — Yerli AI Kodlama Platformu
Built with Streamlit + FastAPI + Claude + Gemini + GLM + Supabase + Bootstrap
"""
import streamlit as st
import asyncio
import json
import uuid
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Milli Yapay Zeka",
    page_icon="🇹🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Bootstrap + Custom CSS Injection ─────────────────────────────────────────
BOOTSTRAP_CSS = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --secondary: #8b5cf6;
    --success: #10b981;
    --danger: #ef4444;
    --dark: #0f172a;
    --surface: #1e293b;
    --surface2: #334155;
    --text: #f8fafc;
    --text-muted: #94a3b8;
    --border: #334155;
    --code-bg: #0d1117;
}
* { box-sizing: border-box; }
body { font-family: 'Inter', sans-serif; background: var(--dark) !important; color: var(--text) !important; }

/* Streamlit Core Overrides */
.stApp { background: var(--dark) !important; }
.stSidebar, [data-testid="stSidebar"] { background: var(--surface) !important; border-right: 1px solid var(--border); }
.stSidebar .stMarkdown, .stSidebar label { color: var(--text) !important; }
div[data-testid="stToolbar"] { display: none; }
.stDeployButton { display: none; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--primary), var(--secondary)) !important;
    color: white !important; border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; padding: 8px 20px !important;
    transition: all 0.2s !important; box-shadow: 0 2px 8px rgba(99,102,241,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important; box-shadow: 0 6px 20px rgba(99,102,241,0.5) !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: var(--surface2) !important; color: var(--text) !important;
    border: 1px solid var(--border) !important; border-radius: 8px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary) !important; box-shadow: 0 0 0 2px rgba(99,102,241,0.3) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important; border-radius: 10px; gap: 4px; padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: var(--text-muted) !important;
    border-radius: 8px !important; padding: 6px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: var(--primary) !important; color: white !important;
}

/* Code blocks */
pre { background: var(--code-bg) !important; border: 1px solid var(--border) !important; border-radius: 10px !important; }
code { font-family: 'JetBrains Mono', monospace !important; }

/* Markdown */
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--text) !important; }
.stMarkdown p { color: var(--text) !important; }

/* Chat */
.chat-container { display: flex; flex-direction: column; gap: 16px; padding: 16px 0; }
.msg-wrapper { display: flex; width: 100%; }
.msg-wrapper.user { justify-content: flex-end; }
.msg-wrapper.assistant { justify-content: flex-start; }
.msg-bubble {
    max-width: 85%; padding: 12px 18px; border-radius: 16px;
    line-height: 1.6; animation: fadeUp 0.3s ease;
}
.msg-bubble.user {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white; border-bottom-right-radius: 4px;
}
.msg-bubble.assistant {
    background: var(--surface2); border: 1px solid var(--border);
    color: var(--text); border-bottom-left-radius: 4px;
}
.msg-meta { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

/* File Tree */
.ftree-item {
    display: flex; align-items: center; gap: 8px; padding: 5px 8px;
    border-radius: 6px; cursor: pointer; transition: background 0.15s; font-size: 13px;
}
.ftree-item:hover { background: var(--surface2); }
.ftree-item.selected { background: rgba(99,102,241,0.2); color: var(--primary); }

/* Cards */
.ai-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px; transition: all 0.2s;
}
.ai-card:hover { border-color: var(--primary); box-shadow: 0 0 0 1px var(--primary); }

/* Model pills */
.model-pill {
    display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px;
    border-radius: 9999px; font-size: 12px; font-weight: 600; cursor: pointer;
    transition: all 0.2s; border: 2px solid transparent;
}
.pill-claude { background: rgba(255,107,53,0.15); color: #ff8c5f; border-color: #ff6b35; }
.pill-gemini { background: rgba(66,133,244,0.15); color: #6fa8f0; border-color: #4285f4; }
.pill-glm { background: rgba(0,196,204,0.15); color: #4ddde0; border-color: #00c4cc; }
.pill-active { transform: scale(1.05); box-shadow: 0 0 12px rgba(0,0,0,0.3); }

/* Status */
.status-dot {
    width: 8px; height: 8px; border-radius: 50%; display: inline-block;
}
.dot-success { background: var(--success); box-shadow: 0 0 6px var(--success); }
.dot-danger { background: var(--danger); }
.dot-muted { background: var(--text-muted); }

/* Animations */
@keyframes fadeUp { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:translateY(0); } }
@keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
.blink { animation: blink 1.2s infinite; }
@keyframes spin { from{transform:rotate(0deg);} to{transform:rotate(360deg);} }
.spin { animation: spin 1s linear infinite; display:inline-block; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--dark); }
::-webkit-scrollbar-thumb { background: var(--surface2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--primary); }

/* Metrics */
.metric-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px 16px; text-align: center;
}
.metric-value { font-size: 28px; font-weight: 700; color: var(--primary); }
.metric-label { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

/* Toolbar */
.toolbar {
    display: flex; align-items: center; gap: 8px; padding: 10px 16px;
    background: var(--surface); border-bottom: 1px solid var(--border);
    border-radius: 10px 10px 0 0;
}
</style>
"""
st.markdown(BOOTSTRAP_CSS, unsafe_allow_html=True)

# ── Session State Init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "model": "claude",
        "current_file": None,
        "file_content": "",
        "workspace_path": "workspace/default",
        "project_name": "Milli Yapay Zeka",
        "github_repo": "",
        "auto_save": True,
        "theme": "dark",
        "sidebar_tab": "files",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

API_URL = "http://localhost:8000/api"


def api_get(path: str, **params) -> Optional[dict]:
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=10)
        return r.json() if r.ok else None
    except Exception:
        return None


def api_post(path: str, data: dict) -> Optional[dict]:
    try:
        r = requests.post(f"{API_URL}{path}", json=data, timeout=30)
        return r.json() if r.ok else None
    except Exception:
        return None


def model_icon(model: str) -> str:
    return {"claude": "🔶", "gemini": "💎", "glm": "🌊"}.get(model, "🤖")

def model_color(model: str) -> str:
    return {"claude": "#ff6b35", "gemini": "#4285f4", "glm": "#00c4cc"}.get(model, "#6366f1")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo / Header
    st.markdown("""
    <div style="padding:16px 0 24px; text-align:center;">
        <div style="font-size:32px;">🇹🇷</div>
        <div style="font-size:20px; font-weight:700; color:#f8fafc; letter-spacing:-0.5px;">Milli Yapay Zeka</div>
        <div style="font-size:11px; color:#94a3b8;">Yerli AI Kodlama Platformu</div>
    </div>
    """, unsafe_allow_html=True)

    # Model Selector
    st.markdown("<div style='font-size:12px; color:#94a3b8; margin-bottom:8px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;'>AI Model</div>", unsafe_allow_html=True)
    model_cols = st.columns(3)
    for i, (m, label, icon) in enumerate([
        ("claude", "Claude", "🔶"),
        ("gemini", "Gemini", "💎"),
        ("glm", "GLM", "🌊"),
    ]):
        with model_cols[i]:
            if st.button(f"{icon}\n{label}", key=f"model_{m}",
                         use_container_width=True,
                         type="primary" if st.session_state.model == m else "secondary"):
                st.session_state.model = m
                st.rerun()

    st.divider()

    # Project
    st.markdown("**Project**")
    project_name = st.text_input("Name", value=st.session_state.project_name, label_visibility="collapsed")
    st.session_state.project_name = project_name
    workspace = st.text_input("Workspace", value=st.session_state.workspace_path, label_visibility="collapsed")
    st.session_state.workspace_path = workspace

    st.divider()

    # Sidebar Tabs
    stab = st.radio("View", ["📁 Files", "🐙 GitHub", "⚙️ Settings"],
                    horizontal=True, label_visibility="collapsed")

    if "Files" in stab:
        st.markdown("**File Tree**")
        tree_data = api_get("/files/tree")
        if tree_data and tree_data.get("tree"):
            def render_tree(node, depth=0):
                indent = "&nbsp;" * (depth * 4)
                icon = "📁" if node["type"] == "directory" else _file_icon(node["name"])
                label = f"{indent}{icon} {node['name']}"
                is_selected = st.session_state.current_file == node.get("path")
                style = "color:#6366f1; font-weight:600;" if is_selected else ""
                if node["type"] == "file":
                    if st.button(f"{node['name']}", key=f"ft_{node['path']}",
                                 use_container_width=True):
                        st.session_state.current_file = node["path"]
                        file_data = api_get("/files/read", path=node["path"])
                        if file_data:
                            st.session_state.file_content = file_data.get("content", "")
                        st.rerun()
                else:
                    st.markdown(f"<div class='ftree-item'>{label}</div>", unsafe_allow_html=True)
                for child in node.get("children", []):
                    render_tree(child, depth + 1)
            render_tree(tree_data["tree"])
        else:
            st.caption("No files yet. Ask AI to generate a project!")

        if st.button("📄 New File", use_container_width=True):
            filename = st.text_input("Filename", key="new_file_input")
            if filename:
                api_post("/files/write", {"path": filename, "content": ""})
                st.rerun()

    elif "GitHub" in stab:
        st.markdown("**GitHub**")
        repo = st.text_input("Repository (owner/name)", value=st.session_state.github_repo)
        st.session_state.github_repo = repo
        if repo:
            if st.button("🔍 Analyze Repo", use_container_width=True):
                with st.spinner("Analyzing..."):
                    parts = repo.split("/")
                    if len(parts) == 2:
                        result = api_get(f"/github/repo/{parts[0]}/{parts[1]}/analyze")
                        if result:
                            st.info(result.get("analysis", ""))
        if st.button("🚀 Deploy to GitHub", use_container_width=True):
            if repo:
                with st.spinner("Deploying..."):
                    result = api_post("/github/deploy", {
                        "workspace_path": st.session_state.workspace_path,
                        "repo_name": repo,
                        "commit_message": f"Deploy from CodeCraft AI - {datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    })
                    if result:
                        st.success(f"Deployed {result.get('deployed', 0)} files")
                    else:
                        st.error("Deploy failed. Check GitHub token.")
            else:
                st.warning("Enter a repository name first")

    else:  # Settings
        st.markdown("**Settings**")
        st.session_state.auto_save = st.toggle("Auto Save", value=st.session_state.auto_save)
        st.selectbox("Theme", ["Dark", "Light"], index=0, disabled=True)
        st.markdown("**About**")
        st.caption("CodeCraft AI v1.0.0")
        st.caption("Powered by Claude, Gemini & GLM")
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        if st.button("🆕 New Session", use_container_width=True):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()


def _file_icon(name: str) -> str:
    ext = Path(name).suffix.lower()
    icons = {
        ".py": "🐍", ".js": "🟨", ".ts": "💙", ".tsx": "⚛️",
        ".html": "🌐", ".css": "🎨", ".json": "📋", ".md": "📝",
        ".sh": "🔧", ".yaml": "⚙️", ".yml": "⚙️", ".sql": "🗄️",
        ".go": "🐹", ".rs": "🦀", ".java": "☕",
    }
    return icons.get(ext, "📄")


# ── Main Layout ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex; align-items:center; justify-content:space-between; padding:8px 0 16px;">
    <div>
        <span style="font-size:22px; font-weight:700;">{st.session_state.project_name}</span>
        <span style="margin-left:12px; font-size:13px; color:#94a3b8;">Session: {st.session_state.session_id[:8]}...</span>
    </div>
    <div style="display:flex; gap:8px; align-items:center;">
        <span class="model-pill pill-{st.session_state.model}">{model_icon(st.session_state.model)} {st.session_state.model.upper()}</span>
        <span style="font-size:12px; color:#94a3b8;">{datetime.now().strftime('%H:%M')}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab_chat, tab_editor, tab_generate, tab_tools = st.tabs([
    "💬 Chat", "📝 Editor", "🚀 Generate", "🔧 Tools"
])


# ── CHAT TAB ─────────────────────────────────────────────────────────────────
with tab_chat:
    # Messages display
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; color:#64748b;">
                <div style="font-size:48px; margin-bottom:16px;">🇹🇷</div>
                <div style="font-size:20px; font-weight:600; color:#94a3b8; margin-bottom:8px;">Milli Yapay Zeka'ya Hoş Geldiniz</div>
                <div style="font-size:14px;">Web uygulaması, API, script — ne istersen söyle, hemen üretelim.</div>
                <div style="margin-top:24px; display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
                    <span style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:8px 16px; font-size:13px; cursor:pointer;">Build a FastAPI REST API</span>
                    <span style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:8px 16px; font-size:13px; cursor:pointer;">Create a React dashboard</span>
                    <span style="background:#1e293b; border:1px solid #334155; border-radius:8px; padding:8px 16px; font-size:13px; cursor:pointer;">Write a Python data pipeline</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                role = msg["role"]
                content = msg["content"]
                model_used = msg.get("model", st.session_state.model)
                ts = msg.get("timestamp", "")
                align = "user" if role == "user" else "assistant"
                icon = "👤" if role == "user" else model_icon(model_used)
                st.markdown(f"""
                <div class="msg-wrapper {align}">
                    <div>
                        <div class="msg-bubble {align}">{content}</div>
                        <div class="msg-meta" style="text-align:{'right' if role=='user' else 'left'};">
                            {icon} {model_used if role=='assistant' else 'You'} · {ts}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # Input area
    col_input, col_send = st.columns([6, 1])
    with col_input:
        user_input = st.text_area(
            "Message",
            placeholder=f"Ask {st.session_state.model.upper()} to build something...",
            height=80,
            label_visibility="collapsed",
            key="chat_input",
        )
    with col_send:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        send = st.button("Send ➤", use_container_width=True, type="primary")

    # Quick actions
    qcols = st.columns(4)
    quick_actions = [
        ("🔍 Explain", "Explain this code: "),
        ("🐛 Fix Bug", "Find and fix bugs in: "),
        ("✨ Refactor", "Refactor and improve: "),
        ("📚 Document", "Add documentation to: "),
    ]
    for i, (label, prefix) in enumerate(quick_actions):
        with qcols[i]:
            if st.button(label, use_container_width=True, key=f"qa_{i}"):
                context = st.session_state.file_content[:500] if st.session_state.file_content else ""
                user_input = prefix + context
                send = True

    if send and user_input.strip():
        # Add user message
        ts = datetime.now().strftime("%H:%M")
        st.session_state.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": ts,
        })

        # Get AI response
        with st.spinner(f"{model_icon(st.session_state.model)} {st.session_state.model.upper()} is thinking..."):
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages[:-1]
            ]
            result = api_post("/chat/message", {
                "prompt": user_input,
                "model": st.session_state.model,
                "messages": history,
                "workspace_path": st.session_state.workspace_path,
            })

        response_text = result.get("response", "Sorry, I couldn't process that.") if result else "API error — is the backend running?"
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "model": st.session_state.model,
            "timestamp": datetime.now().strftime("%H:%M"),
        })
        st.rerun()

    # Image upload
    with st.expander("📷 Upload Image for Analysis"):
        img_file = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed")
        img_prompt = st.text_input("What to analyze?", value="Describe this image and suggest code to implement it")
        if img_file and st.button("Analyze Image"):
            with st.spinner("Analyzing image..."):
                import io
                files = {"file": (img_file.name, img_file.getvalue(), img_file.type)}
                data = {"prompt": img_prompt, "model": st.session_state.model, "analyze": "true"}
                try:
                    r = requests.post(f"{API_URL}/images/upload", files=files, data=data, timeout=30)
                    if r.ok:
                        analysis = r.json().get("analysis", "No analysis returned")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"**Image Analysis:**\n\n{analysis}",
                            "model": st.session_state.model,
                            "timestamp": datetime.now().strftime("%H:%M"),
                        })
                        st.rerun()
                    else:
                        st.error("Image analysis failed")
                except Exception as e:
                    st.error(f"Error: {e}")


# ── EDITOR TAB ────────────────────────────────────────────────────────────────
with tab_editor:
    ecol1, ecol2 = st.columns([1, 2])

    with ecol1:
        st.markdown("**Files**")
        # New file
        new_filename = st.text_input("New file name", placeholder="app.py", key="editor_new_file")
        if st.button("➕ Create", key="create_file_btn"):
            if new_filename:
                result = api_post("/files/write", {"path": new_filename, "content": f"# {new_filename}\n"})
                if result:
                    st.session_state.current_file = new_filename
                    st.session_state.file_content = f"# {new_filename}\n"
                    st.rerun()

        # File list
        files_data = api_get("/files/list")
        if files_data:
            for f in files_data.get("files", []):
                if f["type"] == "file":
                    icon = _file_icon(f["name"])
                    is_active = st.session_state.current_file == f["path"]
                    label = f"{icon} {f['name']}"
                    if st.button(label, key=f"editor_file_{f['path']}", use_container_width=True,
                                 type="primary" if is_active else "secondary"):
                        st.session_state.current_file = f["path"]
                        file_data = api_get("/files/read", path=f["path"])
                        if file_data:
                            st.session_state.file_content = file_data.get("content", "")
                        st.rerun()

    with ecol2:
        if st.session_state.current_file:
            st.markdown(f"**{_file_icon(st.session_state.current_file)} {st.session_state.current_file}**")

            # Editor
            edited = st.text_area(
                "Code",
                value=st.session_state.file_content,
                height=450,
                label_visibility="collapsed",
                key="code_editor",
            )

            # Toolbar
            tcols = st.columns(5)
            with tcols[0]:
                if st.button("💾 Save"):
                    result = api_post("/files/write", {
                        "path": st.session_state.current_file,
                        "content": edited,
                    })
                    if result:
                        st.session_state.file_content = edited
                        st.success("Saved!")
            with tcols[1]:
                if st.button("▶ Run"):
                    lang = Path(st.session_state.current_file).suffix.lstrip(".")
                    result = api_post("/files/run", {"code": edited, "language": lang})
                    if result:
                        if result.get("success"):
                            st.success(f"Output:\n```\n{result.get('output', '')}\n```")
                        else:
                            st.error(f"Error:\n```\n{result.get('error', '')}\n```")
            with tcols[2]:
                if st.button("🔍 Lint"):
                    lang = Path(st.session_state.current_file).suffix.lstrip(".")
                    result = api_post("/files/lint", {"code": edited, "language": lang})
                    if result:
                        st.success("No syntax errors!") if result.get("valid") else st.error(result.get("errors", ""))
            with tcols[3]:
                if st.button("✨ Format"):
                    lang = Path(st.session_state.current_file).suffix.lstrip(".")
                    result = api_post("/files/format", {"code": edited, "language": lang})
                    if result:
                        st.session_state.file_content = result.get("formatted", edited)
                        st.rerun()
            with tcols[4]:
                if st.button("🤖 AI Fix"):
                    with st.spinner("Analyzing..."):
                        result = api_post("/chat/explain", {
                            "code": edited,
                            "model": st.session_state.model,
                        })
                        if result:
                            st.info(result.get("explanation", ""))
        else:
            st.markdown("""
            <div style="text-align:center; padding:60px; color:#64748b;">
                <div style="font-size:40px;">📝</div>
                <div style="margin-top:12px;">Select a file to edit or create a new one</div>
            </div>
            """, unsafe_allow_html=True)


# ── GENERATE TAB ──────────────────────────────────────────────────────────────
with tab_generate:
    st.markdown("## 🚀 Generate Project")
    st.markdown("Describe what you want to build and AI will generate the complete project.")

    gcol1, gcol2 = st.columns([2, 1])
    with gcol1:
        project_desc = st.text_area(
            "Project Description",
            placeholder="Build a FastAPI REST API with authentication, PostgreSQL database, and Docker setup...",
            height=150,
            key="gen_desc",
        )
    with gcol2:
        st.markdown("**Options**")
        gen_model = st.selectbox("Model", ["claude", "gemini", "glm"], key="gen_model")
        gen_workspace = st.text_input("Workspace", value="workspace/generated", key="gen_workspace")
        include_tests = st.toggle("Include Tests", value=True)
        include_docs = st.toggle("Include Docs", value=True)
        include_docker = st.toggle("Include Docker", value=False)

    if st.button("⚡ Generate Project", use_container_width=True, type="primary"):
        if project_desc.strip():
            extras = []
            if include_tests:
                extras.append("Include comprehensive tests")
            if include_docs:
                extras.append("Include detailed documentation")
            if include_docker:
                extras.append("Include Dockerfile and docker-compose.yml")

            full_desc = project_desc
            if extras:
                full_desc += "\n\nAlso: " + ". ".join(extras)

            with st.spinner(f"{model_icon(gen_model)} Generating project with {gen_model.upper()}..."):
                result = api_post("/chat/generate-project", {
                    "description": full_desc,
                    "model": gen_model,
                    "workspace_path": gen_workspace,
                })

            if result:
                st.success("Project generated! Check the Files tab.")
                st.session_state.workspace_path = gen_workspace
            else:
                # Fallback: do it via chat
                st.info("Generating via chat stream...")
                with st.spinner("Building your project..."):
                    result = api_post("/chat/message", {
                        "prompt": f"Generate a complete project: {full_desc}\n\nFor each file use format: <FILE path=\"...\">content</FILE>",
                        "model": gen_model,
                        "messages": [],
                        "workspace_path": gen_workspace,
                    })
                if result:
                    st.success("✅ Project generated!")
                    st.markdown("**AI Response:**")
                    st.markdown(result.get("response", ""))
        else:
            st.warning("Please describe your project first")

    # Templates
    st.divider()
    st.markdown("**Quick Templates**")
    tmpl_cols = st.columns(3)
    templates = [
        ("FastAPI REST API", "Create a FastAPI REST API with CRUD operations, JWT authentication, SQLAlchemy ORM, PostgreSQL database, and Pydantic models. Include proper error handling and API documentation."),
        ("React Dashboard", "Create a React TypeScript dashboard with authentication, data visualization charts, responsive layout, REST API integration, and Tailwind CSS styling."),
        ("Python Data Pipeline", "Create a Python data processing pipeline with pandas, async HTTP fetching, data validation, CSV/JSON export, logging, and comprehensive error handling."),
        ("Discord Bot", "Create a Discord bot with Python using discord.py, slash commands, role management, embed messages, error handling, and environment-based configuration."),
        ("ML Classifier", "Create a machine learning classification pipeline with scikit-learn, data preprocessing, model training/evaluation, cross-validation, and model persistence."),
        ("Telegram Bot", "Create a Telegram bot with aiogram, inline keyboards, state machine, database storage using SQLite, user management, and command handling."),
    ]
    for i, (title, desc) in enumerate(templates):
        with tmpl_cols[i % 3]:
            if st.button(f"📦 {title}", key=f"tmpl_{i}", use_container_width=True):
                st.session_state["gen_desc_value"] = desc
                st.rerun()


# ── TOOLS TAB ─────────────────────────────────────────────────────────────────
with tab_tools:
    tcol1, tcol2 = st.columns(2)

    with tcol1:
        # Code Runner
        st.markdown("### ▶ Code Runner")
        run_lang = st.selectbox("Language", ["python", "javascript", "typescript"], key="run_lang")
        run_code = st.text_area("Code", height=200, placeholder="print('Hello, World!')", key="run_code")
        if st.button("Run Code ▶", key="run_code_btn"):
            with st.spinner("Running..."):
                result = api_post("/files/run", {"code": run_code, "language": run_lang})
            if result:
                if result.get("success"):
                    st.success("Success!")
                    st.code(result.get("output", ""), language="text")
                else:
                    st.error("Error!")
                    st.code(result.get("error", ""), language="text")

        st.divider()

        # Web Search
        st.markdown("### 🔍 Web Search")
        search_q = st.text_input("Search query", placeholder="FastAPI authentication tutorial", key="search_q")
        if st.button("Search 🔍", key="search_btn"):
            from app.tools.search_tools import SearchTools
            st.session_state["_search_running"] = True
            search_tools = SearchTools()
            with st.spinner("Searching..."):
                import asyncio
                results = asyncio.run(search_tools.web_search(search_q))
            if results:
                for r in results:
                    st.markdown(f"""
                    <div class="ai-card" style="margin-bottom:8px;">
                        <div style="font-weight:600;">{r.get('title', '')}</div>
                        <div style="font-size:12px; color:#6366f1;">{r.get('url', '')}</div>
                        <div style="font-size:13px; color:#94a3b8; margin-top:4px;">{r.get('snippet', '')[:150]}</div>
                    </div>
                    """, unsafe_allow_html=True)

    with tcol2:
        # GitHub Tools
        st.markdown("### 🐙 GitHub Tools")
        gh_repo = st.text_input("Repository", placeholder="owner/repo-name", key="gh_tool_repo")
        if gh_repo and st.button("📊 Get Info"):
            parts = gh_repo.split("/")
            if len(parts) == 2:
                with st.spinner("Fetching..."):
                    info = api_get(f"/github/repo/{parts[0]}/{parts[1]}")
                if info:
                    st.markdown(f"""
                    <div class="ai-card">
                        <div style="font-weight:700; font-size:16px;">{info.get('full_name')}</div>
                        <div style="color:#94a3b8; font-size:13px;">{info.get('description', 'No description')}</div>
                        <div style="margin-top:8px; display:flex; gap:16px;">
                            <span>⭐ {info.get('stars', 0)}</span>
                            <span>🔀 {info.get('forks', 0)}</span>
                            <span>🔤 {info.get('language', 'N/A')}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        st.divider()

        # Test Runner
        st.markdown("### 🧪 Test Runner")
        test_ws = st.text_input("Workspace path", value=st.session_state.workspace_path, key="test_ws")
        test_cmd = st.text_input("Test command (optional)", placeholder="pytest -v", key="test_cmd")
        if st.button("🧪 Run Tests", key="run_tests_btn"):
            with st.spinner("Running tests..."):
                result = api_get("/files/test", workspace_path=test_ws, command=test_cmd or None)
            if result:
                if result.get("success"):
                    st.success("✅ Tests passed!")
                else:
                    st.error("❌ Tests failed")
                if result.get("output"):
                    st.code(result["output"], language="text")
                if result.get("error"):
                    st.code(result["error"], language="text")

        st.divider()

        # Metrics
        st.markdown("### 📊 Stats")
        files_data = api_get("/files/list")
        file_count = len([f for f in (files_data or {}).get("files", []) if f["type"] == "file"]) if files_data else 0
        msg_count = len(st.session_state.messages)

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{file_count}</div>
                <div class="metric-label">Files</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{msg_count}</div>
                <div class="metric-label">Messages</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.model[0].upper()}</div>
                <div class="metric-label">Model</div>
            </div>
            """, unsafe_allow_html=True)
