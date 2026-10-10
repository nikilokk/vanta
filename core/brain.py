# core/brain.py
import json
import os
import re
from datetime import datetime

from rich.console import Console
from ollama import chat

from pydantic import ValidationError
from core.validators import TOOL_SCHEMAS

from core.logger import get_logger
from core.memory import forget_memory, recall_memory, save_memory
from core.prompts import SYSTEM_PROMPT
from core.schemas import TOOLS
from core.vector_memory import (
    save_conversation, search_conversations, get_stats
)
from config import MODEL, VISION_MODEL

from tools import (
    web_search, get_current_datetime, open_website, open_program,
    get_system_info, get_gpu_info, get_running_processes, close_program,
    get_uptime, get_clipboard, set_clipboard, set_volume, toggle_mute,
    take_screenshot, analyze_codebase, add_interval_task,
    list_scheduled_tasks, remove_scheduled_task, search_username_osint,
    list_sandbox_files, read_sandbox_file, write_sandbox_file,
    generate_code_local, search_files, read_file, write_file,
    edit_file, run_command,
    move_mouse, click_mouse, double_click, right_click,
    drag_mouse, scroll_mouse, get_mouse_position,
    type_text, press_key, hotkey,
    list_windows, activate_window,
    find_on_screen, click_on_image
)

logger = get_logger(__name__)
console = Console()


# === ОБЁРТКИ ДЛЯ ВЕКТОРНОЙ ПАМЯТИ ===
def _remember_conversation(summary: str):
    """Обёртка: сохраняет summary как диалог."""
    return save_conversation(user_message=summary, assistant_response="(запомнено)")


def _search_memory(query: str):
    """Обёртка: ищет в векторной памяти."""
    result = search_conversations(query, n_results=3)
    if not result["success"]:
        return result
    if not result["results"]:
        return {"success": True, "message": "Ничего не найдено по этому запросу."}

    formatted = []
    for r in result["results"]:
        formatted.append(f"[{r['timestamp'][:16]}] {r['text']}")
    return {"success": True, "memories": "\n\n".join(formatted)}


# === РЕЕСТР ИНСТРУМЕНТОВ ===
TOOL_REGISTRY = {
    "web_search": web_search,
    "get_current_datetime": get_current_datetime,
    "open_website": open_website,
    "open_program": open_program,
    "get_system_info": get_system_info,
    "get_gpu_info": get_gpu_info,
    "get_running_processes": get_running_processes,
    "close_program": close_program,
    "search_files": search_files,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "run_command": run_command,
    "get_uptime": get_uptime,
    "get_clipboard": get_clipboard,
    "set_clipboard": set_clipboard,
    "set_volume": set_volume,
    "toggle_mute": toggle_mute,
    "save_memory": save_memory,
    "recall_memory": recall_memory,
    "forget_memory": forget_memory,
    "take_screenshot": take_screenshot,
    "analyze_codebase": analyze_codebase,
    "add_interval_task": add_interval_task,
    "list_scheduled_tasks": list_scheduled_tasks,
    "remove_scheduled_task": remove_scheduled_task,
    "search_username_osint": search_username_osint,
    "list_sandbox_files": list_sandbox_files,
    "read_sandbox_file": read_sandbox_file,
    "write_sandbox_file": write_sandbox_file,
    "generate_code_local": generate_code_local,
    "remember_conversation": _remember_conversation,
    "search_memory": _search_memory,
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
}


def execute_tool(name: str, arguments: dict):
    """
    Универсальный вызов инструмента с валидацией аргументов через Pydantic.
    Если аргументы неверные — возвращаем понятную ошибку модели,
    чтобы она могла исправиться и вызвать инструмент заново.
    """
    # 1. Проверяем, что инструмент существует
    func = TOOL_REGISTRY.get(name)
    if not func:
        return {"success": False, "error": f"Unknown tool: {name}"}

    # 2. Валидируем аргументы, если для инструмента есть схема
    schema = TOOL_SCHEMAS.get(name)
    if schema is not None:
        if not isinstance(arguments, dict):
            return {
                "success": False,
                "error": f"Аргументы должны быть объектом, получено: {type(arguments).__name__}",
                "hint": "Передавай аргументы как JSON-объект: {\"key\": \"value\"}"
            }
        try:
            validated = schema(**arguments)
            arguments = validated.model_dump()  # обратно в dict, но чистый
        except ValidationError as e:
            # Формируем человекочитаемые ошибки
            errors = []
            for err in e.errors():
                field = ".".join(str(x) for x in err["loc"])
                msg = err["msg"]
                errors.append(f"  • {field}: {msg}")

            return {
                "success": False,
                "error": f"Ошибка валидации аргументов для '{name}':\n" + "\n".join(errors),
                "hint": "Исправь аргументы и вызови инструмент снова.",
                "received": arguments,
            }
    # Если схемы нет — пропускаем как есть (старые инструменты без валидации)

    # 3. Вызываем функцию
    try:
        return func(**arguments)
    except TypeError as e:
        # Если модель передала лишние/недостающие аргументы
        return {
            "success": False,
            "error": f"Неверные аргументы функции: {e}",
            "hint": "Проверь названия и количество аргументов."
        }
    except Exception as e:
        return {"success": False, "error": f"Tool execution failed: {e}"}


