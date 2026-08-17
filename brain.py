import json
import os
from datetime import datetime
from memory import forget_memory, recall_memory, save_memory

from rich.console import Console

console = Console()

from ollama import chat
from file_tools import (
    search_files,
    read_file,
    write_file,
    edit_file,
    run_command,
)
from tools import (
    web_search,
    get_current_datetime,
    open_website,
    open_program,
    find_program,
    launch_program,
    get_system_info,
    get_gpu_info,
    get_running_processes,
    close_program,
    get_uptime,
    get_clipboard,
    set_clipboard,
    set_volume,
    toggle_mute,
    take_screenshot,
    analyze_codebase,
)

current_year = datetime.now().year

# ДОБАВЛЕН префикс f перед строкой
SYSTEM_PROMPT = f"""Ты Vanta — локальный AI-ассистент, управляющий компьютером и проектом.

Текущий год: {current_year}.

ПРАВИЛО ПОИСКА:
- Формируй поисковый запрос ДЛЯ ТЕКУЩЕГО ({current_year}) ГОДА.
- НИКОГДА не добавляй слово "2023" или прошлые года в параметр query функции web_search.
- Если нужно узнать актуальную версию чего-либо, ищи без указания года или используй {current_year} год.
- Для поиска программных версий, документации и IT-новостей всегда формулируй query на английском языке (например, "latest python release version").
- Если в результатах поиска нет конкретной цифры или ответа, измени запрос на более точный (например, добавь site:python.org/downloads).

MEMORY INSTRUCTIONS:
- Whenever the user shares personal preferences, facts, or instructions to remember, call 'save_memory'.
- Before answering queries about user preferences or past choices, check 'recall_memory'.

ГЛАВНОЕ ПРАВИЛО:
- Если пользователь просит выполнить действие (изменить файл, запустить программу, найти информацию), ТЫ ОБЯЗАН СРАЗУ ВЫЗВАТЬ СООТВЕТСТВУЮЩИЙ ИНСТРУМЕНТ (tool_call).
- Не объясняй, как выполнить задачу, и не описывай доступные функции.
- Не пиши вводный текст перед вызовом инструмента. Сначала вызывай инструмент, а итоговый ответ давай только после получения результатов.
- Для изменения файлов проекта сначала прочитай файл через read_file, затем внеси изменения через edit_file.
ВАЖНОЕ ПРАВИЛО: Тебе ЗАПРЕЩЕНО перезаписывать файлы проекта (brain.py, tools.py, main.py) целиком через функцию write_file. Для изменения кода предлагай текстовый диф/код пользователю или создавай новые файлы в отдельной папке.
"""

MODEL = "qwen3:8b"

