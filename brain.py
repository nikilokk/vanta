import json
from datetime import datetime

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

ГЛАВНОЕ ПРАВИЛО:
- Если пользователь просит выполнить действие (изменить файл, запустить программу, найти информацию), ТЫ ОБЯЗАН СРАЗУ ВЫЗВАТЬ СООТВЕТСТВУЮЩИЙ ИНСТРУМЕНТ (tool_call).
- Не объясняй, как выполнить задачу, и не описывай доступные функции.
- Не пиши вводный текст перед вызовом инструмента. Сначала вызывай инструмент, а итоговый ответ давай только после получения результатов.
- Для изменения файлов проекта сначала прочитай файл через read_file, затем внеси изменения через edit_file.
"""

MODEL = "qwen3:8b"

TOOLS = [
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

    return {"error": f"Unknown tool: {name}"}


def ask_ai(message):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    MAX_STEPS = 30
    step = 0
    DANGEROUS_TOOLS = {"run_command", "write_file", "edit_file", "close_program"}

    while True:
        step += 1

        if step > MAX_STEPS:
            return "Я остановила выполнение после достижения лимита действий."

        try:
            response = chat(
                model=MODEL,
                messages=messages,
                tools=TOOLS,
            )
        except Exception as e:
            return f"Ошибка при обращении к модели: {e}"

        messages.append(response.message)

        if not response.message.tool_calls:
            return response.message.content

        for tool_call in response.message.tool_calls:
            name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(f"\n[TOOL] {name}({arguments})")

            # Валидация аргументов
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError as e:
                    result = {"success": False, "error": f"Invalid tool arguments JSON: {e}"}
                    print(f"[RESULT] {result}")
                    messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})
                    continue
            elif not isinstance(arguments, dict):
                result = {"success": False, "error": "Tool arguments must be a dictionary or JSON object."}
                print(f"[RESULT] {result}")
                messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})
                continue

            # ИСПРАВЛЕННАЯ ПРОВЕРКА ОПАСНЫХ ОПЕРАЦИЙ (без лишнего вложенного цикла)
            if name in DANGEROUS_TOOLS:
                print(f"\n⚠️  [ВНИМАНИЕ] ИИ хочет выполнить: {name}({arguments})")
                confirm = input("Разрешить? [y/N]: ").strip().lower()
                if confirm not in {"y", "yes", "да", "д"}:
                    result = {"success": False, "error": "Пользователь отклонил выполнение операции."}
                    print(f"[RESULT] {result}")
                    messages.append({"role": "tool", "content": json.dumps(result, ensure_ascii=False)})
                    continue  # Пропускаем выполнение execute_tool для ЭТОЙ команды

            # Выполнение инструмента
            try:
                result = execute_tool(name, arguments)
            except Exception as e:
                result = {"success": False, "error": f"Tool execution failed: {e}"}

            print(f"[RESULT] {result}")

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

            messages.append({"role": "tool", "content": tool_content})