# core/brain.py
"""
Ядро Vanta. Вся логика общения с LLM через OpenAI API.
"""
import json
import os
import re
import time

from rich.console import Console

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

logger = get_logger(__name__)
console = Console()


# ═══════════════════════════════════════════════════════════════
# КОНСТАНТЫ
# ═══════════════════════════════════════════════════════════════
MAX_STEPS = 20
MAX_SECONDS = 300
MAX_HISTORY = 15


# ═══════════════════════════════════════════════════════════════
# ОБЁРТКИ ДЛЯ API-ОТВЕТОВ
# ═══════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════
# ВЕКТОРНАЯ ПАМЯТЬ (обёртки)
# ═══════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════
# РЕЕСТР ИНСТРУМЕНТОВ
# ═══════════════════════════════════════════════════════════════
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

    schema = TOOL_SCHEMAS.get(name)
    if schema:
        if not isinstance(arguments, dict):
            return {
                "success": False,
                "error": f"Аргументы должны быть объектом, получено {type(arguments).__name__}",
            }
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
        return {"success": False, "error": f"Tool failed: {e}"}


# ═══════════════════════════════════════════════════════════════
# ИСТОРИЯ
# ═══════════════════════════════════════════════════════════════
chat_history: list = [{"role": "system", "content": SYSTEM_PROMPT}]


def clear_chat_history():
    global chat_history
    chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]


# ═══════════════════════════════════════════════════════════════
# ПОСТ-ОБРАБОТКА ОТВЕТА
# ═══════════════════════════════════════════════════════════════
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
    """
    Пост-обработка ответа: чинит сломанные code fences.

    1. Если `​`` открыт, но не закрыт — добавляет закрывающий.
    2. Если перед первым `​`` есть голый код (def/import/class/from) —
       заворачивает его в блок.
    3. Обрабатывает случай "python import ..." без открывающих `​``.
    """
    if not text:
        return text

    # ── Случай 1: "python\nimport ..." без открывающего fence ──
    # Модель иногда пишет "python" как префикс вместо ​```python
    text = re.sub(
        r"^python\s+((?:import |from |def |class |async def )[^\n]+)",
        r"```python\n\1",
        text,
        flags=re.MULTILINE,
    )

    # ── Случай 2: Баланс закрывающих ──
    # Если ``` нечётное количество — добавляем закрывающий в конец
    if text.count("```") % 2 == 1:
        text = text.rstrip() + "\n```"

    # ── Случай 3: голый код ПЕРЕД первым fence ──
    if "```" in text:
        first_fence = text.find("```")
        before = text[:first_fence]

        if before.strip():
            lines = before.split("\n")
            code_start_idx = None

            for i, line in enumerate(lines):
                stripped = line.strip()
                if stripped.startswith((
                    "def ", "import ", "class ", "from ",
                    "async def ", "@",
                )):
                    code_start_idx = i
                    break

            if code_start_idx is not None:
                pre_text = "\n".join(lines[:code_start_idx]).rstrip()
                code_part = "\n".join(lines[code_start_idx:]).rstrip()

                if pre_text:
                    new_block = f"{pre_text}\n\n```python\n{code_part}\n```\n"
                else:
                    new_block = f"```python\n{code_part}\n```\n"

                # Собираем заново: новый блок + оставшийся текст
                rest = text[first_fence + 3:]
                # Если в rest сразу идёт язык (python, bash и т.д.) — 
                # мы его "съели" при первом find, теперь склеиваем корректно
                text = new_block + rest

    return text


def _get_memory_context(user_message: str) -> str:
    parts = []
    try:
        facts = recall_memory()
        if facts.get("success") and facts.get("all_memories"):
            lines = [f"- {k}: {v}" for k, v in facts["all_memories"].items()]
            if lines:
                parts.append("**Факты:**\n" + "\n".join(lines))
    except Exception as e:
        logger.error(f"Recall facts failed: {e}")

    if user_message and len(user_message.strip()) > 10:
        try:
            result = search_conversations(user_message, n_results=2)
            if result.get("success") and result.get("results"):
                lines = [f"- {r['text'][:400]}" for r in result["results"]]
                if lines:
                    parts.append("**Похожие разговоры:**\n" + "\n".join(lines))
        except Exception as e:
            logger.error(f"Recall dialogs failed: {e}")

    return "\n\n".join(parts)


def _build_messages(user_message: str) -> list:
    system_msg = {"role": "system", "content": SYSTEM_PROMPT}

    memory = _get_memory_context(user_message)
    if memory:
        system_msg["content"] += f"\n\n## ЧТО ТЫ ЗНАЕШЬ О ПОЛЬЗОВАТЕЛЕ\n{memory}"

    return [system_msg] + chat_history[1:][-MAX_HISTORY:]


def _auto_save(message: str, response: str):
    if not message or len(message.strip()) < 5:
        return
    try:
        save_conversation(user_message=message, assistant_response=response)
    except Exception as e:
        logger.error(f"Auto-save failed: {e}")


# ═══════════════════════════════════════════════════════════════
# ВЫЗОВ API
# ═══════════════════════════════════════════════════════════════
def _call_api(messages: list):
    from core.api_client import chat_api
    console.print("[dim cyan]→ OpenAI[/dim cyan]")
    result = chat_api(messages=messages, tools=TOOLS)
    return _wrap_api_response(result)