TOOLS = [

    

    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Reads current text from the Windows clipboard.",
            "parameters": {"type": "object", "properties": {}
            }
        }
    },
    
    {
            "type": "function",
            "function": {
                "name": "analyze_codebase",
                "description": "Analyzes a Python file for syntax errors, missing docstrings, function structures, and unused imports.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the .py file to analyze",
                        }
                    },
                    "required": ["file_path"],
                },
            },
        },
    
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Saves a key-value fact or user preference into persistent long-term memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Category or key name (e.g., 'user_name', 'favorite_music', 'preferred_ide')."
                    },
                    "value": {
                        "type": "string",
                        "description": "The fact or detail to remember."
                    }
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "Retrieves saved facts or preferences from long-term memory. Leave key empty to retrieve all memories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Optional specific key to recall."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forget_memory",
            "description": "Deletes a specific fact or key from long-term memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key to remove."
                    }
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Copies specified text to the Windows clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to copy."
                    }
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Takes a screenshot of the current screen to inspect what is shown on the display.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Sets master system volume level in percent (0-100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Volume level percentage (0-100)."
                    }
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_mute",
            "description": "Toggles master audio mute state.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "media_control",
            "description": "Controls system media playback (play_pause, next, prev).",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["play_pause", "next", "prev"],
                        "description": "Media action: play_pause, next, or prev."
                    }
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Открывает веб-сайт на компьютере пользователя.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Полный URL сайта.",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Ищет информацию в интернете через DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Точный поисковый запрос. Для поиска версий ПО и технических данных пиши запрос на английском языке, например: 'Python latest stable release version site:python.org'."
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Возвращает текущую дату и время компьютера.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_uptime",
            "description": "Возвращает время работы компьютера с момента последней загрузки.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Запускает разрешённую команду внутри проекта Vanta и возвращает результат выполнения.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Команда для выполнения, например 'python test_tools.py'."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Точечно изменяет существующий текстовый файл внутри проекта Vanta. Сначала необходимо прочитать файл через read_file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу относительно проекта Vanta."
                    },
                    "old_text": {
                        "type": "string",
                        "description": "Точный фрагмент существующего текста, который нужно заменить."
                    },
                    "new_text": {
                        "type": "string",
                        "description": "Новый текст."
                    }
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Ищет файлы внутри проекта Vanta по имени.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Название или часть названия файла."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Читает текстовый файл внутри проекта Vanta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу относительно проекта Vanta."
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Создаёт новый текстовый файл внутри проекта Vanta. Не используй для изменения существующего файла.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Путь к файлу относительно проекта Vanta."
                    },
                    "content": {
                        "type": "string",
                        "description": "Полное новое содержимое файла."
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_program",
            "description": "Закрывает запущенную программу Windows по её названию.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program": {
                        "type": "string",
                        "description": "Название программы, которую нужно закрыть."
                    }
                },
                "required": ["program"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_running_processes",
            "description": "Получает список наиболее загруженных процессов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 10
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_gpu_info",
            "description": "Получает информацию о видеокарте NVIDIA.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Получает информацию о текущем состоянии компьютера.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "launch_program",
            "description": "Находит и запускает установленную программу Windows.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program": {
                        "type": "string",
                        "description": "Название программы."
                    }
                },
                "required": ["program"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_program",
            "description": "Ищет установленную программу на компьютере.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program": {
                        "type": "string",
                        "description": "Название программы."
                    }
                },
                "required": ["program"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_program",
            "description": "Запускает программу по имени или команде.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program": {
                        "type": "string",
                        "description": "Имя программы или команда."
                    }
                },
                "required": ["program"]
            }
        }
    },
]


def execute_tool(name, arguments):
    if name == "web_search":
        return web_search(**arguments)
    if name == "get_current_datetime":
        return get_current_datetime()
    if name == "open_website":
        return open_website(**arguments)
    if name == "open_program":
        return open_program(**arguments)
    if name == "find_program":
        return find_program(**arguments)
    if name == "launch_program":
        return launch_program(**arguments)
    if name == "get_system_info":
        return get_system_info()
    if name == "get_gpu_info":
        return get_gpu_info()
    if name == "get_running_processes":
        return get_running_processes(**arguments)
    if name == "close_program":
        return close_program(**arguments)
    if name == "search_files":
        return search_files(**arguments)
    if name == "read_file":
        return read_file(**arguments)
    if name == "write_file":
        return write_file(**arguments)
    if name == "edit_file":
        return edit_file(**arguments)
    if name == "run_command":
        return run_command(**arguments)
    if name == "get_uptime":
        return get_uptime()
    if name == "get_clipboard":
        return get_clipboard()
    if name == "set_clipboard":
        return set_clipboard(**arguments)
    if name == "set_volume":
        return set_volume(**arguments)
    if name == "toggle_mute":
        return toggle_mute()
    if name == "save_memory":
        return save_memory(**arguments)
    if name == "recall_memory":
        return recall_memory(**arguments)
    if name == "forget_memory":
        return forget_memory(**arguments)
    if name == "take_screenshot":
        return take_screenshot()
    if name == "analyze_codebase":
            return analyze_codebase()

    return {"error": f"Unknown tool: {name}"}


