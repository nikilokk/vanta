# tools/__init__.py
from tools.file_tools import (
    search_files, read_file, write_file, edit_file, run_command,
)

from tools.system import (
    get_system_info, get_gpu_info, get_running_processes, close_program,
    get_uptime, take_screenshot, get_clipboard, set_clipboard,
    set_volume, toggle_mute, get_screen_size, wait,
    analyze_screenshot,
)

from tools.programs import open_program, open_website
from tools.web import web_search, search_username_osint, get_current_datetime
from tools.sandbox import (
    list_sandbox_files, read_sandbox_file, write_sandbox_file,
)
from tools.code import analyze_codebase, generate_code_local
from tools.scheduler_tools import (
    add_interval_task, list_scheduled_tasks, remove_scheduled_task,
)
from tools.gui import (
    move_mouse, click_mouse, double_click, right_click,
    drag_mouse, scroll_mouse, get_mouse_position,
    type_text, press_key, hotkey,
    list_windows, activate_window,
    find_on_screen, click_on_image,
)
from tools.web_apps import (
    google_search, youtube_search, wikipedia_search, github_search,
    stackoverflow_search, reddit_search, maps_search, translate_text,
    discord_open, discord_send,
    spotify_play, twitch_search,
)


__all__ = [
    # file_tools
    "search_files", "read_file", "write_file", "edit_file", "run_command",
    # system
    "get_system_info", "get_gpu_info", "get_running_processes", "close_program",
    "get_uptime", "take_screenshot", "get_clipboard", "set_clipboard",
    "set_volume", "toggle_mute", "get_screen_size", "wait", "analyze_screenshot",
    # programs
    "open_program", "open_website",
    # web
    "web_search", "search_username_osint", "get_current_datetime",
    # sandbox
    "list_sandbox_files", "read_sandbox_file", "write_sandbox_file",
    # code
    "analyze_codebase", "generate_code_local",
    # scheduler
    "add_interval_task", "list_scheduled_tasks", "remove_scheduled_task",
    # gui
    "move_mouse", "click_mouse", "double_click", "right_click",
    "drag_mouse", "scroll_mouse", "get_mouse_position",
    "type_text", "press_key", "hotkey",
    "list_windows", "activate_window", "find_on_screen", "click_on_image",
    # web_apps
    "google_search", "youtube_search", "wikipedia_search", "github_search",
    "stackoverflow_search", "reddit_search", "maps_search", "translate_text",
    "discord_open", "discord_send",
    "spotify_play", "twitch_search",
]