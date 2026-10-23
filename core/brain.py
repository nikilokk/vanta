# core/brain.py
"""
Ядро Vanta. Потокобезопасная реализация цикла общения с LLM
с поддержкой профилей агентов (Grok Bots mode).
"""
import json
import os
import re
import threading
import time

from rich.console import Console

from core.agents import get_agent, filter_tools_for_agent, AgentConfig
from core.logger import get_logger
from core.memory import forget_memory, recall_memory, save_memory
from core.prompts import SYSTEM_PROMPT
from core.schemas import TOOLS
from core.vector_memory import save_conversation, search_conversations

from tools import (
    search_files, read_file, write_file, edit_file, run_command,
    get_system_info, get_gpu_info, get_running_processes, close_program,
    get_uptime, take_screenshot, get_clipboard, set_clipboard,
    set_volume, toggle_mute, get_screen_size, wait, analyze_screenshot,
    open_program, open_website,
    web_search, search_username_osint, get_current_datetime,
    list_sandbox_files, read_sandbox_file, write_sandbox_file,
    analyze_codebase, generate_code_local,
    add_interval_task, list_scheduled_tasks, remove_scheduled_task,
    move_mouse, click_mouse, double_click, right_click,
    drag_mouse, scroll_mouse, get_mouse_position,
    type_text, press_key, hotkey,
    list_windows, activate_window,
    find_on_screen, click_on_image,
    google_search, youtube_search, wikipedia_search, github_search,
    stackoverflow_search, reddit_search, maps_search, translate_text,
    discord_open, discord_send,
    spotify_play, twitch_search,
)
from tools.web import fetch_webpage

logger = get_logger(__name__)
console = Console()

MAX_STEPS = 20
MAX_SECONDS = 300
MAX_HISTORY = 15
MAX_FACTS_IN_PROMPT = 30

_brain_lock = threading.RLock()


class _Function:
    def __init__(self, f: dict):
        self.name = f["name"]
        self.arguments = f["arguments"]


class _ToolCall:
    def __init__(self, tc: dict):
        self.function = _Function(tc["function"])
        self.id = tc.get("id")


class _Message:
    def __init__(self, d: dict):
        self.content = d.get("content", "")
        self.thinking = None
        tool_calls = d.get("tool_calls")
        self.tool_calls = [_ToolCall(tc) for tc in tool_calls] if tool_calls else None


class _Response:
    def __init__(self, resp_dict: dict):
        self.message = _Message(resp_dict["message"])
        self.usage = resp_dict.get("usage")


def _wrap_api_response(resp_dict: dict) -> _Response:
    return _Response(resp_dict)


def _remember_conversation(summary: str):
    return save_conversation(user_message=summary, assistant_response="(запомнено)")


def _search_memory(query: str):
    result = search_conversations(query, n_results=3)
    if not result.get("success"):
        return result
    if not result.get("results"):
        return {"success": True, "message": "Ничего не найдено."}

    lines = [f"[{r['timestamp'][:16]}] {r['text']}" for r in result["results"]]
    return {"success": True, "memories": "\n\n".join(lines)}


TOOL_REGISTRY = {
    "search_files": search_files,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "run_command": run_command,
    "get_system_info": get_system_info,
    "get_gpu_info": get_gpu_info,
    "get_running_processes": get_running_processes,
    "close_program": close_program,
    "get_uptime": get_uptime,
    "take_screenshot": take_screenshot,
    "analyze_screenshot": analyze_screenshot,
    "get_screen_size": get_screen_size,
    "wait": wait,
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,
    "set_volume": set_volume,
    "toggle_mute": toggle_mute,
    "open_program": open_program,
    "open_website": open_website,
    "web_search": web_search,
    "fetch_webpage": fetch_webpage,
    "search_username_osint": search_username_osint,
    "get_current_datetime": get_current_datetime,
    "save_memory": save_memory,
    "recall_memory": recall_memory,
    "forget_memory": forget_memory,
    "remember_conversation": _remember_conversation,
    "search_memory": _search_memory,
    "list_sandbox_files": list_sandbox_files,
    "read_sandbox_file": read_sandbox_file,
    "write_sandbox_file": write_sandbox_file,
    "analyze_codebase": analyze_codebase,
    "generate_code_local": generate_code_local,
    "add_interval_task": add_interval_task,
    "list_scheduled_tasks": list_scheduled_tasks,
    "remove_scheduled_task": remove_scheduled_task,
    "move_mouse": move_mouse,
    "click_mouse": click_mouse,
    "double_click": double_click,
    "right_click": right_click,
    "drag_mouse": drag_mouse,
    "scroll_mouse": scroll_mouse,
    "get_mouse_position": get_mouse_position,
    "type_text": type_text,
    "press_key": press_key,
    "hotkey": hotkey,
    "list_windows": list_windows,
    "activate_window": activate_window,
    "find_on_screen": find_on_screen,
    "click_on_image": click_on_image,
    "google_search": google_search,
    "youtube_search": youtube_search,
    "wikipedia_search": wikipedia_search,
    "github_search": github_search,
    "stackoverflow_search": stackoverflow_search,
    "reddit_search": reddit_search,
    "maps_search": maps_search,
    "translate_text": translate_text,
    "discord_open": discord_open,
    "discord_send": discord_send,
    "spotify_play": spotify_play,
    "twitch_search": twitch_search,
}


