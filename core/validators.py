# core/validators.py
"""
Pydantic-схемы для валидации аргументов инструментов.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# === ФАЙЛОВЫЕ ОПЕРАЦИИ ===
class ReadFileArgs(BaseModel):
    path: str = Field(..., min_length=1)


class WriteFileArgs(BaseModel):
    path: str = Field(..., min_length=1)
    content: str


class EditFileArgs(BaseModel):
    path: str = Field(..., min_length=1)
    old_text: str = Field(..., min_length=1)
    new_text: str


class SearchFilesArgs(BaseModel):
    query: str = Field(..., min_length=1)


class RunCommandArgs(BaseModel):
    command: str = Field(..., min_length=1)


# === СИСТЕМНЫЕ ФУНКЦИИ ===
class GetRunningProcessesArgs(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)


class CloseProgramArgs(BaseModel):
    program: str = Field(..., min_length=2)


class SetVolumeArgs(BaseModel):
    level: int = Field(..., ge=0, le=100)


class SetClipboardArgs(BaseModel):
    text: str = Field(..., min_length=1)


# === ПРОГРАММЫ И САЙТЫ ===
class OpenProgramArgs(BaseModel):
    program: str = Field(..., min_length=1)


class OpenWebsiteArgs(BaseModel):
    url: str = Field(..., min_length=4)

    @field_validator("url")
    @classmethod
    def _check_url(cls, v: str) -> str:
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            v = "https://" + v
        return v


# === ВЕБ И OSINT ===
class WebSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    max_results: int = Field(default=5, ge=1, le=20)


class SearchUsernameOsintArgs(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)


# === ПАМЯТЬ ===
class SaveMemoryArgs(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=5000)


class RecallMemoryArgs(BaseModel):
    key: Optional[str] = None


class ForgetMemoryArgs(BaseModel):
    key: str = Field(..., min_length=1)


class RememberConversationArgs(BaseModel):
    summary: str = Field(..., min_length=3, max_length=2000)


class SearchMemoryArgs(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)


# === ПЕСОЧНИЦА ===
class ReadSandboxFileArgs(BaseModel):
    relative_path: str = Field(..., min_length=1)


class WriteSandboxFileArgs(BaseModel):
    relative_path: str = Field(..., min_length=1)
    content: str


# === АНАЛИЗ И ГЕНЕРАЦИЯ КОДА ===
class AnalyzeCodebaseArgs(BaseModel):
    file_path: str = Field(..., min_length=1)


class GenerateCodeLocalArgs(BaseModel):
    prompt: str = Field(..., min_length=3)
    language: str = Field(default="python")


# === ПЛАНИРОВЩИК ===
class AddIntervalTaskArgs(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    minutes: int = Field(..., ge=1, le=1440)
    prompt: str = Field(..., min_length=1)
    task_type: Literal["notification", "ai_task"] = "ai_task"


class RemoveScheduledTaskArgs(BaseModel):
    job_id: str = Field(..., min_length=3)


# === GUI-АВТОМАТИЗАЦИЯ ===
class MoveMouseArgs(BaseModel):
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    duration: float = Field(default=0.3, ge=0.0, le=5.0)


class ClickMouseArgs(BaseModel):
    x: Optional[int] = Field(default=None, ge=0)
    y: Optional[int] = Field(default=None, ge=0)
    button: Literal["left", "right", "middle"] = "left"
    clicks: int = Field(default=1, ge=1, le=5)


class DoubleClickArgs(BaseModel):
    x: Optional[int] = Field(default=None, ge=0)
    y: Optional[int] = Field(default=None, ge=0)


class RightClickArgs(BaseModel):
    x: Optional[int] = Field(default=None, ge=0)
    y: Optional[int] = Field(default=None, ge=0)


class DragMouseArgs(BaseModel):
    x1: int = Field(..., ge=0)
    y1: int = Field(..., ge=0)
    x2: int = Field(..., ge=0)
    y2: int = Field(..., ge=0)
    duration: float = Field(default=0.5, ge=0.1, le=5.0)


class ScrollMouseArgs(BaseModel):
    amount: int = Field(..., ge=-100, le=100)
    x: Optional[int] = Field(default=None, ge=0)
    y: Optional[int] = Field(default=None, ge=0)


class TypeTextArgs(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class PressKeyArgs(BaseModel):
    key: str = Field(..., min_length=1, max_length=20)


class HotkeyArgs(BaseModel):
    keys: str = Field(..., min_length=3, max_length=50)


class ActivateWindowArgs(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class FindOnScreenArgs(BaseModel):
    image_path: str = Field(..., min_length=1)
    confidence: float = Field(default=0.8, ge=0.1, le=1.0)


class ClickOnImageArgs(BaseModel):
    image_path: str = Field(..., min_length=1)
    confidence: float = Field(default=0.8, ge=0.1, le=1.0)


class WaitArgs(BaseModel):
    seconds: float = Field(..., ge=0.0, le=10.0)


class GetScreenSizeArgs(BaseModel):
    pass


class AnalyzeScreenshotArgs(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=1000)


# === WEB APPS ===
class GoogleSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    open_first: bool = False


class YoutubeSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    open_first: bool = True


class WikipediaSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)


class GithubSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    search_type: Literal["repositories", "code", "issues", "users"] = "repositories"


class StackoverflowSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)


class RedditSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)


class MapsSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)


class TranslateTextArgs(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    to_lang: str = Field(default="en", min_length=2, max_length=5)


class DiscordOpenArgs(BaseModel):
    channel_name: Optional[str] = None


class DiscordSendArgs(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    channel_name: Optional[str] = None


class SpotifyPlayArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)


class TwitchSearchArgs(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)


# === КАРТА СХЕМ ===
TOOL_SCHEMAS = {
    # file_tools
    "read_file": ReadFileArgs,
    "write_file": WriteFileArgs,
    "edit_file": EditFileArgs,
    "search_files": SearchFilesArgs,
    "run_command": RunCommandArgs,
    # system
    "get_running_processes": GetRunningProcessesArgs,
    "close_program": CloseProgramArgs,
    "set_volume": SetVolumeArgs,
    "set_clipboard": SetClipboardArgs,
    # programs
    "open_program": OpenProgramArgs,
    "open_website": OpenWebsiteArgs,
    # web
    "web_search": WebSearchArgs,
    "search_username_osint": SearchUsernameOsintArgs,
    # memory
    "save_memory": SaveMemoryArgs,
    "recall_memory": RecallMemoryArgs,
    "forget_memory": ForgetMemoryArgs,
    "remember_conversation": RememberConversationArgs,
    "search_memory": SearchMemoryArgs,
    # sandbox
    "read_sandbox_file": ReadSandboxFileArgs,
    "write_sandbox_file": WriteSandboxFileArgs,
    # code
    "analyze_codebase": AnalyzeCodebaseArgs,
    "generate_code_local": GenerateCodeLocalArgs,
    # scheduler
    "add_interval_task": AddIntervalTaskArgs,
    "remove_scheduled_task": RemoveScheduledTaskArgs,
    # GUI
    "move_mouse": MoveMouseArgs,
    "click_mouse": ClickMouseArgs,
    "double_click": DoubleClickArgs,
    "right_click": RightClickArgs,
    "drag_mouse": DragMouseArgs,
    "scroll_mouse": ScrollMouseArgs,
    "type_text": TypeTextArgs,
    "press_key": PressKeyArgs,
    "hotkey": HotkeyArgs,
    "activate_window": ActivateWindowArgs,
    "find_on_screen": FindOnScreenArgs,
    "click_on_image": ClickOnImageArgs,
    "wait": WaitArgs,
    "get_screen_size": GetScreenSizeArgs,
    "analyze_screenshot": AnalyzeScreenshotArgs,
    # web_apps
    "google_search": GoogleSearchArgs,
    "youtube_search": YoutubeSearchArgs,
    "wikipedia_search": WikipediaSearchArgs,
    "github_search": GithubSearchArgs,
    "stackoverflow_search": StackoverflowSearchArgs,
    "reddit_search": RedditSearchArgs,
    "maps_search": MapsSearchArgs,
    "translate_text": TranslateTextArgs,
    "discord_open": DiscordOpenArgs,
    "discord_send": DiscordSendArgs,
    "spotify_play": SpotifyPlayArgs,
    "twitch_search": TwitchSearchArgs,
}