# ═══════════════════════════════════════════════════════════════
# ОБРАБОТКА TOOL CALLS
# ═══════════════════════════════════════════════════════════════
def _run_tool_calls(tool_calls, screenshots_to_cleanup: list) -> list:
    tool_messages = []

    for idx, tc in enumerate(tool_calls):
        name = tc.function.name
        args = tc.function.arguments
        tc_id = getattr(tc, "id", None) or f"call_{idx}_{int(time.time() * 1000)}"

        try:
            console.print(f"\n[bold yellow]⚡[/bold yellow] [bold white]{name}[/bold white]")
        except Exception:
            pass

        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError as e:
                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": json.dumps(
                        {"success": False, "error": f"Invalid JSON: {e}"},
                        ensure_ascii=False,
                    ),
                })
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

        if name in ("take_screenshot", "analyze_screenshot"):
            if isinstance(result, dict) and result.get("success"):
                img = result.get("image_path")
                if img:
                    screenshots_to_cleanup.append(img)

        tool_messages.append({
            "role": "tool",
            "tool_call_id": tc_id,
            "content": json.dumps(result, ensure_ascii=False),
        })

    return tool_messages


def _cleanup_screenshots(paths: list):
    for p in paths:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def _error_response(text: str) -> dict:
    return {"display": text, "speech": text, "thoughts": ""}


# ═══════════════════════════════════════════════════════════════
# ask_ai (CLI)
# ═══════════════════════════════════════════════════════════════
def ask_ai(message: str) -> dict:
    global chat_history
    chat_history.append({"role": "user", "content": message})

    start = time.time()
    screenshots = []

    try:
        for step in range(1, MAX_STEPS + 1):
            if time.time() - start > MAX_SECONDS:
                return _error_response(f"Превышено время ({MAX_SECONDS} сек).")

            messages = _build_messages(message)

            try:
                response = _call_api(messages)
            except Exception as e:
                return _error_response(f"Ошибка API: {e}")

            if not response.message.tool_calls:
                raw = (response.message.content or "").strip()
                display, thoughts = _parse_thoughts(raw)

                # Автопочинка code fences
                display = _fix_code_fences(display)

                if not display.strip():
                    display = "✔ Готово."

                chat_history.append({
                    "role": "assistant",
                    "content": display,
                    "thoughts": thoughts,
                    "usage": response.usage,
                })
                _auto_save(message, display)
                return {
                    "display": display,
                    "speech": display,
                    "thoughts": thoughts,
                    "usage": response.usage,
                }

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

            chat_history.append({
                "role": "assistant",
                "content": response.message.content or "",
                "tool_calls": formatted,
            })

            tool_msgs = _run_tool_calls(response.message.tool_calls, screenshots)
            chat_history.extend(tool_msgs)

        return _error_response("Слишком много шагов.")

    finally:
        _cleanup_screenshots(screenshots)


# ═══════════════════════════════════════════════════════════════
# ask_ai_stream (дашборд)
# ═══════════════════════════════════════════════════════════════
def ask_ai_stream(message: str):
    global chat_history
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

            messages = _build_messages(message)

            if not api_notice_shown:
                yield {"type": "answer", "text": "🌐 OpenAI...\n\n"}
                api_notice_shown = True

            try:
                response = _call_api(messages)
            except Exception as e:
                logger.error(f"API error: {e}")
                yield {
                    "type": "done",
                    "display": f"Ошибка API: {e}",
                    "thoughts": "",
                    "usage": total_usage,
                }
                return

            # Накопление usage
            if getattr(response, "usage", None):
                for k in ("prompt", "cached", "completion", "total"):
                    total_usage[k] += response.usage.get(k, 0)
                total_usage["cost"] = round(
                    total_usage["cost"] + response.usage.get("cost", 0), 6
                )

            full_content = response.message.content or ""

            # Финальный ответ
            if not response.message.tool_calls:
                display, thoughts = _parse_thoughts(full_content)

                # Автопочинка code fences
                display = _fix_code_fences(display)

                if not display.strip():
                    display = "✔ Готово."

                chat_history.append({
                    "role": "assistant",
                    "content": display,
                    "thoughts": thoughts,
                    "usage": total_usage,
                })
                _auto_save(message, display)

                yield {"type": "answer", "text": display}
                yield {
                    "type": "done",
                    "display": display,
                    "thoughts": thoughts,
                    "usage": total_usage,
                }
                return

            # Tool calls
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

            chat_history.append({
                "role": "assistant",
                "content": full_content or "",
                "tool_calls": formatted,
            })

            for tc in formatted:
                name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                tc_id = tc["id"]

                yield {"type": "tool_call", "name": name, "args": args}

                try:
                    result = execute_tool(name, args)
                except Exception as e:
                    logger.error(f"Tool {name} critical error: {e}")
                    result = {"success": False, "error": f"Критическая ошибка: {e}"}

                yield {"type": "tool_result", "name": name, "result": result}

                if name in ("take_screenshot", "analyze_screenshot"):
                    if isinstance(result, dict) and result.get("success"):
                        img = result.get("image_path")
                        if img:
                            screenshots.append(img)

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