# interfaces/dashboard.py
"""
Vanta Dashboard — Premium Cyberpunk / Grok Blobs Edition.
Анимированные органические кляксы, темная неоновая эстетика, конструктор агентов.
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
import json
import re as _re
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Vanta AI",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── i18n & Settings ───
from core.settings import get_setting, set_setting
from core.i18n import set_lang, get_lang, t, available_languages

if "lang" not in st.session_state:
    st.session_state.lang = get_setting("lang", "ru")
set_lang(st.session_state.lang)

# ─── Vanta Core, Agents & Blobs ───
from core.prompts import SYSTEM_PROMPT
from core.agents import list_agents, get_agent, save_agent, delete_agent, AgentConfig
from core.blobs import generate_blob_svg, get_agent_avatar_path, BLOB_PATHS, BLOB_PALETTES
from core.brain import ask_ai_stream, clear_chat_history, chat_history, TOOL_REGISTRY
from core.memory import recall_memory, save_memory, forget_memory
from core.vector_memory import get_stats, search_conversations
from core.scheduler import _load_jobs, remove_scheduled_task, init_scheduler
from tools.system import get_system_info, get_gpu_info
from config import DATA_DIR, MAIN_MODEL

LOG_FILE = DATA_DIR / "vanta.log"


@st.cache_resource
def ensure_background_services():
    init_scheduler()
    return True

ensure_background_services()


# ═══════════════════════════════════════════════════════════════
# ПРЕМИУМ СТИЛИ (Glassmorphism + Живые Кляксы + Неоновое свечение)
# ═══════════════════════════════════════════════════════════════
STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

.stApp {
    background-color: #070709 !important;
    background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 0%, rgba(168, 85, 247, 0.08) 0px, transparent 50%),
        radial-gradient(at 50% 100%, rgba(14, 165, 233, 0.06) 0px, transparent 50%);
    background-attachment: fixed;
    color: #f1f1f4;
}

#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    display: none !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1440px !important;
}

/* Боковая панель */
section[data-testid="stSidebar"] {
    background: #0b0b0e !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
}
section[data-testid="stSidebar"] > div {
    padding: 1.5rem 1.2rem;
}

/* Логотип */
.vanta-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 1.2rem;
    margin-bottom: 1.2rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: 700;
    color: #fff;
    box-shadow: 0 0 24px rgba(99, 102, 241, 0.45);
}
.brand-name {
    font-size: 1.2rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: #fff;
    line-height: 1.2;
}
.brand-tag {
    font-size: 0.68rem;
    color: #71717a;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Анимация органической живой кляксы (Grok Blob) */
@keyframes blob-morph {
    0%, 100% {
        transform: rotate(0deg) scale(1);
    }
    33% {
        transform: rotate(5deg) scale(1.04);
    }
    66% {
        transform: rotate(-4deg) scale(0.97);
    }
}

.live-blob {
    animation: blob-morph 9s ease-in-out infinite;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    display: inline-flex;
    align-items: center;
    justify-content: center;
}
.live-blob:hover {
    transform: scale(1.15) rotate(8deg);
    filter: brightness(1.2) drop-shadow(0 0 20px rgba(99, 102, 241, 0.5));
}

/* Карточки */
.v-card {
    background: rgba(18, 18, 23, 0.7);
    backdrop-filter: blur(24px) saturate(1.4);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 1rem;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}
.v-card:hover {
    border-color: rgba(99, 102, 241, 0.3);
    background: rgba(22, 22, 28, 0.85);
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
}

/* Метрики */
.v-metric {
    background: rgba(18, 18, 23, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    position: relative;
    overflow: hidden;
}
.v-metric::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.6), transparent);
    opacity: 0.5;
}
.v-metric-title {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #71717a;
    margin-bottom: 6px;
}
.v-metric-val {
    font-size: 1.8rem;
    font-weight: 700;
    letter-spacing: -0.04em;
    color: #fafafa;
}
.v-metric-sub {
    font-size: 0.76rem;
    color: #a1a1aa;
    margin-top: 4px;
}

/* Статус-бар в чате */
.chat-status-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 1.4rem;
    background: rgba(18, 18, 23, 0.55);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    margin-bottom: 1.2rem;
}
.pulse-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 10px #10b981;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.3; }
    100% { opacity: 1; }
}

/* Tool Chips */
.tool-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 8px;
    background: rgba(245, 158, 11, 0.08);
    border: 1px solid rgba(245, 158, 11, 0.25);
    color: #fbbf24;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    font-weight: 500;
    margin: 4px 4px 4px 0;
}

/* Мысли модели */
.thoughts-container {
    background: rgba(99, 102, 241, 0.04);
    border-left: 2px solid rgba(99, 102, 241, 0.4);
    border-radius: 0 10px 10px 0;
    padding: 10px 14px;
    font-size: 0.82rem;
    color: #9ca3af;
    font-style: italic;
    margin-bottom: 0.8rem;
    line-height: 1.6;
}

/* Поля ввода */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
    background: rgba(18, 18, 23, 0.8) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    color: #f4f4f6 !important;
    font-size: 0.88rem !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: rgba(99, 102, 241, 0.5) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}

/* Кнопки */
.stButton > button {
    background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)) !important;
    border: 1px solid rgba(255, 255, 255, 0.09) !important;
    color: #e4e4e7 !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    padding: 0.55rem 1.1rem !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    border-color: rgba(99, 102, 241, 0.45) !important;
    background: rgba(99, 102, 241, 0.12) !important;
    color: #ffffff !important;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.2) !important;
    transform: translateY(-1px);
}

/* Навигация */
section[data-testid="stSidebar"] .stRadio > label { display: none !important; }
section[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 9px 12px !important;
    border-radius: 10px !important;
    margin-bottom: 2px !important;
    border: 1px solid transparent !important;
    transition: all 0.15s ease !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.03) !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: rgba(99, 102, 241, 0.12) !important;
    border-color: rgba(99, 102, 241, 0.25) !important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {
    color: #e0e7ff !important;
    font-weight: 600 !important;
}

/* === ЖЕСТКАЯ ФИКСАЦИЯ САЙДБАРА (НЕЛЬЗЯ ЗАКРЫТЬ ИЛИ СВЕРНУТЬ) === */

/* 1. Полностью убираем кнопки закрытия ("<") и открытия (">") сайдбара */
[data-testid="stSidebarCollapseButton"],
button[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarHeader"] {
    display: none !important;
    visibility: hidden !important;
    pointer-events: none !important;
}

/* 2. Принудительно держим сайдбар открытым даже при состоянии aria-expanded="false" */
section[data-testid="stSidebar"] {
    background: #0b0b0e !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    width: 280px !important;
    min-width: 280px !important;
    max-width: 280px !important;
    transform: none !important;
    margin-left: 0 !important;
    display: block !important;
    visibility: visible !important;
}

/* 3. Отключаем ползунок изменения ширины сайдбара мышкой */
div[data-testid="stSidebarUserContent"] {
    padding-top: 1.5rem !important;
}
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", status: str = "Online"):
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:flex-end; padding-bottom:1.2rem; margin-bottom:1.5rem; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div>
            <h1 style="font-size:1.6rem; font-weight:700; margin:0; letter-spacing:-0.03em;">{title}</h1>
            <div style="font-size:0.8rem; color:#71717a; margin-top:4px;">{subtitle}</div>
        </div>
        <div style="display:flex; align-items:center; gap:8px; font-size:0.75rem; color:#10b981; font-weight:600; background:rgba(16,185,129,0.08); padding:5px 12px; border-radius:20px; border:1px solid rgba(16,185,129,0.2);">
            <span class="pulse-dot"></span>{status}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# САЙДБАР (Брендинг, Язык, Активный Агент с Кляксой, Меню)
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="vanta-brand">
        <div class="brand-icon">◈</div>
        <div>
            <div class="brand-name">Vanta AI</div>
            <div class="brand-tag">Modular Assistant</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Селектор языка
    langs = available_languages()
    lang_keys = list(langs.keys())
    current_lang_idx = lang_keys.index(st.session_state.lang) if st.session_state.lang in lang_keys else 0

    chosen_lang = st.selectbox(
        t("sidebar.language"),
        options=lang_keys,
        format_func=lambda x: langs[x],
        index=current_lang_idx,
        key="lang_selector",
    )
    if chosen_lang != st.session_state.lang:
        st.session_state.lang = chosen_lang
        set_setting("lang", chosen_lang)
        set_lang(chosen_lang)
        st.rerun()

    # Селектор активного агента
    all_agents = list_agents()
    agent_map = {a.id: a for a in all_agents}
    if "current_agent_id" not in st.session_state or st.session_state.current_agent_id not in agent_map:
        st.session_state.current_agent_id = "default"

    active_agent = agent_map[st.session_state.current_agent_id]
    agent_ids = list(agent_map.keys())

    selected_agent_id = st.selectbox(
        t("sidebar.agent"),
        options=agent_ids,
        format_func=lambda x: f"{agent_map[x].name}",
        index=agent_ids.index(st.session_state.current_agent_id),
    )
    st.session_state.current_agent_id = selected_agent_id

    # Мини-рендер кляксы в сайдбаре
    cur_blob_svg = generate_blob_svg(active_agent.blob_preset, active_agent.blob_palette, size=42)
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; padding:8px 12px; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:10px; margin-top:4px;">
        <div class="live-blob" style="width:42px; height:42px;">{cur_blob_svg}</div>
        <div>
            <div style="font-size:0.84rem; font-weight:600; color:#fff;">{active_agent.name}</div>
            <div style="font-size:0.68rem; color:#71717a; font-family:'JetBrains Mono',monospace;">{active_agent.blob_preset}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            t("nav.chat"),
            t("nav.agents"),
            t("nav.memory"),
            t("nav.tasks"),
            t("nav.tokens"),
            t("nav.status"),
            t("nav.logs"),
        ],
        label_visibility="collapsed",
    )

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    if st.button(f"🧹 {t('sidebar.clear_chat')}", use_container_width=True):
        clear_chat_history()
        st.rerun()


# ═══════════════════════════════════════════════════════════════
# 1. ЧАТ (Streamlit Chat Message + Live Blob Header)
# ═══════════════════════════════════════════════════════════════
if page == t("nav.chat"):
    agent = get_agent(st.session_state.current_agent_id)
    tools_count_desc = "All Tools (*)" if "*" in agent.allowed_tools else f"{len(agent.allowed_tools)} tools active"
    agent_avatar_path = get_agent_avatar_path(agent.id, agent.blob_preset, agent.blob_palette)
    header_blob_svg = generate_blob_svg(agent.blob_preset, agent.blob_palette, size=46)

    # Верхняя плашка активного агента
    st.markdown(f"""
    <div class="chat-status-bar">
        <div style="display:flex; align-items:center; gap:14px;">
            <div class="live-blob" style="width:46px; height:46px;">
                {header_blob_svg}
            </div>
            <div>
                <div style="font-weight:700; color:#fff; font-size:1.05rem;">{agent.name}</div>
                <div style="font-size:0.72rem; color:#71717a; font-family:'JetBrains Mono',monospace;">
                    {agent.id} · {agent.blob_preset} · {MAIN_MODEL}
                </div>
            </div>
        </div>
        <div style="font-size:0.75rem; color:#a1a1aa; font-family:'JetBrains Mono',monospace;">
            {tools_count_desc} · temp {agent.temperature}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Отрисовка истории сообщений
    for msg in chat_history[1:]:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)

        if role == "user" and content:
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)

        elif role == "assistant" and content:
            # Аватар — кэшированный SVG-файл живой кляксы агента
            with st.chat_message("assistant", avatar=agent_avatar_path):
                thoughts = msg.get("thoughts", "") if isinstance(msg, dict) else ""
                if not thoughts and "<think>" in str(content):
                    m = _re.search(r"<think>(.*?)</think>", content, flags=_re.DOTALL)
                    if m:
                        thoughts = m.group(1).strip()
                        content = _re.sub(r"<think>.*?</think>", "", content, flags=_re.DOTALL).strip()

                if thoughts:
                    with st.expander("💭 Ход рассуждений", expanded=False):
                        st.markdown(f'<div class="thoughts-container">{thoughts}</div>', unsafe_allow_html=True)

                st.markdown(content)

                if isinstance(msg, dict) and msg.get("usage"):
                    u = msg["usage"]
                    st.markdown(f"""
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#52525b; margin-top:6px;">
                        {u.get('total', 0):,} tok · cached {u.get('cached', 0):,} · ${u.get('cost', 0):.5f}
                    </div>
                    """, unsafe_allow_html=True)

    # Поле ввода
    user_input = st.chat_input(t("chat.input_placeholder"))
    if user_input:
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar=agent_avatar_path):
            thought_placeholder = st.empty()
            tools_container = st.container()
            answer_placeholder = st.empty()

            thought_text = ""
            answer_text = ""
            final_display = ""
            final_thoughts = ""

            try:
                for event in ask_ai_stream(user_input, agent_id=st.session_state.current_agent_id):
                    etype = event.get("type")

                    if etype == "thought":
                        thought_text += event["text"]
                        thought_placeholder.markdown(f'<div class="thoughts-container">{thought_text}</div>', unsafe_allow_html=True)

                    elif etype == "answer":
                        answer_text += event["text"]
                        answer_placeholder.markdown(answer_text)

                    elif etype == "tool_call":
                        with tools_container:
                            st.markdown(f'<span class="tool-chip">⚡ {event["name"]}</span>', unsafe_allow_html=True)

                    elif etype == "tool_result":
                        with tools_container:
                            with st.expander(f"↳ {event['name']} (Result)", expanded=False):
                                st.json(event["result"])

                    elif etype == "done":
                        final_display = event.get("display", answer_text)
                        final_thoughts = event.get("thoughts", thought_text)

            except Exception as e:
                st.error(f"{t('chat.error')}: {e}")
                final_display = answer_text or t("chat.error")

            thought_placeholder.empty()
            tools_container.empty()
            answer_placeholder.empty()

            if final_thoughts:
                with st.expander("💭 Ход рассуждений", expanded=False):
                    st.markdown(f'<div class="thoughts-container">{final_thoughts}</div>', unsafe_allow_html=True)

            st.markdown(final_display)

        st.rerun()


