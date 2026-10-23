# ◈ Vanta AI

**Vanta** is a modular personal AI assistant for Windows built in Python. It combines OpenAI tool calling, customizable **agent personas**, two-tier memory (JSON facts + ChromaDB vector search), system telemetry, GUI automation, and a dark glassmorphic Streamlit dashboard.

---

## ✨ Key Features

- **🤖 Custom Agent Personas** — Switch between specialized built-in agents (`Vanta Core`, `Developer`, `SysAdmin`, `Researcher`) or build your own custom agents with isolated system prompts, temperature settings, and granular tool permissions.
  <img width="1528" height="1025" alt="{BEEEABFA-B9CC-4E05-BEC2-420C488C3E2A}" src="https://github.com/user-attachments/assets/210cd63a-ee18-4adb-83af-d7a635328d9d" />

- **🔮 Procedural Animated SVG Blobs** — Each agent features a living, morphing SVG avatar with customizable geometry (`plasma`, `liquid`, `crystal`, `droplet`, `nucleus`) and neon color palettes.

<img width="1792" height="2400" alt="blobs" src="https://github.com/user-attachments/assets/4c196a3c-e2b9-4755-80b0-5232ff48749d" />

- **🧠 Two-Tier Long-Term Memory** — Instant key-value fact storage (`data/memory.json`) paired with semantic conversation search powered by **ChromaDB** and OpenAI embeddings (`text-embedding-3-small`).
- **🛡️ Sandboxed Execution & Path Security** — Strict path validation (`safe_path`) prevents path traversal, blocks access to sensitive `.env` files, protects Vanta's source code from self-modification, and executes allowed shell commands without injection risks.
- **🖥️ Desktop & System Automation** — Real-time CPU, RAM, disk, and NVIDIA GPU telemetry (`psutil`, `pynvml`), audio control (`pycaw`), window management, mouse/keyboard control (`PyAutoGUI`), and screen analysis via OpenAI Vision (`gpt-4o-mini`).
- **🌐 Web Research & OSINT** — DuckDuckGo search (`ddgs`), clean webpage text extraction (`httpx` + `BeautifulSoup`), Sherlock OSINT username lookup, and quick browser launchers.
- **💬 Three Interfaces** — Interactive **Streamlit Dashboard**, **Rich CLI**, and background **Telegram Bot** with an integrated recurring task scheduler (`APScheduler`).
- **📊 Token & Cost Analytics** — Thread-safe usage tracking (`data/usage.json`) calculating per-request and daily token costs, including cached prompt token discounts.
  <img width="1514" height="562" alt="{86EAA56C-50BE-4760-B14D-C43551D37DCF}" src="https://github.com/user-attachments/assets/f23b4e05-dea2-4892-9ea6-0ab57550c358" />

- **🌍 Multilingual UI** — Full localization in **English**, **Russian**, **Ukrainian**, and **Polish**.

---

## 🗂️ Project Structure

```text
vanta/
├── core/
│   ├── agents.py          # Custom agent profiles & tool filtering
│   ├── api_client.py      # OpenAI API client (Chat, Vision, Embeddings)
│   ├── blobs.py           # Procedural animated SVG blob generator
│   ├── brain.py           # Thread-safe agent loop & tool execution
│   ├── i18n.py            # UI localization (RU, EN, UK, PL)
│   ├── logger.py          # Rotating file & console logger
│   ├── memory.py          # Long-term key-value fact memory
│   ├── prompts.py         # Core system instructions
│   ├── scheduler.py       # APScheduler background task runner
│   ├── schemas.py         # OpenAI function calling schemas
│   ├── settings.py        # Persistent user settings
│   ├── usage_tracker.py   # Token & USD cost analytics
│   ├── validators.py      # Pydantic v2 argument validation schemas
│   └── vector_memory.py   # ChromaDB semantic conversation memory
├── interfaces/
│   ├── dashboard.py       # Streamlit web UI & Agent Builder
│   ├── main.py            # Rich CLI entrypoint
│   └── tg_bot.py          # Telegram bot interface
├── tools/
│   ├── code.py            # AST code analysis & code generation
│   ├── file_tools.py      # Sandboxed file operations & command runner
│   ├── gui.py             # Mouse, keyboard & window automation
│   ├── programs.py        # Application & URL launcher
│   ├── sandbox.py         # Isolated sandbox directory tools
│   ├── system.py          # Hardware telemetry, screenshots & audio
│   ├── web.py             # DuckDuckGo search, webpage parser & OSINT
│   └── web_apps.py        # Quick web service openers
├── tests/
│   └── test_vanta_core.py # Security, validation & agent unit tests
├── config.py              # Environment & directory configuration
├── pyproject.toml         # Package & pytest configuration
└── requirements.txt       # Project dependencies
```
🚀 Quick Start
1. Clone the repository
```Bash
git clone https://github.com/YOUR_USERNAME/vanta.git
cd vanta
```

2. Create a virtual environment & install dependencies
```PowerShell

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```
3. Configure environment variables

Create a .env file in the root directory:
```

# Required
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1

# Models (optional, defaults shown)
MAIN_MODEL=gpt-5-mini
VISION_MODEL=gpt-4o-mini
EMBED_MODEL=text-embedding-3-small

# Sandbox path (optional, defaults to D:\Vanta_Sandbox or data/sandbox)
SANDBOX_DIR=D:\Vanta_Sandbox

# Telegram Bot (optional — set TELEGRAM_TOKEN=disabled to turn off)
TELEGRAM_TOKEN=disabled
ALLOWED_USER_ID=0
```
💻 Usage
Launch the Web Dashboard (Recommended)
```PowerShell

streamlit run interfaces/dashboard.py
```
Gives you access to the Chat, Agent Builder (Grok Mode), Memory Manager, Background Tasks, Token Analytics, System Telemetry, and Live Logs.
Launch the CLI + Background Telegram Bot
```PowerShell

python interfaces/main.py
```
Telegram Bot Commands

When TELEGRAM_TOKEN and ALLOWED_USER_ID are configured in .env, the bot supports:

    /start — Greeting and status

    /agent — List available agents or switch active profile (/agent coder)

    /clear — Reset conversation context

    /memory — View saved facts and vector memory count

    /jobs — List active scheduled tasks

    /status — Check CPU, RAM, and OS load

🧪 Running Tests

The test suite verifies path traversal protection, .env and source code write-protection, command execution rules, Pydantic tool argument validation, and agent tool filtering:
PowerShell
```
python -m pytest -v
```
📄 License

This project is licensed under the MIT License.
