# Vanta

Personal AI assistant with GUI automation, long-term memory, and multi-interface support.

## Features

- 🤖 **OpenAI-powered** (gpt-5-mini, gpt-4o-mini for vision)
- 🧠 **Long-term memory** — key-value facts + vector search (ChromaDB)
- 🖥️ **GUI automation** — mouse, keyboard, screenshots
- 🌐 **Specialized web tools** — YouTube, Google, Discord, Spotify, GitHub, and more
- 💬 **Three interfaces** — CLI, Telegram bot, Streamlit dashboard
- ⏰ **Background scheduler** — recurring tasks with notifications
- 📊 **Token usage tracking** — per-request cost analysis
- 🌍 **Multilingual UI** — Russian, English, Ukrainian, Polish

## Quick Start

```bash
git clone https://github.com/YOUR_USERNAME/vanta
cd vanta

python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
cp .env.example .env
# Edit .env, add your OPENAI_API_KEY

python interfaces/main.py