def ask_ai(message):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    MAX_STEPS = 30
    step = 0
    DANGEROUS_TOOLS = {"run_command", "write_file", "edit_file", "close_program"}
    screenshots_to_cleanup = []

    try:
        while True:
            step += 1

            if step > MAX_STEPS:
                return "Я остановила выполнение после достижения лимита действий."

            try:
                # Если в истории сообщений есть изображения, используем Vision-модель, иначе — обычную
                has_images = any("images" in m for m in messages)
                current_model = "qwen3-vl:8b " if has_images else MODEL

                response = chat(
                    model=current_model,
                    messages=messages,
                    tools=TOOLS,
                    keep_alive=-1,
                    options={"num_ctx": 16384},
                )
            except Exception as e:
                return f"Ошибка при обращении к модели: {e}"

            messages.append(response.message)

            if not response.message.tool_calls:
                return response.message.content

            for tool_call in response.message.tool_calls:
                name = tool_call.function.name
                arguments = tool_call.function.arguments

                console.print(
                    f"\n[bold yellow]⚡ [TOOL CALL]:[/bold yellow] [bold white]{name}[/bold white] [dim]args: {arguments}[/dim]"
                )

                # Валидация аргументов
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError as e:
                        result = {
                            "success": False,
                            "error": f"Invalid tool arguments JSON: {e}",
                        }
                        console.print(
                            f"[bold green]✔ [RESULT]:[/bold green] [dim]{result}[/dim]"
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "content": json.dumps(
                                    result, ensure_ascii=False
                                ),
                            }
                        )
                        continue
                elif not isinstance(arguments, dict):
                    result = {
                        "success": False,
                        "error": "Tool arguments must be a dictionary or JSON object.",
                    }
                    console.print(
                        f"[bold green]✔ [RESULT]:[/bold green] [dim]{result}[/dim]"
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )
                    continue

                # Проверка опасных операций
                if name in DANGEROUS_TOOLS:
                    console.print(
                        f"\n[bold red]⚠️  [WARNING] Action required for:[/bold red] [bold white]{name}[/bold white]"
                    )
                    confirm = (
                        console.input(
                            "[yellow]Allow execution? [y/N]: [/yellow]"
                        )
                        .strip()
                        .lower()
                    )
                    if confirm not in {"y", "yes"}:
                        result = {
                            "success": False,
                            "error": "Operation rejected by user.",
                        }
                        console.print(
                            f"[bold red]❌ [RESULT]:[/bold red] [dim]{result}[/dim]"
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "content": json.dumps(
                                    result, ensure_ascii=False
                                ),
                            }
                        )
                        continue

                # Выполнение инструмента
                try:
                    result = execute_tool(name, arguments)
                except Exception as e:
                    result = {
                        "success": False,
                        "error": f"Tool execution failed: {e}",
                    }

                console.print(
                    f"[bold green]✔ [RESULT]:[/bold green] [dim]{result}[/dim]"
                )

                # Сериализация результата
                try:
                    tool_content = json.dumps(result, ensure_ascii=False)
                except TypeError:
                    tool_content = json.dumps(
                        {
                            "success": False,
                            "error": "Tool returned a value that could not be serialized.",
                            "raw_result": str(result),
                        },
                        ensure_ascii=False,
                    )

                tool_message = {
                    "role": "tool",
                    "content": tool_content,
                }

                # Если сделан скриншот — добавляем картинку в сообщение и в список на авто-удаление
                if (
                    name == "take_screenshot"
                    and isinstance(result, dict)
                    and result.get("success")
                ):
                    img_path = result.get("image_path")
                    if img_path:
                        tool_message["images"] = [img_path]
                        screenshots_to_cleanup.append(img_path)

                messages.append(tool_message)

    finally:
        # Очистка всех созданных за этот запрос скриншотов
        for img_path in screenshots_to_cleanup:
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception:
                    pass