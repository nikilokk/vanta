# core/agents.py
"""
Менеджер агентов Vanta (в стиле Grok Bots / Custom Personas).
Поддерживает процедурные кляксы (Blobs), изолированные промпты и списки инструментов.
"""
import json
import threading
from pathlib import Path
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from config import DATA_DIR
from core.logger import get_logger
from core.prompts import SYSTEM_PROMPT

logger = get_logger(__name__)
AGENTS_FILE = DATA_DIR / "agents.json"
_agents_lock = threading.RLock()


class AgentConfig(BaseModel):
    id: str = Field(..., description="Уникальный идентификатор (латиница, a-z, 0-9, _)")
    name: str = Field(..., description="Отображаемое имя")
    description: str = Field("", description="Краткое описание роли")
    system_prompt: str = Field(..., description="Системный промпт (инструкции)")
    allowed_tools: List[str] = Field(default_factory=list, description="Список разрешенных инструментов")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    
    # ─── Визуальные настройки в стиле Grok Blob ───
    blob_preset: str = Field(default="plasma", description="Форма: plasma, liquid, crystal, droplet, nucleus")
    blob_palette: str = Field(default="cyber_indigo", description="Палитра: cyber_indigo, neon_cyan, toxic_lime, solar_amber, deep_void")
    
    is_builtin: bool = Field(default=False, description="Защита от удаления базовых профилей")


BUILTIN_AGENTS: Dict[str, AgentConfig] = {
    "default": AgentConfig(
        id="default",
        name="Vanta Core",
        description="Универсальный личный ассистент с полным доступом к функциям",
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["*"],
        temperature=0.7,
        blob_preset="plasma",
        blob_palette="cyber_indigo",
        is_builtin=True,
    ),
    "coder": AgentConfig(
        id="coder",
        name="Vanta Developer",
        description="Специалист по программированию, анализу кода и работе в песочнице",
        system_prompt=(
            f"{SYSTEM_PROMPT}\n\n"
            "## СПЕЦИАЛИЗАЦИЯ: РАЗРАБОТКА ПО\n"
            "Твоя задача — писать, рефакторить и тестировать код. "
            "Работай преимущественно внутри песочницы (sandbox). "
            "Перед внесением изменений всегда проверяй синтаксис и существующие тесты."
        ),
        allowed_tools=[
            "read_sandbox_file", "write_sandbox_file", "list_sandbox_files",
            "analyze_codebase", "run_command", "search_files", "read_file"
        ],
        temperature=0.2,
        blob_preset="crystal",
        blob_palette="neon_cyan",
        is_builtin=True,
    ),
    "sysadmin": AgentConfig(
        id="sysadmin",
        name="Vanta SysAdmin",
        description="Мониторинг ресурсов, диагностика ПК и управление процессами Windows",
        system_prompt=(
            f"{SYSTEM_PROMPT}\n\n"
            "## СПЕЦИАЛИЗАЦИЯ: АДМИНИСТРИРОВАНИЕ WINDOWS\n"
            "Ты системный инженер. Твоя цель — контролировать состояние компьютера, "
            "загрузку CPU/GPU, свободное место на дисках и управлять запущенными процессами. "
            "Не закрывай критические системные процессы."
        ),
        allowed_tools=[
            "get_system_info", "get_gpu_info", "get_running_processes",
            "close_program", "get_uptime", "list_windows", "activate_window",
            "set_volume", "toggle_mute"
        ],
        temperature=0.2,
        blob_preset="liquid",
        blob_palette="toxic_lime",
        is_builtin=True,
    ),
    "researcher": AgentConfig(
        id="researcher",
        name="Vanta Researcher",
        description="Глубокий веб-поиск, чтение статей и OSINT-анализ",
        system_prompt=(
            f"{SYSTEM_PROMPT}\n\n"
            "## СПЕЦИАЛИЗАЦИЯ: ИССЛЕДОВАНИЯ И ВЕБ-ПОИСК\n"
            "Твоя задача — искать достоверную информацию в интернете. "
            "Используй web_search для поиска ссылок и fetch_webpage для извлечения текста страниц. "
            "Обязательно структурируй выводы и приводи источники."
        ),
        allowed_tools=[
            "web_search", "fetch_webpage", "search_username_osint",
            "get_current_datetime", "wikipedia_search", "github_search",
            "save_memory", "search_memory"
        ],
        temperature=0.5,
        blob_preset="nucleus",
        blob_palette="solar_amber",
        is_builtin=True,
    ),
}


def _load_agents_from_disk() -> Dict[str, AgentConfig]:
    agents = dict(BUILTIN_AGENTS)
    if not AGENTS_FILE.exists():
        _save_agents_to_disk(agents)
        return agents

    try:
        with open(AGENTS_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        for agent_dict in raw_data:
            try:
                cfg = AgentConfig(**agent_dict)
                # Для встроенных агентов всегда принудительно берем актуальный дизайн из BUILTIN_AGENTS
                if cfg.id in BUILTIN_AGENTS:
                    agents[cfg.id] = BUILTIN_AGENTS[cfg.id]
                else:
                    agents[cfg.id] = cfg
            except Exception as e:
                logger.error(f"Agents: ошибка парсинга профиля {agent_dict.get('id')}: {e}")

    except Exception as e:
        logger.error(f"Agents: ошибка загрузки {AGENTS_FILE}: {e}")

    return agents


def _save_agents_to_disk(agents: Dict[str, AgentConfig]):
    try:
        data = [agent.model_dump() for agent in agents.values()]
        with open(AGENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Agents: ошибка сохранения {AGENTS_FILE}: {e}")


def get_agent(agent_id: str = "default") -> AgentConfig:
    with _agents_lock:
        agents = _load_agents_from_disk()
        return agents.get(agent_id, agents["default"])


def list_agents() -> List[AgentConfig]:
    with _agents_lock:
        return list(_load_agents_from_disk().values())


def save_agent(config: AgentConfig) -> bool:
    with _agents_lock:
        agents = _load_agents_from_disk()
        agents[config.id] = config
        _save_agents_to_disk(agents)
        logger.info(f"Agents: сохранён агент '{config.id}' ({config.name})")
        return True


def delete_agent(agent_id: str) -> bool:
    with _agents_lock:
        agents = _load_agents_from_disk()
        if agent_id in agents:
            if agents[agent_id].is_builtin:
                logger.warning(f"Agents: попытка удалить встроенного агента '{agent_id}'")
                return False
            del agents[agent_id]
            _save_agents_to_disk(agents)
            logger.info(f"Agents: удалён агент '{agent_id}'")
            return True
        return False


def filter_tools_for_agent(agent: AgentConfig, all_tools_schemas: list) -> list:
    if "*" in agent.allowed_tools:
        return all_tools_schemas

    allowed_set = set(agent.allowed_tools)
    return [
        t for t in all_tools_schemas
        if t.get("function", {}).get("name") in allowed_set
    ]