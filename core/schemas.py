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
            "description": "Создаёт НОВЫЙ текстовый файл. НЕ используй для изменения существующих.",
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
            "description": "Точечно изменяет существующий файл. Сначала прочитай через read_file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
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
            "description": "Информация о CPU, RAM и дисках.",
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
                    "program": {"type": "string"}
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
                    "text": {"type": "string"}
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
                    "url": {"type": "string"}
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
            "description": "Ищет информацию в интернете и возвращает ТЕКСТОВЫЕ результаты (сниппеты). Используй для вопросов «узнай», «расскажи», «какая погода», «сколько стоит», «что такое». Ты САМА читаешь результаты и пересказываешь пользователю.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Поисковый запрос (2-4 слова)."},
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
                    "username": {"type": "string"}
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
                    "key": {"type": "string"},
                    "value": {"type": "string"}
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
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remember_conversation",
            "description": "Сохраняет текущий диалог в векторную память. Используй для планов, историй, опыта.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Краткое содержание (1-2 предложения)."}
                },
                "required": ["summary"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Ищет в векторной памяти прошлые разговоры. Используй на «помнишь...», «о чём говорили...».",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
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
                    "relative_path": {"type": "string"}
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
                    "relative_path": {"type": "string"},
                    "content": {"type": "string"}
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
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_code_local",
            "description": "Генерирует код через gpt-5-mini. Используй для написания, исправления или рефакторинга кода.",
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
            "description": "Создаёт задачу, повторяющуюся каждые N минут. 'notification' для простых напоминаний, 'ai_task' для задач с ИИ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "minutes": {"type": "integer"},
                    "prompt": {"type": "string"},
                    "task_type": {
                        "type": "string",
                        "enum": ["notification", "ai_task"]
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
            "description": "Список активных задач планировщика.",
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
                    "job_id": {"type": "string"}
                },
                "required": ["job_id"]
            }
        }
    },

    # === GUI-АВТОМАТИЗАЦИЯ ===
    {
        "type": "function",
        "function": {
            "name": "move_mouse",
            "description": "Перемещает курсор в точку (x, y).",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
                    "duration": {"type": "number", "default": 0.3}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_mouse",
            "description": "Клик мышью. Если x/y не указаны — клик в текущей позиции.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer"},
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
            "description": "Перетаскивание: зажать ЛКМ в (x1,y1), тащить в (x2,y2), отпустить.",
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
            "description": "Прокрутка. amount > 0 — вверх, < 0 — вниз.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "integer"},
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
            "description": "Текущие координаты курсора.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Печатает текст в активное окно. Работает с кириллицей.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Нажимает одну клавишу: 'enter', 'esc', 'tab', 'f5' и т.д.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"}
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hotkey",
            "description": "Комбинация клавиш через '+'. Пример: 'ctrl+c', 'alt+tab'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {"type": "string"}
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_windows",
            "description": "Список открытых окон Windows.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "activate_window",
            "description": "Активирует окно по части заголовка.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_on_screen",
            "description": "Ищет PNG-изображение на экране.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "confidence": {"type": "number", "default": 0.8}
                },
                "required": ["image_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_on_image",
            "description": "Ищет изображение на экране и кликает по центру.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_path": {"type": "string"},
                    "confidence": {"type": "number", "default": 0.8}
                },
                "required": ["image_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_screen_size",
            "description": "Разрешение экрана в пикселях.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Пауза в секундах. Используй между GUI-действиями.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "number"}
                },
                "required": ["seconds"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_screenshot",
            "description": "Скриншот + анализ через OpenAI Vision (gpt-4o-mini). Возвращает текстовое описание того, что на экране. Используй для GUI-задач: найти кнопку, проверить результат клика.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Что именно узнать из скриншота."}
                },
                "required": ["prompt"]
            }
        }
    },

    # ═══ СПЕЦИАЛИЗИРОВАННЫЕ ИНСТРУМЕНТЫ ДЛЯ САЙТОВ ═══
    {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "ОТКРЫВАЕТ браузер на странице Google с запросом. Ты НЕ увидишь результаты. Используй только для 'открой', 'загугли мне'. Для 'узнай/расскажи' используй web_search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "open_first": {"type": "boolean", "default": False}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "youtube_search",
            "description": "Открывает YouTube и ищет видео. Опционально запускает первое.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "open_first": {"type": "boolean", "default": True}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wikipedia_search",
            "description": "Поиск в Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "github_search",
            "description": "Поиск на GitHub.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "search_type": {"type": "string", "enum": ["repositories", "code", "issues", "users"], "default": "repositories"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stackoverflow_search",
            "description": "Поиск на Stack Overflow.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reddit_search",
            "description": "Поиск на Reddit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "maps_search",
            "description": "Поиск на Google Maps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "translate_text",
            "description": "Перевод через Google Translate.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "to_lang": {"type": "string", "default": "en"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "discord_open",
            "description": "Открывает Discord, опционально переходит в канал.",
            "parameters": {
                "type": "object",
                "properties": {
                    "channel_name": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "discord_send",
            "description": "Отправляет сообщение в Discord.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"},
                    "channel_name": {"type": "string"}
                },
                "required": ["message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "spotify_play",
            "description": "Открывает Spotify с поиском.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "twitch_search",
            "description": "Поиск на Twitch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
]