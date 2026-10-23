# tests/test_vanta_core.py
import pytest
from unittest.mock import patch

from config import VANTA_ROOT, SANDBOX_DIR
from tools.file_tools import safe_path, run_command
from tools.sandbox import read_sandbox_file
from core.agents import get_agent, filter_tools_for_agent, AgentConfig
from core.api_client import _convert_messages
from core.brain import execute_tool, ask_ai, clear_chat_history, _fix_code_fences


# 1. ТЕСТЫ БЕЗОПАСНОСТИ ПУТЕЙ И КОМАНД
def test_safe_path_blocks_outside_directories():
    with pytest.raises(PermissionError):
        safe_path("../../Windows/System32/cmd.exe")


def test_safe_path_blocks_secrets():
    with pytest.raises(PermissionError):
        safe_path(".env")
    with pytest.raises(PermissionError):
        safe_path(".git/config")


def test_safe_path_blocks_self_modification():
    with pytest.raises(PermissionError):
        safe_path("core/brain.py", allow_write=True)
    with pytest.raises(PermissionError):
        safe_path("config.py", allow_write=True)


def test_sandbox_prevents_path_traversal():
    res = read_sandbox_file("../../config.py")
    assert res["success"] is False


def test_run_command_security():
    res1 = run_command("python --version && dir")
    assert res1["success"] is False

    res2 = run_command('python -c "print(123)"')
    assert res2["success"] is False

    res3 = run_command("python --version")
    assert res3["success"] is True


# 2. ТЕСТЫ ВАЛИДАЦИИ PYDANTIC
def test_execute_tool_validation_errors():
    res = execute_tool("set_volume", {"level": 250})
    assert res["success"] is False
    assert "Ошибка валидации" in res["error"]


# 3. ТЕСТЫ МЕНЕДЖЕРА АГЕНТОВ
def test_agent_tools_filtering():
    coder = get_agent("coder")
    assert coder.id == "coder"
    assert "write_sandbox_file" in coder.allowed_tools
    assert "close_program" not in coder.allowed_tools

    dummy_tools = [
        {"function": {"name": "write_sandbox_file"}},
        {"function": {"name": "close_program"}},
    ]
    filtered = filter_tools_for_agent(coder, dummy_tools)
    names = [t["function"]["name"] for t in filtered]
    assert names == ["write_sandbox_file"]


# 4. ТЕСТЫ ОЧИСТКИ ИСТОРИИ
def test_convert_messages_drops_orphans():
    raw_history = [
        {"role": "system", "content": "sys"},
        {"role": "tool", "tool_call_id": "orphan_1", "content": "{}"},
        {"role": "user", "content": "Hello"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": "valid_1", "function": {"name": "get_uptime", "arguments": "{}"}}],
        },
        {"role": "tool", "tool_call_id": "valid_1", "content": '{"uptime": "1h"}'},
    ]
    cleaned = _convert_messages(raw_history)
    roles = [m["role"] for m in cleaned]
    assert roles == ["system", "user", "assistant", "tool"]


# 5. ТЕСТ ЦИКЛА С MOCK API
def test_ask_ai_cycle_with_agent():
    clear_chat_history()

    first_resp = {
        "message": {
            "content": "",
            "tool_calls": [{
                "id": "call_1",
                "function": {"name": "get_current_datetime", "arguments": {}},
            }],
        },
        "usage": {"prompt": 50, "cached": 0, "completion": 10, "total": 60, "cost": 0.0001},
    }
    second_resp = {
        "message": {
            "content": "Всё отлично!",
            "tool_calls": None,
        },
        "usage": {"prompt": 60, "cached": 0, "completion": 10, "total": 70, "cost": 0.0001},
    }

    with patch("core.api_client.chat_api", side_effect=[first_resp, second_resp]) as mock_api:
        result = ask_ai("Тест", agent_id="researcher")
        assert mock_api.call_count == 2
        assert result["display"] == "Всё отлично!"