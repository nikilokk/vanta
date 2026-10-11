# interfaces/dashboard.py
"""
Vanta Dashboard — Dark Futuristic + Liquid Glass.
Запуск: streamlit run interfaces/dashboard.py
"""
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    libs_path = PROJECT_ROOT / "libs"
    if libs_path.exists():
        os.add_dll_directory(str(libs_path))

from core.logger import setup_logging
setup_logging()

import time
import re as _re
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Vanta",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

from core.brain import ask_ai, ask_ai_stream, clear_chat_history, chat_history
from core.memory import recall_memory, save_memory, forget_memory
from core.vector_memory import get_stats, search_conversations
from core.scheduler import _load_jobs, add_interval_task, remove_scheduled_task
from tools.system import get_system_info, get_gpu_info
from config import DATA_DIR

LOG_FILE = DATA_DIR / "vanta.log"


def _typewriter(text: str, speed: float = 0.012, chunk_size: int = 1):
    if not text:
        return
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]
        time.sleep(speed)


# ═══════════════════════════════════════════════════════════════
# СТИЛЬ
# ═══════════════════════════════════════════════════════════════
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.stApp {
    background: #0a0a0c;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.08), transparent),
        radial-gradient(ellipse 60% 40% at 100% 100%, rgba(168, 85, 247, 0.05), transparent),
        radial-gradient(ellipse 50% 40% at 0% 80%, rgba(6, 182, 212, 0.04), transparent);
    background-attachment: fixed;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1400px;
}

#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }

header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}

[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapsedControl"] > button,
button[data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"],
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    top: 1rem !important;
    left: 1rem !important;
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.5), rgba(168, 85, 247, 0.5)) !important;
    border: 1px solid rgba(99, 102, 241, 0.7) !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    box-shadow: 0 0 30px rgba(99, 102, 241, 0.5) !important;
    z-index: 999999 !important;
    cursor: pointer !important;
}
[data-testid="stSidebarCollapsedControl"]:hover,
button[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="collapsedControl"]:hover {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.8), rgba(168, 85, 247, 0.8)) !important;
    transform: scale(1.05) !important;
}

h1, h2, h3, h4, h5, h6 {
    color: #f4f4f6 !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    font-family: 'Inter', sans-serif !important;
}
h1 { font-size: 1.85rem !important; }
h2 { font-size: 1.4rem !important; }
h3 { font-size: 1.15rem !important; }
p, span, li, label, div { color: #b8b8c0; }

code, pre, .stCode {
    font-family: 'JetBrains Mono', 'Consolas', monospace !important;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.15); }

section[data-testid="stSidebar"] {
    background: #0d0d10 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}
section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}

.vanta-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 0.5rem 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    margin-bottom: 1.5rem;
}
.vanta-logo-mark {
    width: 32px;
    height: 32px;
    border-radius: 9px;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: white;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}
.vanta-logo-text {
    font-size: 1.05rem;
    font-weight: 600;
    color: #f4f4f6;
    letter-spacing: -0.02em;
}
.vanta-logo-sub {
    font-size: 0.7rem;
    color: #6b6b78;
    font-weight: 400;
}

section[data-testid="stSidebar"] .stRadio > label {
    display: none !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 4px !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child,
section[data-testid="stSidebar"] [role="radiogroup"] label > input,
section[data-testid="stSidebar"] [role="radiogroup"] label [data-baseweb="radio"] > div:first-child {
    display: none !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] label {
    display: flex !important;
    align-items: center !important;
    padding: 10px 14px !important;
    border-radius: 10px !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    cursor: pointer !important;
    transition: all 0.18s ease !important;
    width: 100% !important;
    margin: 0 !important;
    position: relative !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.04) !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] label > div:last-child,
section[data-testid="stSidebar"] [role="radiogroup"] label p {
    color: #8b8b95 !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    transition: color 0.18s ease !important;
    margin: 0 !important;
    letter-spacing: -0.01em !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] label:hover > div:last-child,
section[data-testid="stSidebar"] [role="radiogroup"] label:hover p {
    color: #d4d4dc !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: rgba(99, 102, 241, 0.12) !important;
    border-color: rgba(99, 102, 241, 0.28) !important;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.1) !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) > div:last-child,
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color: #e0e0ff !important;
    font-weight: 600 !important;
}