def execute_tool(name: str, arguments: dict) -> dict:
    from pydantic import ValidationError
    from core.validators import TOOL_SCHEMAS

    func = TOOL_REGISTRY.get(name)
    if not func:
        return {"success": False, "error": f"Unknown tool: {name}"}

    if not isinstance(arguments, dict):
        return {
            "success": False,
            "error": f"Аргументы должны быть объектом, получено {type(arguments).__name__}",
        }

    schema = TOOL_SCHEMAS.get(name)
    if schema:
        try:
            validated = schema(**arguments)
            arguments = validated.model_dump()
        except ValidationError as e:
            errors = [f"  • {'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
            return {
                "success": False,
                "error": f"Ошибка валидации '{name}':\n" + "\n".join(errors),
                "hint": "Исправь аргументы и вызови снова.",
            }

    try:
        return func(**arguments)
    except TypeError as e:
        return {"success": False, "error": f"Неверные аргументы: {e}"}
    except Exception as e:
        logger.error(f"Tool '{name}' failed: {e}")
        return {"success": False, "error": f"Tool failed: {e}"}


chat_history: list = [{"role": "system", "content": SYSTEM_PROMPT}]


def clear_chat_history():
    global chat_history
    with _brain_lock:
        chat_history.clear()
        chat_history.append({"role": "system", "content": SYSTEM_PROMPT})


def _parse_thoughts(raw: str):
    if not raw:
        return "", ""
    thoughts = ""
    match = re.search(r"<think>(.*?)</think>", raw, flags=re.DOTALL)
    if match:
        thoughts = match.group(1).strip()
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    return raw, thoughts


def _fix_code_fences(text: str) -> str:
    if not text:
        return text

    text = re.sub(
        r"^python\s+((?:import |from |def |class |async def )[^\n]+)",
        r"```python\n\1",
        text,
        flags=re.MULTILINE,
    )

    if text.count("```") % 2 == 1:
        text = text.rstrip() + "\n```"

    if "```" in text:
        first_fence = text.find("```")
        before = text[:first_fence]

        if before.strip():
            lines = before.split("\n")
            code_start_idx = None

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith(("def ", "import ", "class ", "from ", "async def ", "@")):
                    code_start_idx = i
                    break

            if code_start_idx is not None:
                pre_text = "\n".join(lines[:code_start_idx]).rstrip()
                code_part = "\n".join(lines[code_start_idx:]).rstrip()

                if pre_text:
                    new_block = f"{pre_text}\n\n```python\n{code_part}\n```\n"
                else:
                    new_block = f"```python\n{code_part}\n```\n"

                rest = text[first_fence + 3:]
                text = new_block + rest

    return text


def _get_memory_context() -> str:
    try:
        facts = recall_memory()
        if facts.get("success") and facts.get("all_memories"):
            items = list(facts["all_memories"].items())[:MAX_FACTS_IN_PROMPT]
            lines = [f"- {k}: {v}" for k, v in items]
            if lines:
                return "**Известные факты о пользователе:**\n" + "\n".join(lines)
    except Exception as e:
        logger.error(f"Recall facts failed: {e}")
    return ""


def _get_role(m):
    if isinstance(m, dict):
        return m.get("role")
    return getattr(m, "role", None)


def _build_messages(agent: AgentConfig) -> list:
    from core.settings import get_setting

    system_msg = {"role": "system", "content": agent.system_prompt}
    lang = get_setting("lang", "ru")

    lang_instructions = {
        "en": "Always respond in ENGLISH, regardless of the language of tools. Keep Vanta's tone: friendly, concise, human-like.",
        "uk": "Завжди відповідай УКРАЇНСЬКОЮ мовою, навіть якщо інструменти повернули дані англійською. Зберігай тон Vanta: дружній, лаконічний.",
        "pl": "Zawsze odpowiadaj po POLSKU, nawet jeśli narzędzia zwróciły dane po angielsku. Zachowaj ton Vanta: przyjazny, zwięzły.",
        "ru": "Всегда отвечай на РУССКОМ языке, даже если инструменты вернули данные на английском. Сохраняй тон Vanta: дружелюбный, лаконичный.",
    }
    system_msg["content"] += f"\n\n## RESPONSE LANGUAGE\n{lang_instructions.get(lang, lang_instructions['ru'])}"

    memory = _get_memory_context()
    if memory:
        system_msg["content"] += f"\n\n## ПАМЯТЬ О ПОЛЬЗОВАТЕЛЕ\n{memory}"

    with _brain_lock:
        history = list(chat_history[1:])

    sliced = history[-MAX_HISTORY:]
    while sliced and _get_role(sliced[0]) == "tool":
        sliced = sliced[1:]

    return [system_msg] + sliced


def _call_api(messages: list, agent: AgentConfig):
    from core.api_client import chat_api
    agent_tools = filter_tools_for_agent(agent, TOOLS)
    console.print(f"[dim cyan]→ OpenAI [{agent.name}] (tools: {len(agent_tools)})[/dim cyan]")
    result = chat_api(messages=messages, tools=agent_tools if agent_tools else None)
    return _wrap_api_response(result)


def _cleanup_screenshots(paths: list):
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def _error_response(text: str) -> dict:
    return {"display": text, "speech": text, "thoughts": ""}


def ask_ai_stream(message: str, agent_id: str = "default"):
    agent = get_agent(agent_id)
    with _brain_lock:
        chat_history.append({"role": "user", "content": message})

    start = time.time()
    screenshots = []
    api_notice_shown = False
    total_usage = {"prompt": 0, "cached": 0, "completion": 0, "total": 0, "cost": 0.0}

    try:
        for step in range(1, MAX_STEPS + 1):
            if time.time() - start > MAX_SECONDS:
                yield {
                    "type": "done",
                    "display": f"Превышено время ({MAX_SECONDS} сек).",
                    "thoughts": "",
                    "usage": total_usage,
                }
                return

            messages = _build_messages(agent)

            if not api_notice_shown:
                yield {"type": "answer", "text": f"🌐 OpenAI [{agent.name}]...\n\n"}
                api_notice_shown = True

            try:
                response = _call_api(messages, agent)
            except Exception as e:
                logger.error(f"API error: {e}")
                yield {
                    "type": "done",
                    "display": f"Ошибка API: {e}",
                    "thoughts": "",
                    "usage": total_usage,
                }
                return

            if getattr(response, "usage", None):
                for k in ("prompt", "cached", "completion", "total"):
                    total_usage[k] += response.usage.get(k, 0)
                total_usage["cost"] = round(
                    total_usage["cost"] + response.usage.get("cost", 0), 6
                )

            full_content = response.message.content or ""

            if not response.message.tool_calls:
                display, thoughts = _parse_thoughts(full_content)
                display = _fix_code_fences(display)

                if not display.strip():
                    display = "✔ Готово."

                with _brain_lock:
                    chat_history.append({
                        "role": "assistant",
                        "content": display,
                        "thoughts": thoughts,
                        "usage": total_usage,
                    })

                yield {"type": "answer", "text": display}
                yield {
                    "type": "done",
                    "display": display,
                    "thoughts": thoughts,
                    "usage": total_usage,
                }
                return

            formatted = []
            for idx, tc in enumerate(response.message.tool_calls):
                formatted.append({
                    "id": tc.id or f"call_{idx}_{int(time.time()*1000)}",
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

            with _brain_lock:
                chat_history.append({
                    "role": "assistant",
                    "content": full_content or "",
                    "tool_calls": formatted,
                })

            for tc in formatted:
                name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                tc_id = tc["id"]

                try:
                    console.print(f"\n[bold yellow]⚡[/bold yellow] [bold white]{name}[/bold white]")
                except Exception:
                    pass

                yield {"type": "tool_call", "name": name, "args": args}

                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError as e:
                        result = {"success": False, "error": f"Invalid JSON: {e}"}
                        with _brain_lock:
                            chat_history.append({
                                "role": "tool",
                                "tool_call_id": tc_id,
                                "content": json.dumps(result, ensure_ascii=False),
                            })
                        yield {"type": "tool_result", "name": name, "result": result}
                        continue

                try:
                    result = execute_tool(name, args)
                except Exception as e:
                    logger.error(f"Tool {name} critical error: {e}")
                    result = {"success": False, "error": f"Критическая ошибка: {e}"}

                try:
                    console.print(f"[bold green]✔[/bold green] [dim]{str(result)[:200]}[/dim]")
                except Exception:
                    pass

                yield {"type": "tool_result", "name": name, "result": result}

                if isinstance(result, dict) and result.get("image_path"):
                    screenshots.append(result["image_path"])

                with _brain_lock:
                    chat_history.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": json.dumps(result, ensure_ascii=False),
                    })

        yield {
            "type": "done",
            "display": "Слишком много шагов.",
            "thoughts": "",
            "usage": total_usage,
        }

    finally:
        _cleanup_screenshots(screenshots)


def ask_ai(message: str, agent_id: str = "default") -> dict:
    final_event = None
    for event in ask_ai_stream(message, agent_id=agent_id):
        if event.get("type") == "done":
            final_event = event

    if not final_event:
        return _error_response("Не удалось получить ответ.")

    display = final_event.get("display", "")
    return {
        "display": display,
        "speech": display,
        "thoughts": final_event.get("thoughts", ""),
        "usage": final_event.get("usage"),
    }