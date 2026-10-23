# core/api_client.py
"""
Единый клиент для OpenAI API с переиспользованием HTTP-соединений.
Используется для: чата, vision, кода, эмбеддингов.
"""
import base64
import json
import os
import threading
import time
from typing import Optional

from openai import OpenAI

from core.logger import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2
REASONING_MODELS = ("gpt-5", "o1", "o3", "o4")

_client_lock = threading.Lock()
_cached_client: Optional[OpenAI] = None
_cached_config: tuple = ("", "")


def _get_client() -> OpenAI:
    """Возвращает синглтон-клиент OpenAI (пересоздаёт только при смене ключа/URL)."""
    global _cached_client, _cached_config
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    current_cfg = (api_key, base_url)

    with _client_lock:
        if _cached_client is None or _cached_config != current_cfg:
            _cached_client = OpenAI(api_key=api_key, base_url=base_url)
            _cached_config = current_cfg
        return _cached_client


def is_api_available() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _is_retryable_error(error: Exception) -> bool:
    err_str = str(error)
    return any(code in err_str for code in [
        "503", "429", "500", "UNAVAILABLE", "RESOURCE_EXHAUSTED", "rate_limit", "Connection"
    ])


def _track_response_usage(response, model: str, include_completion: bool = True):
    try:
        u = getattr(response, "usage", None)
        if not u:
            return None
        from core.usage_tracker import record_usage
        ptd = getattr(u, "prompt_tokens_details", None)
        return record_usage(
            model=model,
            prompt_tokens=getattr(u, "prompt_tokens", 0) or 0,
            cached_tokens=getattr(ptd, "cached_tokens", 0) or 0 if ptd else 0,
            completion_tokens=(getattr(u, "completion_tokens", 0) or 0) if include_completion else 0,
        )
    except Exception as ex:
        logger.error(f"Usage tracking failed: {ex}")
        return None


def chat_api(messages: list, tools: Optional[list] = None) -> dict:
    """Отправляет запрос в OpenAI Chat Completions."""
    client = _get_client()
    model = os.getenv("MAIN_MODEL", "gpt-5-mini")

    kwargs = {
        "model": model,
        "messages": _convert_messages(messages),
    }

    if not any(model.startswith(p) for p in REASONING_MODELS):
        kwargs["temperature"] = 0.7

    if tools:
        kwargs["tools"] = tools

    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(**kwargs)
            msg = response.choices[0].message
            usage_dict = _track_response_usage(response, model)

            return {
                "message": {
                    "content": msg.content or "",
                    "tool_calls": _parse_tool_calls(msg),
                },
                "usage": usage_dict,
            }

        except Exception as e:
            last_error = e
            err_str = str(e)

            if "tool_call_id" in err_str or "invalid_request" in err_str:
                logger.error(f"Ошибка формата запроса: {e}")
                break

            if _is_retryable_error(e) and attempt < MAX_RETRIES - 1:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(f"Временная ошибка API, пауза {delay}с")
                time.sleep(delay)
                continue

            break

    raise RuntimeError(f"OpenAI API недоступен: {last_error}")


def _get_field(m, field, default=None):
    if isinstance(m, dict):
        return m.get(field, default)
    return getattr(m, field, default)


def _convert_assistant_message(m) -> dict:
    content = _get_field(m, "content", "") or ""
    msg_dict = {"role": "assistant", "content": content or None}

    tool_calls = _get_field(m, "tool_calls")
    if not tool_calls:
        return msg_dict

    formatted = []
    for idx, tc in enumerate(tool_calls):
        if isinstance(tc, dict):
            fn_name = tc["function"]["name"]
            fn_args = tc["function"]["arguments"]
            tc_id = tc.get("id") or f"call_{idx}"
        else:
            fn_name = tc.function.name
            fn_args = tc.function.arguments
            tc_id = getattr(tc, "id", None) or f"call_{idx}"

        if isinstance(fn_args, dict):
            fn_args = json.dumps(fn_args, ensure_ascii=False)
        elif not isinstance(fn_args, str):
            fn_args = str(fn_args)

        formatted.append({
            "id": tc_id,
            "type": "function",
            "function": {"name": fn_name, "arguments": fn_args},
        })

    msg_dict["tool_calls"] = formatted
    return msg_dict


def _convert_messages(messages: list) -> list:
    """Приводит историю к формату OpenAI и удаляет разорванные пары assistant <-> tool."""
    answered_ids = set()
    for m in messages:
        if _get_field(m, "role") == "tool":
            tc_id = _get_field(m, "tool_call_id")
            if tc_id:
                answered_ids.add(tc_id)

    declared_ids = set()
    for m in messages:
        if _get_field(m, "role") == "assistant":
            tool_calls = _get_field(m, "tool_calls")
            if tool_calls:
                for tc in tool_calls:
                    tc_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    if tc_id:
                        declared_ids.add(tc_id)

    result = []
    for m in messages:
        role = _get_field(m, "role")
        content = _get_field(m, "content", "") or ""

        if role == "system":
            result.append({"role": "system", "content": content})

        elif role == "user":
            result.append({"role": "user", "content": content})

        elif role == "assistant":
            tool_calls = _get_field(m, "tool_calls")
            if tool_calls:
                all_answered = True
                for tc in tool_calls:
                    tc_id = tc.get("id") if isinstance(tc, dict) else getattr(tc, "id", None)
                    if tc_id and tc_id not in answered_ids:
                        all_answered = False
                        break

                if not all_answered:
                    logger.warning("Пропускаю assistant с неотвеченными tool_calls")
                    continue

            result.append(_convert_assistant_message(m))

        elif role == "tool":
            tool_call_id = _get_field(m, "tool_call_id")
            if not tool_call_id or tool_call_id not in declared_ids:
                logger.warning(f"Пропускаю осиротевший tool (id={tool_call_id})")
                continue

            result.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": content,
            })

    return result


def _parse_tool_calls(msg) -> Optional[list]:
    if not msg.tool_calls:
        return None

    parsed = []
    for tc in msg.tool_calls:
        try:
            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
        except json.JSONDecodeError:
            logger.warning(f"Не удалось распарсить arguments для {tc.function.name}")
            args = {}
        parsed.append({
            "id": tc.id,
            "function": {"name": tc.function.name, "arguments": args},
        })
    return parsed


def analyze_image(image_path: str, prompt: str) -> str:
    client = _get_client()
    model = os.getenv("VISION_MODEL", "gpt-4o-mini")

    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": f"data:image/png;base64,{img_b64}",
                    "detail": "low",
                }},
            ],
        }],
        max_tokens=500,
    )
    _track_response_usage(response, model)
    return response.choices[0].message.content.strip()


def generate_code(prompt: str, language: str = "python") -> str:
    client = _get_client()
    model = os.getenv("MAIN_MODEL", "gpt-5-mini")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"Ты Senior Software Engineer. Пиши чистый рабочий код на {language}."},
            {"role": "user", "content": prompt},
        ],
    )
    _track_response_usage(response, model)
    return response.choices[0].message.content


def embed_texts(texts: list) -> list:
    client = _get_client()
    model = os.getenv("EMBED_MODEL", "text-embedding-3-small")

    response = client.embeddings.create(model=model, input=texts)
    _track_response_usage(response, model, include_completion=False)
    return [item.embedding for item in response.data]