section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)::before {
    content: '' !important;
    position: absolute !important;
    left: 0 !important;
    top: 20% !important;
    bottom: 20% !important;
    width: 3px !important;
    background: linear-gradient(180deg, #6366f1, #a855f7) !important;
    border-radius: 2px !important;
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.6) !important;
}

.stButton > button {
    background: rgba(255, 255, 255, 0.04) !important;
    color: #d4d4dc !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-radius: 10px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em;
}
.stButton > button:hover {
    background: rgba(99, 102, 241, 0.12) !important;
    border-color: rgba(99, 102, 241, 0.35) !important;
    color: #e0e0ff !important;
    box-shadow: 0 0 24px rgba(99, 102, 241, 0.15);
}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stSelectbox div[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    color: #e4e4ea !important;
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: rgba(99, 102, 241, 0.4) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    background: rgba(255, 255, 255, 0.04) !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #55555f !important;
}

.stChatMessage {
    background: rgba(255, 255, 255, 0.025) !important;
    backdrop-filter: blur(20px) saturate(1.3);
    -webkit-backdrop-filter: blur(20px) saturate(1.3);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 14px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
.stChatMessage p {
    color: #d4d4dc;
    line-height: 1.65;
    font-size: 0.94rem;
}
.stChatMessage strong { color: #f4f4f6; }
/* Inline code (`code` внутри текста) */
.stChatMessage code {
    background: rgba(99, 102, 241, 0.12) !important;
    color: #c4b5fd !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 0.85em !important;
    font-family: 'JetBrains Mono', monospace !important;
    border: 1px solid rgba(99, 102, 241, 0.15);
}

/* Fenced code block (```python ... ```) */
.stChatMessage pre {
    background: #0a0a0f !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    border-radius: 12px !important;
    padding: 1rem 1.2rem !important;
    margin: 0.8rem 0 !important;
    overflow-x: auto !important;
    box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.05), 0 4px 16px rgba(0, 0, 0, 0.3);
    position: relative;
}

/* Тонкая полоска-акцент сверху блока */
.stChatMessage pre::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.4), transparent);
}

.stChatMessage pre code {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    font-size: 0.82rem !important;
    line-height: 1.65 !important;
    color: #e4e4ea !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ═════════ PYGMALEX SYNTAX HIGHLIGHT ═════════ */
/* Streamlit использует Pygments — перекрашиваем классы */

.stChatMessage pre code .k,   /* keyword: def, if, for, class */
.stChatMessage pre code .kn,  /* keyword.namespace: import */
.stChatMessage pre code .kr,  /* keyword.reserved: return, yield */
.stChatMessage pre code .kd { /* keyword.declaration: def, class */
    color: #c084fc !important;
    font-weight: 500 !important;
}

.stChatMessage pre code .s,   /* string */
.stChatMessage pre code .s1,  /* string.single */
.stChatMessage pre code .s2,  /* string.double */
.stChatMessage pre code .sb,
.stChatMessage pre code .sc,
.stChatMessage pre code .sd,
.stChatMessage pre code .se,
.stChatMessage pre code .sh,
.stChatMessage pre code .si,
.stChatMessage pre code .sx,
.stChatMessage pre code .sr,
.stChatMessage pre code .ss {
    color: #86efac !important;   /* зелёный для строк */
}

.stChatMessage pre code .c,   /* comment */
.stChatMessage pre code .c1,  /* comment.single */
.stChatMessage pre code .cm,  /* comment.multiline */
.stChatMessage pre code .cs {
    color: #6b7280 !important;
    font-style: italic !important;
}

.stChatMessage pre code .nf,  /* name.function */
.stChatMessage pre code .fm { /* name.function.magic */
    color: #60a5fa !important;
}

.stChatMessage pre code .nc { /* name.class */
    color: #fbbf24 !important;
    font-weight: 500 !important;
}

.stChatMessage pre code .nb,  /* name.builtin: print, len */
.stChatMessage pre code .bp { /* name.builtin.pseudo: self */
    color: #67e8f9 !important;
}

.stChatMessage pre code .nn { /* name.namespace */
    color: #f4f4f6 !important;
}

.stChatMessage pre code .mi,  /* number.integer */
.stChatMessage pre code .mf,  /* number.float */
.stChatMessage pre code .m,   /* number */
.stChatMessage pre code .mh,
.stChatMessage pre code .mo {
    color: #fda4af !important;   /* розовый для чисел */
}

.stChatMessage pre code .o,   /* operator: +, =, > */
.stChatMessage pre code .ow { /* operator.word: and, or, not */
    color: #f472b6 !important;
}

.stChatMessage pre code .p {  /* punctuation: (, ), :, , */
    color: #9ca3af !important;
}

.stChatMessage pre code .n {  /* name (переменные) */
    color: #e4e4ea !important;
}

.stChatMessage pre code .na { /* name.attribute */
    color: #a5b4fc !important;
}

/* Небольшой скролл для блоков с длинными строками */
.stChatMessage pre::-webkit-scrollbar {
    height: 8px;
}
.stChatMessage pre::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}
.stChatMessage pre::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
}