# === ИСТОРИЯ ДИАЛОГА ===
chat_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


def clear_chat_history():
    """Очищает кратковременную память."""
    global chat_history
    chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]


def _parse_final_response(raw: str):
    """Просто возвращает чистый текст без JSON-парсинга."""
    if not raw:
        return "", ""
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    return raw, raw


def _auto_save(user_message: str, assistant_response: str):
    """Автосохранение пары запрос-ответ в векторную память."""
    # Не сохраняем пустое или слишком короткое
    if not user_message or len(user_message.strip()) < 5:
        return

    try:
        result = save_conversation(
            user_message=user_message,
            assistant_response=assistant_response,
        )
        if result.get("success"):
            logger.info(f"VectorMemory: автосохранён диалог {result.get('id')}")
        else:
            logger.warning(f"VectorMemory: не сохранено — {result.get('error')}")
    except Exception as e:
        logger.error(f"VectorMemory auto-save failed: {e}")


def ask_ai(message):
    global chat_history
    chat_history.append({"role": "user", "content": message})

    MAX_STEPS = 30
    step = 0
    screenshots_to_cleanup = []

    try:
        while True:
            step += 1
            if step > MAX_STEPS:
                return {"display": "Я остановилась после лимита действий.",
                        "speech": "Я остановилась после лимита действий."}

            try:
                trimmed_messages = [chat_history[0]] + chat_history[-20:]
                has_images = any("images" in m for m in trimmed_messages)
                current_model = VISION_MODEL if has_images else MODEL

                response = chat(
                    model=current_model,
                    messages=trimmed_messages,
                    tools=TOOLS,
                    keep_alive=-1,
                    options={
                        "num_ctx": 16384,
                        "temperature": 0.85,
                        "top_p": 0.95,
                        "repeat_penalty": 1.1,
                        "presence_penalty": 0.3,
                    }
                )
            except Exception as e:
                err = f"Ошибка при обращении к модели: {e}"
                return {"display": err, "speech": err}

            chat_history.append(response.message)

            # === ФИНАЛЬНЫЙ ОТВЕТ (нет tool_calls) ===
            if not response.message.tool_calls:
                raw = (response.message.content or "").strip()
                display, speech = _parse_final_response(raw)

                # === АВТОСОХРАНЕНИЕ В ВЕКТОРНУЮ ПАМЯТЬ ===
                _auto_save(message, display)
                # =========================================

                return {"display": display, "speech": speech}

            # === ОБРАБОТКА ВЫЗОВОВ ИНСТРУМЕНТОВ ===
            for tool_call in response.message.tool_calls:
                name = tool_call.function.name
                arguments = tool_call.function.arguments

                console.print(
                    f"\n[bold yellow]⚡ [TOOL CALL]:[/bold yellow] "
                    f"[bold white]{name}[/bold white] [dim]args: {arguments}[/dim]"
                )

                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError as e:
                        result = {"success": False, "error": f"Invalid JSON: {e}"}
                        chat_history.append({
                            "role": "tool",
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                        continue

                result = execute_tool(name, arguments)

                console.print(f"[bold green]✔ [RESULT]:[/bold green] [dim]{result}[/dim]")

                tool_message = {
                    "role": "tool",
                    "content": json.dumps(result, ensure_ascii=False)
                }

                if name == "take_screenshot" and isinstance(result, dict) and result.get("success"):
                    img_path = result.get("image_path")
                    if img_path:
                        tool_message["images"] = [img_path]
                        screenshots_to_cleanup.append(img_path)

                chat_history.append(tool_message)

            # Возвращаемся на новый круг while — модель сформулирует финал

    finally:
        for img_path in screenshots_to_cleanup:
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception:
                    pass