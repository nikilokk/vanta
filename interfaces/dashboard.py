# interfaces/dashboard.py
"""
Веб-дашборд Vanta на Streamlit с glassmorphism-стилем.
Запуск: streamlit run interfaces/dashboard.py
"""
import sys
import os
from pathlib import Path

# === ПУТИ ===
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    libs_path = PROJECT_ROOT / "libs"
    if libs_path.exists():
        os.add_dll_directory(str(libs_path))

from core.logger import setup_logging
setup_logging()

import streamlit as st
from datetime import datetime

import time

# === НАСТРОЙКА СТРАНИЦЫ ===
st.set_page_config(
    page_title="Vanta",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# === VANTA ===
from core.brain import ask_ai, clear_chat_history, chat_history
from core.memory import recall_memory, save_memory, forget_memory
from core.vector_memory import get_stats, search_conversations
from core.scheduler import _load_jobs, add_interval_task, remove_scheduled_task
from tools.system import get_system_info, get_gpu_info
from config import DATA_DIR

LOG_FILE = DATA_DIR / "vanta.log"

def _typewriter(text: str, speed: float = 0.012, chunk_size: int = 1):
    """
    Генератор для эффекта печатной машинки.
    speed — задержка в секундах между кусками.
    chunk_size — сколько символов за раз (для длинных текстов увеличиваем).
    """
    if not text:
        return
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]
        time.sleep(speed)


# ═══════════════════════════════════════════════════════════════
# 🎨 СТИЛЬ
# ═══════════════════════════════════════════════════════════════
GLASS_CSS = """
<style>
/* === ФОН И СВЕТОВЫЕ ОРБЫ === */
.stApp {
    background: radial-gradient(circle at 15% 15%, #1e1b4b 0%, #0a0a15 45%),
                radial-gradient(circle at 85% 85%, #1e293b 0%, transparent 50%);
    background-attachment: fixed;
}

.glow-orb {
    position: fixed;
    border-radius: 50%;
    filter: blur(100px);
    opacity: 0.35;
    pointer-events: none;
    z-index: 0;
}
.orb-1 { width: 400px; height: 400px; background: #6366f1; top: -100px; left: -100px; animation: float1 18s ease-in-out infinite; }
.orb-2 { width: 350px; height: 350px; background: #a855f7; bottom: -80px; right: -80px; animation: float2 22s ease-in-out infinite; }
.orb-3 { width: 300px; height: 300px; background: #06b6d4; top: 40%; left: 50%; animation: float3 25s ease-in-out infinite; }

@keyframes float1 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(80px,60px) scale(1.15); } }
@keyframes float2 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(-70px,-50px) scale(1.2); } }
@keyframes float3 { 0%,100% { transform: translate(-50%,-50%) scale(1); } 50% { transform: translate(-30%,-70%) scale(0.9); } }

.block-container { position: relative; z-index: 1; padding-top: 2rem; }

/* === ТЕКСТ === */
h1, h2, h3 { color: #f1f5f9 !important; letter-spacing: -0.02em; }
p, span, label, div { color: #cbd5e1; }

/* === САЙДБАР === */
section[data-testid="stSidebar"] {
    background: rgba(15, 15, 30, 0.6) !important;
    backdrop-filter: blur(20px) saturate(1.5);
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* === СТЕКЛЯННЫЕ КАРТОЧКИ === */
.glass-card {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(20px) saturate(1.4);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-top: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 18px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    transition: all 0.25s ease;
}
.glass-card:hover {
    border-top-color: rgba(255, 255, 255, 0.28);
    box-shadow: 0 12px 40px rgba(99, 102, 241, 0.18);
    transform: translateY(-1px);
}

/* === КАТЕГОРИИ-БЭЙДЖИ === */
.category-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    backdrop-filter: blur(10px);
}
.cat-info { background: rgba(96,165,250,0.18); color: #93c5fd; border: 1px solid rgba(96,165,250,0.3); }

/* === ПРОГРЕСС-БАР === */
.progress-wrap {
    height: 8px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    overflow: hidden;
    margin: 12px 0 4px;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #06b6d4 100%);
    border-radius: 10px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 0 12px rgba(99, 102, 241, 0.5);
}

/* === КНОПКИ === */
.stButton > button {
    background: rgba(255, 255, 255, 0.06) !important;
    backdrop-filter: blur(12px);
    color: #e2e8f0 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 12px !important;
    transition: all 0.2s ease !important;
    font-weight: 500 !important;
}
.stButton > button:hover {
    background: rgba(99, 102, 241, 0.18) !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.25) !important;
}

/* === ИНПУТЫ === */
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"],
.stNumberInput input {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.18) !important;
    backdrop-filter: blur(12px);
    color: #e2e8f0 !important;
    border-radius: 12px !important;
    transition: all 0.2s ease;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: rgba(99, 102, 241, 0.5) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
}

/* === ЧАТ === */
.stChatMessage {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px !important;
    padding: 1rem 1.2rem !important;
    margin-bottom: 0.6rem !important;
}

/* === EMPTY STATE === */
.empty-state {
    text-align: center;
    padding: 3rem 1rem;
    color: #94a3b8;
}
.empty-state .icon { font-size: 3rem; opacity: 0.6; margin-bottom: 1rem; display: block; }
.empty-state .title { font-size: 1.1rem; font-weight: 600; color: #cbd5e1; margin-bottom: 0.3rem; }
.empty-state .subtitle { font-size: 0.85rem; opacity: 0.7; }

/* === СКРЫТЬ ФУТЕР === */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
</style>

<!-- Световые орбы -->
<div class="glow-orb orb-1"></div>
<div class="glow-orb orb-2"></div>
<div class="glow-orb orb-3"></div>
"""