[data-testid="stChatInput"] {
    background: transparent !important;
}
[data-testid="stChatInput"] > div {
    background: rgba(20, 20, 26, 0.85) !important;
    backdrop-filter: blur(24px) saturate(1.5);
    -webkit-backdrop-filter: blur(24px) saturate(1.5);
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: rgba(99, 102, 241, 0.35) !important;
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.4), 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
}
[data-testid="stChatInput"] textarea {
    color: #e4e4ea !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: #55555f !important;
}

details[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem !important;
    overflow: hidden;
}
details[data-testid="stExpander"] summary {
    color: #9a9aa5 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 8px 14px !important;
    transition: all 0.15s ease;
}
details[data-testid="stExpander"] summary:hover {
    color: #d4d4dc !important;
    background: rgba(255, 255, 255, 0.02);
}
details[data-testid="stExpander"] pre {
    background: #0d0d12 !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
}

.card {
    background: rgba(255, 255, 255, 0.025);
    backdrop-filter: blur(16px) saturate(1.2);
    -webkit-backdrop-filter: blur(16px) saturate(1.2);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.8rem;
    transition: all 0.2s ease;
}
.card:hover {
    border-color: rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.035);
}

.metric-card {
    background: rgba(255, 255, 255, 0.025);
    backdrop-filter: blur(16px) saturate(1.2);
    -webkit-backdrop-filter: blur(16px) saturate(1.2);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 1.2rem 1.3rem;
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.4), transparent);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.metric-card:hover::before { opacity: 1; }
.metric-card:hover {
    border-color: rgba(99, 102, 241, 0.2);
    transform: translateY(-1px);
}
.metric-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #6b6b78;
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.metric-value {
    font-size: 1.75rem;
    font-weight: 600;
    color: #f4f4f6;
    letter-spacing: -0.03em;
    line-height: 1;
    font-family: 'Inter', sans-serif;
}
.metric-sub {
    font-size: 0.75rem;
    color: #8b8b95;
    margin-top: 0.4rem;
}

.progress-track {
    height: 6px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
    overflow: hidden;
    margin: 10px 0 6px;
}
.progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #6366f1 0%, #a855f7 100%);
    border-radius: 3px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.5);
}
.progress-bar.cyan {
    background: linear-gradient(90deg, #06b6d4 0%, #6366f1 100%);
    box-shadow: 0 0 12px rgba(6, 182, 212, 0.5);
}

.thoughts-box {
    color: #8b8b95;
    font-size: 0.82rem;
    font-style: italic;
    line-height: 1.65;
    padding: 12px 16px;
    border-radius: 10px;
    background: rgba(99, 102, 241, 0.04);
    border: 1px solid rgba(99, 102, 241, 0.12);
    border-left: 2px solid rgba(99, 102, 241, 0.4);
    font-family: 'Inter', sans-serif;
    max-height: 280px;
    overflow-y: auto;
}

.tool-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 8px;
    background: rgba(168, 85, 247, 0.08);
    border: 1px solid rgba(168, 85, 247, 0.2);
    color: #c4b5fd;
    font-size: 0.75rem;
    font-weight: 500;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 4px;
}
.tool-chip::before {
    content: '⚡';
    font-size: 0.7rem;
    opacity: 0.8;
}

.usage-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #55555f;
    margin-top: 8px;
    padding-left: 2px;
    letter-spacing: 0.01em;
}

.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: #55555f;
}
.empty-icon {
    font-size: 2.5rem;
    opacity: 0.4;
    display: block;
    margin-bottom: 1rem;
    color: #6b6b78;
}
.empty-title {
    font-size: 1.05rem;
    font-weight: 500;
    color: #8b8b95;
    margin-bottom: 0.4rem;
    letter-spacing: -0.01em;
}
.empty-sub {
    font-size: 0.85rem;
    opacity: 0.7;
    color: #6b6b78;
}