# ═══════════════════════════════════════════════════════════════
# 2. КОНСТРУКТОР АГЕНТОВ (Blob Styling & Presets)
# ═══════════════════════════════════════════════════════════════
elif page == t("nav.agents"):
    page_header(t("agents.title"), "Кастомные ИИ-агенты с органическими аватарами-кляксами", "Grok Mode")

    col_agents, col_builder = st.columns([1, 1], gap="large")

    with col_agents:
        st.markdown(f"### {t('agents.existing')}")
        all_curr_agents = list_agents()

        for a in all_curr_agents:
            badge_type = f'<span style="color:#6ee7b7; font-size:0.7rem;">● {t("agents.builtin")}</span>' if a.is_builtin else f'<span style="color:#a78bfa; font-size:0.7rem;">● {t("agents.custom")}</span>'
            tools_str = "Все инструменты (*)" if "*" in a.allowed_tools else f"{len(a.allowed_tools)} {t('agents.tools_count')}"
            card_blob_svg = generate_blob_svg(a.blob_preset, a.blob_palette, size=44)

            st.markdown(f"""
            <div class="v-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div style="display:flex; gap:14px; align-items:center;">
                        <div class="live-blob" style="width:44px; height:44px;">
                            {card_blob_svg}
                        </div>
                        <div>
                            <div style="display:flex; align-items:center; gap:8px;">
                                <span style="font-weight:700; font-size:1.02rem; color:#fff;">{a.name}</span>
                                <span style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#71717a; background:rgba(255,255,255,0.05); padding:2px 6px; border-radius:4px;">{a.id}</span>
                            </div>
                            <div style="font-size:0.8rem; color:#a1a1aa; margin:4px 0 6px 0;">{a.description or 'Нет описания.'}</div>
                            <div style="display:flex; gap:16px; font-size:0.72rem; color:#71717a; font-family:'JetBrains Mono',monospace;">
                                <span>{tools_str}</span>
                                <span>{badge_type}</span>
                                <span>{a.blob_preset}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not a.is_builtin:
                if st.button(f"🗑️ {t('agents.del')} {a.id}", key=f"del_agent_{a.id}", use_container_width=True):
                    delete_agent(a.id)
                    st.rerun()

    with col_builder:
        st.markdown(f"### {t('agents.create_new')}")

        # ─── ВЫБОР ФОРМЫ И ПАЛИТРЫ ВНЕ ФОРМЫ (для мгновенного превью!) ───
        c_shape, c_palette = st.columns(2)
        with c_shape:
            preset_options = list(BLOB_PATHS.keys())
            new_preset = st.selectbox(
                t("agents.shape"),
                options=preset_options,
                format_func=lambda x: {
                    "plasma": "Плазма (Волна)",
                    "liquid": "Амёба (Жидкость)",
                    "crystal": "Кристалл (Грани)",
                    "droplet": "Капля (Комета)",
                    "nucleus": "Ядро (Атом)",
                }.get(x, x),
                key="builder_preset_select",
            )
        with c_palette:
            palette_options = list(BLOB_PALETTES.keys())
            new_palette = st.selectbox(
                t("agents.palette"),
                options=palette_options,
                format_func=lambda x: {
                    "cyber_indigo": "🟣 Cyber Indigo",
                    "neon_cyan": "🔵 Neon Cyan",
                    "toxic_lime": "🟢 Toxic Lime",
                    "solar_amber": "🟠 Solar Amber",
                    "deep_void": "🔴 Crimson Void",
                }.get(x, x),
                key="builder_palette_select",
            )

        # Живое превью аватара (обновляется мгновенно при смене селектов выше)
        preview_svg = generate_blob_svg(new_preset, new_palette, size=96)
        st.markdown(f"""
        <div class="v-card" style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:16px;">
            <div style="font-size:0.72rem; color:#71717a; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px;">
                {t("agents.preview")}: {new_preset} + {new_palette}
            </div>
            <div class="live-blob" style="width:96px; height:96px;">
                {preview_svg}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ─── ОСТАЛЬНЫЕ ПОЛЯ ВНУТРИ ФОРМЫ ───
        with st.form("agent_builder_form"):
            new_id = st.text_input(t("agents.id"), placeholder="e.g. devops_bot").strip().lower()
            new_name = st.text_input(t("agents.name"), placeholder="e.g. DevOps Engineer")
            new_desc = st.text_input(t("agents.desc"), placeholder="Автоматизация деплоя и работы с логами")

            new_temp = st.slider("Креативность (Temperature)", min_value=0.0, max_value=1.5, value=0.5, step=0.1)
            new_prompt = st.text_area(t("agents.prompt"), value=SYSTEM_PROMPT, height=150)

            all_tools = sorted(list(TOOL_REGISTRY.keys()))
            selected_tools = st.multiselect(
                t("agents.tools"),
                options=all_tools,
                default=["web_search", "fetch_webpage", "get_system_info"],
            )

            submit_agent = st.form_submit_button(f"✨ {t('agents.save')}", use_container_width=True)
            if submit_agent:
                if not new_id or not new_name:
                    st.error("Пожалуйста, заполните ID и Имя агента.")
                elif not selected_tools:
                    st.error("Выберите хотя бы один доступный инструмент.")
                else:
                    new_agent = AgentConfig(
                        id=new_id,
                        name=new_name,
                        description=new_desc,
                        system_prompt=new_prompt,
                        allowed_tools=selected_tools,
                        temperature=new_temp,
                        blob_preset=new_preset,
                        blob_palette=new_palette,
                        is_builtin=False,
                    )
                    save_agent(new_agent)
                    get_agent_avatar_path(new_id, new_preset, new_palette)
                    st.success(f"Агент '{new_name}' успешно создан!")
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
# 3. ПАМЯТЬ
# ═══════════════════════════════════════════════════════════════
elif page == t("nav.memory"):
    page_header(t("memory.title"), "Двухуровневая долговременная память ассистента", "Storage")
    m_col1, m_col2 = st.columns([1, 1], gap="large")

    with m_col1:
        st.markdown(f"### {t('memory.facts')}")
        facts_res = recall_memory()
        memories = facts_res.get("all_memories", {}) if facts_res.get("success") else {}

        if memories:
            for k, v in memories.items():
                st.markdown(f"""
                <div class="v-card" style="padding:0.9rem 1.1rem; margin-bottom:0.6rem;">
                    <div style="font-size:0.68rem; text-transform:uppercase; color:#6366f1; font-weight:700; letter-spacing:0.08em; margin-bottom:4px;">{k}</div>
                    <div style="font-size:0.88rem; color:#e4e4e7;">{v}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(t("memory.facts_empty_title"))

        with st.form("add_memory_fact", clear_on_submit=True):
            st.markdown(t("memory.add_fact"))
            k_input = st.text_input(t("memory.add_key"), placeholder="user_preferred_stack")
            v_input = st.text_area(t("memory.add_value"), placeholder="Python, FastAPI, PyTorch", height=70)
            if st.form_submit_button(f"💾 {t('memory.save')}", use_container_width=True):
                if k_input and v_input:
                    save_memory(k_input, v_input)
                    st.rerun()

    with m_col2:
        st.markdown(f"### {t('memory.vector')}")
        v_stats = get_stats()
        v_count = v_stats.get("total_conversations", 0) if v_stats.get("success") else 0

        st.markdown(f"""
        <div class="v-metric">
            <div class="v-metric-title">{t('memory.vector_count')}</div>
            <div class="v-metric-val">{v_count}</div>
            <div class="v-metric-sub">{t('memory.vector_sub')}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)
        s_query = st.text_input(t("memory.search"), placeholder=t("memory.search_placeholder"))
        if s_query:
            with st.spinner(t("memory.searching")):
                sr = search_conversations(s_query, n_results=4)
                if sr.get("success") and sr.get("results"):
                    for r in sr["results"]:
                        st.markdown(f"""
                        <div class="v-card" style="padding:0.8rem 1rem;">
                            <div style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#71717a; margin-bottom:4px;">
                                {r['timestamp'][:16]} · dist: {r['distance']}
                            </div>
                            <div style="font-size:0.84rem; color:#d4d4d8; line-height:1.5;">{r['text'][:350]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info(t("memory.nothing_found"))


# ═══════════════════════════════════════════════════════════════
# 4. ФОНОВЫЕ ЗАДАЧИ
# ═══════════════════════════════════════════════════════════════
elif page == t("nav.tasks"):
    page_header(t("tasks.title"), "Периодические проверки и уведомления планировщика", t("tasks.status"))
    jobs = _load_jobs()
    if not jobs:
        st.info(t("tasks.empty_title"))
    else:
        for j in jobs:
            c_info, c_act = st.columns([5, 1])
            with c_info:
                st.markdown(f"""
                <div class="v-card">
                    <div style="font-weight:600; color:#fff; font-size:1rem;">{j.get('name', 'Task')}</div>
                    <div style="font-size:0.75rem; color:#71717a; font-family:'JetBrains Mono',monospace; margin-top:4px;">
                        Каждые {j.get('minutes')} мин · тип: {j.get('task_type', 'ai_task')} · ID: {j.get('id')}
                    </div>
                    <div style="font-size:0.82rem; color:#a1a1aa; margin-top:6px;">Промпт: <i>{j.get('prompt', '')}</i></div>
                </div>
                """, unsafe_allow_html=True)
            with c_act:
                st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
                if st.button("Удалить", key=f"del_job_{j['id']}", use_container_width=True):
                    remove_scheduled_task(j["id"])
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
# 5. ТОКЕНЫ И РАСХОД
# ═══════════════════════════════════════════════════════════════
elif page == t("nav.tokens"):
    page_header(t("tokens.title"), "Локальная аналитика потребления и стоимости токенов", "API Analytics")
    from core.usage_tracker import get_stats as usage_stats, reset_usage
    u_data = usage_stats()
    today = u_data["today"]
    total = u_data["total"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="v-metric">
            <div class="v-metric-title">{t('tokens.today')}</div>
            <div class="v-metric-val">${today['cost_usd']:.4f}</div>
            <div class="v-metric-sub">{today['requests']} {t('tokens.requests')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="v-metric">
            <div class="v-metric-title">{t('tokens.total')}</div>
            <div class="v-metric-val">${total['cost_usd']:.3f}</div>
            <div class="v-metric-sub">{total['requests']} {t('tokens.requests')}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        today_tokens = today['prompt_tokens'] + today['completion_tokens']
        st.markdown(f"""
        <div class="v-metric">
            <div class="v-metric-title">{t('tokens.tokens_today')}</div>
            <div class="v-metric-val">{today_tokens:,}</div>
            <div class="v-metric-sub">{today['prompt_tokens']:,} in / {today['completion_tokens']:,} out</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="v-metric">
            <div class="v-metric-title">{t('tokens.cache_hit')}</div>
            <div class="v-metric-val">{u_data['cache_hit_rate']}%</div>
            <div class="v-metric-sub">{total['cached_tokens']:,} {t('tokens.cached')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    with st.expander(f"⚙️ {t('tokens.manage')}"):
        st.caption(t("tokens.manage_desc"))
        if st.button(t("tokens.reset"), use_container_width=True):
            reset_usage()
            st.rerun()


# ═══════════════════════════════════════════════════════════════
# 6. СТАТУС СИСТЕМЫ
# ═══════════════════════════════════════════════════════════════
elif page == t("nav.status"):
    page_header(t("status.title"), "Телеметрия локального ПК (CPU, RAM, GPU, Disks)", "Telemetry")
    sys_info = get_system_info()
    c_cpu, c_ram, c_os = st.columns(3)

    with c_cpu:
        cpu_pct = sys_info.get("cpu_usage_percent", 0)
        st.markdown(f"""
        <div class="v-metric">
            <div class="v-metric-title">CPU Load</div>
            <div class="v-metric-val">{cpu_pct}%</div>
            <div class="v-metric-sub">{sys_info.get('cpu', '')[:35]}</div>
        </div>
        """, unsafe_allow_html=True)

    with c_ram:
        ram = sys_info.get("ram", {})
        ram_pct = ram.get("usage_percent", 0)
        st.markdown(f"""
        <div class="v-metric">
            <div class="v-metric-title">RAM Usage</div>
            <div class="v-metric-val">{ram_pct}%</div>
            <div class="v-metric-sub">{ram.get('used_gb')} / {ram.get('total_gb')} GB</div>
        </div>
        """, unsafe_allow_html=True)

    with c_os:
        st.markdown(f"""
        <div class="v-metric">
            <div class="v-metric-title">Environment</div>
            <div class="v-metric-val">{sys_info.get('os', '?')}</div>
            <div class="v-metric-sub">{sys_info.get('architecture', '')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("### GPU Status")
    try:
        gpu_info = get_gpu_info()
        if gpu_info.get("success") and gpu_info.get("gpus"):
            for g in gpu_info["gpus"]:
                st.markdown(f"""
                <div class="v-card">
                    <div style="font-weight:700; font-size:1.1rem; color:#fff;">{g['name']}</div>
                    <div style="display:flex; gap:24px; font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#a1a1aa; margin-top:8px;">
                        <span>Temp: <b>{g['temperature_c']}°C</b></span>
                        <span>Load: <b>{g['gpu_usage_percent']}%</b></span>
                        <span>VRAM: <b>{g['vram_used_gb']} / {g['vram_total_gb']} GB</b></span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(t("status.gpu_not_found"))
    except Exception as ex:
        st.warning(f"GPU Telemetry: {ex}")


# ═══════════════════════════════════════════════════════════════
# 7. ЛОГИ
# ═══════════════════════════════════════════════════════════════
elif page == t("nav.logs"):
    page_header(t("logs.title"), "Журнал работы ассистента и вызовов инструментов", "Debug")
    if not LOG_FILE.exists():
        st.info(t("logs.empty_title"))
    else:
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as lf:
                lines = lf.readlines()[-250:]
            st.code("".join(lines), language="log")
        except Exception as ex:
            st.error(f"{t('common.error')}: {ex}")