st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# 🧭 САЙДБАР
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🤖 Vanta")
    st.caption("Личный AI-ассистент")
    st.markdown("---")

    page = st.radio(
        "Навигация",
        ["💬 Чат", "🧠 Память", "⏰ Задачи", "💻 Статус", "📋 Логи"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.caption(f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    if st.button("🗑 Очистить контекст чата", use_container_width=True):
        clear_chat_history()
        st.success("Очищено")


# ═══════════════════════════════════════════════════════════════
# 💬 ЧАТ
# ═══════════════════════════════════════════════════════════════
if page == "💬 Чат":
    st.markdown("# 💬 Чат с Vanta")

    for msg in chat_history[1:]:
        role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
        if role == "user" and content:
            with st.chat_message("user"):
                st.markdown(content)
        elif role == "assistant" and content:
            with st.chat_message("assistant"):
                st.markdown(content)

    user_input = st.chat_input("Напиши сообщение...")
    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            # Показываем "думает", пока модель генерит
            with st.spinner("Vanta думает..."):
                try:
                    result = ask_ai(user_input)
                    response = result["display"] if isinstance(result, dict) else str(result)
                except Exception as e:
                    st.error(f"Ошибка: {e}")
                    response = None

            # Плавно печатаем ответ
            if response:
                # Для длинных текстов печатаем быстрее и большими кусками
                if len(response) > 500:
                    speed, chunk = 0.005, 3
                elif len(response) > 200:
                    speed, chunk = 0.008, 2
                else:
                    speed, chunk = 0.012, 1

                st.write_stream(_typewriter(response, speed=speed, chunk_size=chunk))

        st.rerun()


# ═══════════════════════════════════════════════════════════════
# 🧠 ПАМЯТЬ
# ═══════════════════════════════════════════════════════════════
elif page == "🧠 Память":
    st.markdown("# 🧠 Память")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📌 Факты")
        result = recall_memory()
        memories = result.get("all_memories", {}) if result.get("success") else {}

        if memories:
            for key, value in memories.items():
                st.markdown(f"""
                <div class="glass-card" style="padding:0.8rem 1rem;">
                    <div style="font-size:0.75rem; color:#94a3b8; letter-spacing:0.05em;">🔑 {key}</div>
                    <div style="margin-top:6px; color:#e2e8f0;">{value}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <span class="icon">💭</span>
                <div class="title">Фактов пока нет</div>
                <div class="subtitle">Ванта запомнит, что ты ей расскажешь</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        with st.form("add_fact"):
            st.markdown("**➕ Добавить факт**")
            new_key = st.text_input("Ключ")
            new_value = st.text_area("Значение")
            if st.form_submit_button("Сохранить"):
                if new_key and new_value:
                    save_memory(new_key, new_value)
                    st.rerun()

    with col2:
        st.subheader("💬 Векторная память")
        stats = get_stats()
        count = stats.get("total_conversations", 0) if stats.get("success") else 0

        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size:0.75rem; color:#94a3b8; letter-spacing:0.08em;">ДИАЛОГОВ СОХРАНЕНО</div>
            <div style="font-size:2rem; font-weight:700; color:#f1f5f9; margin-top:4px;">{count}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        query = st.text_input("🔍 Поиск по смыслу")
        if query:
            with st.spinner("Ищу..."):
                sr = search_conversations(query, n_results=5)
                if sr.get("success") and sr.get("results"):
                    for r in sr["results"]:
                        st.markdown(f"""
                        <div class="glass-card" style="padding:0.9rem 1rem;">
                            <div style="font-size:0.72rem; color:#94a3b8;">📅 {r['timestamp'][:16]} · точность {r['distance']}</div>
                            <div style="margin-top:6px; font-size:0.9rem;">{r['text'][:400]}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Ничего не найдено.")


# ═══════════════════════════════════════════════════════════════
# ⏰ ЗАДАЧИ (планировщик)
# ═══════════════════════════════════════════════════════════════
elif page == "⏰ Задачи":
    st.markdown("# ⏰ Фоновые задачи")
    st.caption("Выполняются в CLI-процессе, а не здесь")

    jobs = _load_jobs()

    if not jobs:
        st.markdown("""
        <div class="empty-state">
            <span class="icon">⏳</span>
            <div class="title">Нет активных задач</div>
            <div class="subtitle">Создай задачу через чат: "напоминай мне каждые 30 минут..."</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for job in jobs:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"""
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:start;">
                        <div>
                            <div style="font-size:1rem; font-weight:600; color:#e2e8f0;">{job.get('name', 'task')}</div>
                            <div style="font-size:0.8rem; color:#94a3b8; margin-top:4px;">
                                каждые {job.get('minutes')} мин · <code>{job.get('task_type', 'ai_task')}</code>
                            </div>
                        </div>
                        <div style="font-size:0.7rem; color:#64748b;">{job.get('id')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("🗑", key=f"deljob_{job['id']}"):
                    remove_scheduled_task(job["id"])
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
# 💻 СТАТУС
# ═══════════════════════════════════════════════════════════════
elif page == "💻 Статус":
    st.markdown("# 💻 Состояние системы")

    try:
        info = get_system_info()
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:0.75rem; color:#94a3b8; letter-spacing:0.08em;">CPU</div>
                <div style="font-size:1.8rem; font-weight:700; color:#f1f5f9;">{info.get('cpu_usage_percent', '?')}%</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            ram = info.get("ram", {})
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:0.75rem; color:#94a3b8; letter-spacing:0.08em;">RAM</div>
                <div style="font-size:1.8rem; font-weight:700; color:#f1f5f9;">{ram.get('usage_percent', '?')}%</div>
                <div style="font-size:0.78rem; color:#94a3b8;">{ram.get('used_gb')}/{ram.get('total_gb')} GB</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:0.75rem; color:#94a3b8; letter-spacing:0.08em;">OS</div>
                <div style="font-size:1.2rem; font-weight:600; color:#f1f5f9; margin-top:8px;">{info.get('os', '?')}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 💾 Диски")
        for disk in info.get("disks", []):
            pct = disk["usage_percent"]
            st.markdown(f"""
            <div class="glass-card" style="padding:0.9rem 1.2rem;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#cbd5e1;">
                    <span>{disk['drive']}</span>
                    <span>{disk['used_gb']} / {disk['total_gb']} GB</span>
                </div>
                <div class="progress-wrap">
                    <div class="progress-fill" style="width:{pct}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### 🎮 GPU")
        try:
            gi = get_gpu_info()
            if gi.get("success"):
                for gpu in gi.get("gpus", []):
                    st.markdown(f"""
                    <div class="glass-card">
                        <div style="font-weight:600; color:#e2e8f0;">{gpu['name']}</div>
                        <div style="display:flex; gap:24px; margin-top:8px; font-size:0.85rem; color:#94a3b8;">
                            <span>🌡 {gpu['temperature_c']}°C</span>
                            <span>⚡ {gpu['gpu_usage_percent']}%</span>
                            <span>💾 {gpu['vram_used_gb']} / {gpu['vram_total_gb']} GB</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("GPU не обнаружен.")
        except Exception as e:
            st.warning(f"GPU: {e}")
    except Exception as e:
        st.error(f"Ошибка: {e}")


# ═══════════════════════════════════════════════════════════════
# 📋 ЛОГИ
# ═══════════════════════════════════════════════════════════════
elif page == "📋 Логи":
    st.markdown("# 📋 Логи Vanta")

    if not LOG_FILE.exists():
        st.info("Лог-файл пуст.")
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
            st.caption(f"Всего строк: {len(all_lines)}")
        except Exception as e:
            st.error(f"Ошибка чтения: {e}")