.page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 1.2rem;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.page-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: #f4f4f6;
    letter-spacing: -0.025em;
    display: flex;
    align-items: center;
    gap: 12px;
}
.page-status {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 20px;
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    color: #6ee7b7;
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.02em;
}
.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 8px #10b981;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

.sidebar-footer {
    margin-top: 2rem;
    padding: 0.8rem 1rem;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    font-size: 0.72rem;
    color: #6b6b78;
    text-align: center;
}

[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 1.2rem 1.3rem;
}

.stAlert {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid rgba(255, 255, 255, 0.07) !important;
    border-radius: 10px !important;
    color: #d4d4dc !important;
}
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# ХЕЛПЕРЫ
# ═══════════════════════════════════════════════════════════════
def page_header(title: str, emoji: str = "", status: str = None):
    status_html = ""
    if status:
        status_html = f"""
        <div class="page-status">
            <span class="status-dot"></span>
            {status}
        </div>
        """
    st.markdown(
        f"""
        <div class="page-header">
            <div class="page-title">{emoji} {title}</div>
            {status_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, sub: str = "", progress: float = None, accent: str = "violet"):
    progress_html = ""
    if progress is not None:
        cls = "progress-bar cyan" if accent == "cyan" else "progress-bar"
        progress_html = f"""
        <div class="progress-track">
            <div class="{cls}" style="width: {progress}%;"></div>
        </div>
        """
    sub_html = f'<div class="metric-sub">{sub}</div>' if sub else ""

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {sub_html}
            {progress_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="empty-state">
            <span class="empty-icon">{icon}</span>
            <div class="empty-title">{title}</div>
            <div class="empty-sub">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def usage_tag(usage: dict):
    """Маленькая подпись с расходом токенов."""
    if not usage or not usage.get("total"):
        return
    st.markdown(
        f'<div class="usage-tag">'
        f'{usage["total"]:,} tok · cached {usage.get("cached", 0):,} · ${usage.get("cost", 0):.5f}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════
# САЙДБАР
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        """
        <div class="vanta-logo">
            <div class="vanta-logo-mark">◈</div>
            <div>
                <div class="vanta-logo-text">Vanta</div>
                <div class="vanta-logo-sub">AI Assistant</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Навигация",
        ["💬  Чат", "🧠  Память", "⏰  Задачи", "📊  Токены", "💻  Статус", "📋  Логи"],
        label_visibility="collapsed",
    )

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    if st.button("🗑  Очистить чат", use_container_width=True):
        clear_chat_history()
        st.rerun()

    st.markdown(
        f"""
        <div class="sidebar-footer">
            {datetime.now().strftime('%d.%m.%Y · %H:%M')}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════
# ЧАТ
# ═══════════════════════════════════════════════════════════════
if page.endswith("Чат"):
    page_header("Чат с Vanta", "◈", "Online")

    for msg in chat_history[1:]:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)

        if role == "user" and content:
            with st.chat_message("user"):
                st.markdown(content)

        elif role == "assistant" and content:
            with st.chat_message("assistant"):
                display = content
                thoughts = ""

                if isinstance(msg, dict):
                    thoughts = msg.get("thoughts", "")

                if not thoughts and isinstance(content, str) and "<think>" in content:
                    m = _re.search(r"<think>(.*?)</think>", content, flags=_re.DOTALL)
                    if m:
                        thoughts = m.group(1).strip()
                        display = _re.sub(r"<think>.*?</think>", "", content, flags=_re.DOTALL).strip()

                if thoughts:
                    with st.expander("💭  Мысли Vanta", expanded=False):
                        st.markdown(
                            f'<div class="thoughts-box">{thoughts.replace(chr(10), "<br>")}</div>',
                            unsafe_allow_html=True,
                        )
                st.markdown(display)

                # Подпись с расходом
                if isinstance(msg, dict) and msg.get("usage"):
                    usage_tag(msg["usage"])

    user_input = st.chat_input("Напиши сообщение...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            thought_box = st.empty()
            tool_box = st.container()
            answer_box = st.empty()

            thought_buf = ""
            answer_buf = ""
            final_display = ""
            final_thoughts = ""
            final_usage = None

            try:
                for event in ask_ai_stream(user_input):
                    etype = event.get("type")

                    if etype == "thought":
                        thought_buf += event["text"]
                        safe = (
                            thought_buf
                            .replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;")
                            .replace("\n", "<br>")
                        )
                        thought_box.markdown(
                            f'<div class="thoughts-box">💭 {safe}</div>',
                            unsafe_allow_html=True,
                        )

                    elif etype == "answer":
                        answer_buf += event["text"]
                        answer_box.markdown(answer_buf)

                    elif etype == "tool_call":
                        with tool_box:
                            st.markdown(
                                f'<div class="tool-chip">{event["name"]}</div>',
                                unsafe_allow_html=True,
                            )

                    elif etype == "tool_result":
                        with tool_box:
                            with st.expander(f"↳ {event['name']}", expanded=False):
                                st.json(event["result"])

                    elif etype == "done":
                        final_display = event.get("display", answer_buf)
                        final_thoughts = event.get("thoughts", thought_buf)
                        final_usage = event.get("usage")

            except Exception as e:
                st.error(f"Ошибка стриминга: {e}")
                final_display = answer_buf or "Произошла ошибка."
                final_thoughts = thought_buf

            thought_box.empty()
            tool_box.empty()
            answer_box.empty()

            if final_thoughts:
                with st.expander("💭  Мысли Vanta", expanded=False):
                    st.markdown(
                        f'<div class="thoughts-box">{final_thoughts.replace(chr(10), "<br>")}</div>',
                        unsafe_allow_html=True,
                    )

            if not final_display.strip():
                final_display = "✔ Готово."

            if len(final_display) > 500:
                speed, chunk = 0.005, 3
            elif len(final_display) > 200:
                speed, chunk = 0.008, 2
            else:
                speed, chunk = 0.012, 1

            st.write_stream(_typewriter(final_display, speed=speed, chunk_size=chunk))

            if final_usage:
                usage_tag(final_usage)

        st.rerun()


# ═══════════════════════════════════════════════════════════════
# ПАМЯТЬ
# ═══════════════════════════════════════════════════════════════
elif page.endswith("Память"):
    page_header("Память", "🧠")

    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.markdown("#### 📌 Факты")
        result = recall_memory()
        memories = result.get("all_memories", {}) if result.get("success") else {}

        if memories:
            for key, value in memories.items():
                st.markdown(
                    f"""
                    <div class="card" style="padding: 0.9rem 1.1rem;">
                        <div style="font-size:0.7rem; color:#6b6b78; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:6px;">
                            {key}
                        </div>
                        <div style="color:#d4d4dc; font-size:0.92rem; line-height:1.5;">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            empty_state("◇", "Пока пусто", "Ванта запомнит, что ты ей расскажешь")

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        with st.form("add_fact", clear_on_submit=True):
            st.markdown("**Добавить факт**")
            new_key = st.text_input("Ключ", placeholder="например, user_name")
            new_value = st.text_area("Значение", placeholder="что запомнить", height=80)
            if st.form_submit_button("Сохранить", use_container_width=True):
                if new_key and new_value:
                    save_memory(new_key, new_value)
                    st.rerun()

    with col2:
        st.markdown("#### 💬 Векторная память")
        stats = get_stats()
        count = stats.get("total_conversations", 0) if stats.get("success") else 0

        metric_card(
            "Диалогов сохранено",
            str(count),
            "в ChromaDB · эмбеддинги OpenAI",
        )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        query = st.text_input("🔍 Поиск по смыслу", placeholder="о чём говорили...")
        if query:
            with st.spinner("Ищу..."):
                sr = search_conversations(query, n_results=5)
                if sr.get("success") and sr.get("results"):
                    for r in sr["results"]:
                        st.markdown(
                            f"""
                            <div class="card" style="padding: 0.9rem 1.1rem;">
                                <div style="font-size:0.7rem; color:#6b6b78; margin-bottom:6px; font-family:'JetBrains Mono', monospace;">
                                    {r['timestamp'][:16]} · d={r['distance']}
                                </div>
                                <div style="font-size:0.88rem; line-height:1.55; color:#b8b8c0;">
                                    {r['text'][:400]}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("Ничего не найдено.")


# ═══════════════════════════════════════════════════════════════
# ЗАДАЧИ
# ═══════════════════════════════════════════════════════════════
elif page.endswith("Задачи"):
    page_header("Фоновые задачи", "⏰", "Планировщик активен")

    jobs = _load_jobs()

    if not jobs:
        empty_state(
            "◇",
            "Нет активных задач",
            "Создай через чат: «напоминай мне каждые 30 минут...»",
        )
    else:
        for job in jobs:
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(
                    f"""
                    <div class="card">
                        <div style="display:flex; justify-content:space-between; align-items:start;">
                            <div>
                                <div style="font-size:0.98rem; font-weight:600; color:#e4e4ea; letter-spacing:-0.01em;">
                                    {job.get('name', 'task')}
                                </div>
                                <div style="font-size:0.78rem; color:#8b8b95; margin-top:6px; font-family:'JetBrains Mono', monospace;">
                                    every {job.get('minutes')} min · {job.get('task_type', 'ai_task')}
                                </div>
                            </div>
                            <div style="font-size:0.68rem; color:#55555f; font-family:'JetBrains Mono', monospace;">
                                {job.get('id')}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)
                if st.button("🗑", key=f"deljob_{job['id']}", use_container_width=True):
                    remove_scheduled_task(job["id"])
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
# ТОКЕНЫ
# ═══════════════════════════════════════════════════════════════
elif page.endswith("Токены"):
    page_header("Расход токенов", "📊", "OpenAI API")

    from core.usage_tracker import get_stats, reset_usage
    stats = get_stats()
    today = stats["today"]
    total = stats["total"]
    cache_hit = stats["cache_hit_rate"]

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        metric_card("Сегодня", f"${today['cost_usd']:.4f}", f"{today['requests']} запросов")
    with c2:
        metric_card(
            "Всего",
            f"${total['cost_usd']:.3f}",
            f"{total['requests']} запросов",
            accent="cyan",
        )
    with c3:
        tokens_today = today["prompt_tokens"] + today["completion_tokens"]
        metric_card(
            "Токены сегодня",
            f"{tokens_today:,}",
            f"{today['prompt_tokens']:,} in / {today['completion_tokens']:,} out",
        )
    with c4:
        metric_card("Cache hit", f"{cache_hit}%", f"{total['cached_tokens']:,} кэшировано")

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

    # График за 7 дней
    st.markdown("#### 📈 Расход за последние 7 дней")
    days = stats["last_7_days"]
    max_cost = max([d["cost"] for d in days] + [0.0001])

    bars_html = ""
    for d in days:
        h = (d["cost"] / max_cost) * 100 if max_cost > 0 else 0
        bars_html += f"""
        <div style="flex:1; display:flex; flex-direction:column; align-items:center; gap:8px;">
            <div style="width:100%; height:120px; display:flex; align-items:flex-end;">
                <div style="width:100%; height:{h}%; min-height:2px;
                    background:linear-gradient(180deg, #a855f7, #6366f1);
                    border-radius:6px 6px 0 0;
                    box-shadow:0 0 12px rgba(99,102,241,0.4);
                    transition:all 0.3s ease;"></div>
            </div>
            <div style="font-size:0.7rem; color:#8b8b95; font-family:JetBrains Mono,monospace;">{d['label']}</div>
            <div style="font-size:0.68rem; color:#55555f; font-family:JetBrains Mono,monospace;">${d['cost']:.3f}</div>
        </div>
        """

    st.markdown(
        f"""
        <div class="card" style="padding:1.2rem;">
            <div style="display:flex; gap:12px; align-items:end;">{bars_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Последние запросы
    st.markdown("#### 🕒 Последние запросы")
    recent = stats["recent"]

    if not recent:
        empty_state("◇", "Пока пусто", "Здесь появятся запросы к OpenAI")
    else:
        for r in recent:
            ts = r["ts"][11:19]
            model = r["model"]
            cached_str = f" · cached {r['cached']:,}" if r['cached'] else ""
            st.markdown(
                f"""
                <div class="card" style="padding:0.7rem 1rem; margin-bottom:0.5rem;">
                    <div style="display:flex; justify-content:space-between; align-items:center; gap:16px;">
                        <div style="font-family:JetBrains Mono,monospace; font-size:0.78rem; color:#8b8b95; min-width:60px;">
                            {ts}
                        </div>
                        <div style="font-family:JetBrains Mono,monospace; font-size:0.72rem; color:#6b6b78; flex:1;">
                            {model}
                        </div>
                        <div style="font-family:JetBrains Mono,monospace; font-size:0.75rem; color:#b8b8c0; text-align:right;">
                            <span style="color:#c4b5fd;">{r['prompt']:,}</span>
                            <span style="color:#55555f;"> + </span>
                            <span style="color:#6ee7b7;">{r['completion']:,}</span>
                            <span style="color:#6b6b78;">{cached_str}</span>
                        </div>
                        <div style="font-family:JetBrains Mono,monospace; font-size:0.75rem; color:#a5b4fc; min-width:70px; text-align:right;">
                            ${r['cost']:.5f}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    with st.expander("⚙️  Управление", expanded=False):
        st.caption("Сброс статистики (не влияет на OpenAI, только локальный лог).")
        if st.button("🗑  Сбросить статистику"):
            reset_usage()
            st.rerun()


# ═══════════════════════════════════════════════════════════════
# СТАТУС
# ═══════════════════════════════════════════════════════════════
elif page.endswith("Статус"):
    page_header("Состояние системы", "💻", "Live")

    try:
        info = get_system_info()

        c1, c2, c3 = st.columns(3, gap="medium")
        with c1:
            cpu = info.get("cpu_usage_percent", 0)
            metric_card("CPU", f"{cpu}%", info.get("cpu", "")[:40], progress=cpu)
        with c2:
            ram = info.get("ram", {})
            ram_pct = ram.get("usage_percent", 0)
            metric_card(
                "RAM",
                f"{ram_pct}%",
                f"{ram.get('used_gb')} / {ram.get('total_gb')} GB",
                progress=ram_pct,
                accent="cyan",
            )
        with c3:
            metric_card("OS", info.get("os", "?"), info.get("architecture", ""))

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("#### 💾 Диски")

        for disk in info.get("disks", []):
            pct = disk["usage_percent"]
            st.markdown(
                f"""
                <div class="card" style="padding: 1rem 1.2rem;">
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#b8b8c0; margin-bottom:4px;">
                        <span style="font-weight:500;">{disk['drive']}</span>
                        <span style="font-family:'JetBrains Mono', monospace; font-size:0.78rem;">
                            {disk['used_gb']} / {disk['total_gb']} GB · {pct}%
                        </span>
                    </div>
                    <div class="progress-track">
                        <div class="progress-bar" style="width:{pct}%;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.markdown("#### 🎮 GPU")

        try:
            gi = get_gpu_info()
            if gi.get("success"):
                for gpu in gi.get("gpus", []):
                    st.markdown(
                        f"""
                        <div class="card">
                            <div style="font-weight:600; color:#e4e4ea; font-size:0.98rem; margin-bottom:10px;">
                                {gpu['name']}
                            </div>
                            <div style="display:flex; gap:32px; font-size:0.82rem; color:#8b8b95; font-family:'JetBrains Mono', monospace;">
                                <span>🌡 {gpu['temperature_c']}°C</span>
                                <span>⚡ {gpu['gpu_usage_percent']}%</span>
                                <span>💾 {gpu['vram_used_gb']} / {gpu['vram_total_gb']} GB</span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("GPU не обнаружен.")
        except Exception as e:
            st.warning(f"GPU: {e}")

    except Exception as e:
        st.error(f"Ошибка: {e}")


# ═══════════════════════════════════════════════════════════════
# ЛОГИ
# ═══════════════════════════════════════════════════════════════
elif page.endswith("Логи"):
    page_header("Логи", "📋")

    if not LOG_FILE.exists():
        empty_state("◇", "Лог-файл пуст", "Здесь появятся записи после первых запусков")
    else:
        c1, c2 = st.columns([1, 4])
        with c1:
            lines_count = st.number_input("Строк", min_value=50, max_value=2000, value=200)
            level_filter = st.selectbox("Уровень", ["Все", "ERROR", "WARNING", "INFO"])

        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            tail = all_lines[-lines_count:]
            if level_filter != "Все":
                tail = [l for l in tail if f"[{level_filter}]" in l]

            with c2:
                if tail:
                    st.code("".join(tail), language="log")
                else:
                    st.info("Нет подходящих записей.")

            st.caption(f"Всего строк в файле: {len(all_lines)}")
        except Exception as e:
            st.error(f"Ошибка чтения: {e}")