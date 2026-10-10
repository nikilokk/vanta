# core/schemas.py

TOOLS = [
    # === ФАЙЛОВЫЕ ОПЕРАЦИИ ===
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Читает текстовый файл внутри проекта Vanta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Путь к файлу относительно проекта."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Создаёт НОВЫЙ текстовый файл внутри проекта Vanta. НЕ используй для изменения существующих файлов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Путь к файлу."},
                    "content": {"type": "string", "description": "Полное содержимое файла."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Точечно изменяет существующий файл. Сначала прочитай файл через read_file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Путь к файлу."},
                    "old_text": {"type": "string", "description": "Точный фрагмент для замены."},
                    "new_text": {"type": "string", "description": "Новый текст."}
                },
                "required": ["path", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Ищет файлы в проекте Vanta по имени.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Часть имени файла."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Запускает разрешённую команду (python, pip, git, pytest).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Команда для выполнения."}
                },
                "required": ["command"]
            }
        }
    },

    # === СИСТЕМНЫЕ ФУНКЦИИ ===
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Получает информацию о CPU, RAM и дисках.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_gpu_info",
            "description": "Информация о видеокарте NVIDIA.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_running_processes",
            "description": "Список наиболее загруженных процессов.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_program",
            "description": "Закрывает программу Windows по имени.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program": {"type": "string", "description": "Название программы."}
                },
                "required": ["program"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_uptime",
            "description": "Время работы компьютера с момента загрузки.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Скриншот текущего экрана для анализа.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Читает текст из буфера обмена.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_clipboard",
            "description": "Копирует текст в буфер обмена.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Текст для копирования."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Устанавливает громкость (0-100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Громкость 0-100."}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "toggle_mute",
            "description": "Переключает mute аудио.",
            "parameters": {"type": "object", "properties": {}}
        }
    },

    # === ПРОГРАММЫ И САЙТЫ ===
    {
        "type": "function",
        "function": {
            "name": "open_program",
            "description": "Ищет и запускает программу Windows или открывает URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "program": {"type": "string", "description": "Название программы или URL."}
                },
                "required": ["program"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_website",
            "description": "Открывает веб-сайт в браузере.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Полный URL."}
                },
                "required": ["url"]
            }
        }
    },

    # === ВЕБ И OSINT ===
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Ищет информацию в интернете через DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос (английский для IT-тем)."},
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_username_osint",
            "description": "Ищет ник через Sherlock OSINT по 400+ платформам.",
            "parameters": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Никнейм."}
                },
                "required": ["username"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_datetime",
            "description": "Текущая дата и время компьютера.",
            "parameters": {"type": "object", "properties": {}}
        }
    },

    # === ПАМЯТЬ ===
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Сохраняет факт или предпочтение в долговременную память.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Ключ (например, 'user_name')."},
                    "value": {"type": "string", "description": "Значение."}
                },
                "required": ["key", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "recall_memory",
            "description": "Возвращает факты из памяти. Оставь key пустым, чтобы получить всё.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Опциональный ключ."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forget_memory",
            "description": "Удаляет факт из памяти.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Ключ для удаления."}
                },
                "required": ["key"]
            }
        }
    },

    # === ПЕСОЧНИЦА ===
    {
        "type": "function",
        "function": {
            "name": "list_sandbox_files",
            "description": "Список файлов в песочнице D:\\Vanta_Sandbox.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_sandbox_file",
            "description": "Читает файл из песочницы.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {"type": "string", "description": "Относительный путь."}
                },
                "required": ["relative_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_sandbox_file",
            "description": "Пишет файл в песочницу.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relative_path": {"type": "string", "description": "Относительный путь."},
                    "content": {"type": "string", "description": "Содержимое."}
                },
                "required": ["relative_path", "content"]
            }
        }
    },

    # === АНАЛИЗ И ГЕНЕРАЦИЯ КОДА ===
    {
        "type": "function",
        "function": {
            "name": "analyze_codebase",
            "description": "Анализирует Python-файл (AST, docstrings, unused imports).",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Путь к .py файлу."}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_code_local",
            "description": "Генерирует код через локальную модель qwen2.5-coder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "ТЗ для генерации."},
                    "language": {"type": "string", "description": "Язык программирования."}
                },
                "required": ["prompt"]
            }
        }
    },

    # === ПЛАНИРОВЩИК ===
    {
        "type": "function",
        "function": {
            "name": "add_interval_task",
            "description": "Создаёт задачу, повторяющуюся каждые N минут. Используй 'notification' для простых напоминаний (текст отправляется как есть) и 'ai_task' для задач, где нужно, чтобы Ванта подумала и дала ответ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Имя задачи."},
                    "minutes": {"type": "integer", "description": "Интервал в минутах."},
                    "prompt": {"type": "string", "description": "Текст напоминания (для notification) или запрос (для ai_task)."},
                    "task_type": {
                        "type": "string",
                        "enum": ["notification", "ai_task"],
                        "description": "'notification' — простое напоминание. 'ai_task' — задача для ИИ."
                    }
                },
                "required": ["name", "minutes", "prompt", "task_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_scheduled_tasks",
            "description": "Список активных задач.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_scheduled_task",
            "description": "Удаляет задачу по ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_id": {"type": "string", "description": "ID задачи."}
                },
                "required": ["job_id"]
            }
        }
    },
        # === ВЕКТОРНАЯ ПАМЯТЬ ===
    {
        "type": "function",
        "function": {
            "name": "remember_conversation",
            "description": "Сохраняет текущий диалог в долговременную векторную память. Используй, когда пользователь делится чем-то важным: планами, мыслями, опытом, историями.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "Краткое содержание того, что нужно запомнить (1-2 предложения)."
                    }
                },
                "required": ["summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Ищет в долговременной памяти прошлые разговоры и события по смыслу. Используй, когда пользователь спрашивает 'помнишь...', 'о чём мы говорили...', 'что я рассказывал про...'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос — что именно вспомнить."
                    }
                },
                "required": ["query"]
            }
        }
    },
        # === GUI-АВТОМАТИЗАЦИЯ ===
    {
        "type": "function",
        "function": {
            "name": "move_mouse",
            "description": "Перемещает курсор мыши в точку (x, y) на экране.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X-координата."},
                    "y": {"type": "integer", "description": "Y-координата."},
                    "duration": {"type": "number", "default": 0.3, "description": "Длительность перемещения в секундах."}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_mouse",
            "description": "Кликает мышью. Если x/y не указаны — клик в текущей позиции.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X-координата (опционально)."},
                    "y": {"type": "integer", "description": "Y-координата (опционально)."},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                    "clicks": {"type": "integer", "default": 1}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "double_click",
            "description": "Двойной клик мышью.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "right_click",
            "description": "Правый клик мышью.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "drag_mouse",
            "description": "Перетаскивает: зажать ЛКМ в (x1,y1), тащить в (x2,y2), отпустить.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x1": {"type": "integer"},
                    "y1": {"type": "integer"},
                    "x2": {"type": "integer"},
                    "y2": {"type": "integer"},
                    "duration": {"type": "number", "default": 0.5}
                },
                "required": ["x1", "y1", "x2", "y2"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll_mouse",
            "description": "Прокрутка колесом мыши. amount > 0 — вверх, < 0 — вниз.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "integer", "description": "Величина прокрутки."},
                    "x": {"type": "integer"},
                    "y": {"type": "integer"}
                },
                "required": ["amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_mouse_position",
            "description": "Возвращает текущие координаты курсора мыши.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Печатает текст в активное окно. Поддерживает русский (через буфер обмена).",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Текст для ввода."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Нажимает одну клавишу: 'enter', 'esc', 'tab', 'f5', 'delete' и т.д.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Название клавиши."}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hotkey",
            "description": "Нажимает комбинацию клавиш через '+'. Пример: 'ctrl+c', 'alt+tab', 'ctrl+shift+esc'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {"type": "string", "description": "Комбинация, например 'ctrl+c'."}
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_windows",
            "description": "Возвращает список открытых окон Windows.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "activate_window",
            "description": "Активирует окно по части заголовка (выводит на передний план).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Часть заголовка окна."}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_on_screen",
            "description": "Ищет изображение (PNG) на экране. Возвращает координаты центра, если нашёл.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "Путь к PNG-файлу."},
                    "confidence": {"type": "number", "default": 0.8, "description": "Точность совпадения 0.0-1.0."}
                },
                "required": ["image_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_on_image",
            "description": "Ищет изображение на экране и кликает по его центру.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "Путь к PNG-файлу."},
                    "confidence": {"type": "number", "default": 0.8}
                },
                "required": ["image_path"]
            }
        }
    },
]