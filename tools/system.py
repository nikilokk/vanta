# tools/system.py
import os
import time
import mss
import pynvml
import platform
import psutil
import pyperclip
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from datetime import datetime
from pathlib import Path


# === ЗАЩИЩЁННЫЕ ПРОЦЕССЫ (нельзя закрывать) ===
PROTECTED_PROCESSES = {
    "system",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "winlogon.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
    "explorer.exe",
    "dwm.exe",
    "taskhostw.exe",
}


def get_system_info():
    """Информация о CPU, RAM и дисках."""
    memory = psutil.virtual_memory()
    disks = []

    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disks.append({
                "drive": partition.mountpoint,
                "total_gb": round(usage.total / (1024 ** 3), 1),
                "used_gb": round(usage.used / (1024 ** 3), 1),
                "free_gb": round(usage.free / (1024 ** 3), 1),
                "usage_percent": usage.percent,
            })
        except PermissionError:
            pass

    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "cpu": platform.processor(),
        "cpu_usage_percent": psutil.cpu_percent(interval=0.5),
        "ram": {
            "total_gb": round(memory.total / (1024 ** 3), 1),
            "used_gb": round(memory.used / (1024 ** 3), 1),
            "available_gb": round(memory.available / (1024 ** 3), 1),
            "usage_percent": memory.percent,
        },
        "disks": disks,
    }


def get_gpu_info():
    """Информация о видеокарте NVIDIA."""
    try:
        pynvml.nvmlInit()
        gpu_count = pynvml.nvmlDeviceGetCount()
        gpus = []

        for i in range(gpu_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(
                handle, pynvml.NVML_TEMPERATURE_GPU
            )
            if isinstance(name, bytes):
                name = name.decode("utf-8")

            gpus.append({
                "name": name,
                "temperature_c": temperature,
                "gpu_usage_percent": utilization.gpu,
                "memory_usage_percent": utilization.memory,
                "vram_total_gb": round(memory.total / (1024 ** 3), 2),
                "vram_used_gb": round(memory.used / (1024 ** 3), 2),
                "vram_free_gb": round(memory.free / (1024 ** 3), 2),
            })

        pynvml.nvmlShutdown()
        return {"success": True, "gpus": gpus}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_running_processes(limit: int = 10):
    """Список наиболее загруженных процессов."""
    processes = []
    for process in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = process.info
            processes.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu_percent": info["cpu_percent"],
                "memory_percent": round(info["memory_percent"], 2),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return {"success": True, "processes": processes[:limit]}


def close_program(program: str):
    """Закрывает программу по имени."""
    program = program.lower().strip()
    if len(program) < 3:
        return {"success": False, "error": "Имя программы слишком короткое."}

    closed = []
    found = False

    for process in psutil.process_iter(["pid", "name"]):
        try:
            name = process.info["name"]
            if not name:
                continue
            name_lower = name.lower()
            process_stem = Path(name_lower).stem

            if program != process_stem and program not in name_lower.split():
                continue

            found = True
            if name_lower in PROTECTED_PROCESSES:
                continue

            process.terminate()
            closed.append({"pid": process.info["pid"], "name": name})
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    if not found:
        return {"success": False, "error": f"Program '{program}' is not running."}
    return {"success": True, "program": program, "closed": closed}


def get_uptime():
    """Время с момента загрузки ПК."""
    uptime_seconds = time.time() - psutil.boot_time()
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    return {"success": True, "uptime": f"{hours} hours, {minutes} minutes"}


def take_screenshot():
    """Скриншот экрана в папку img/."""
    try:
        project_dir = Path(__file__).resolve().parent.parent
        img_dir = project_dir / "img"
        img_dir.mkdir(exist_ok=True)

        filename = f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        screenshot_path = img_dir / filename

        with mss.mss() as sct:
            sct.shot(mon=1, output=str(screenshot_path))

        return {
            "success": True,
            "image_path": str(screenshot_path),
            "message": "Screenshot captured.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_clipboard():
    """Читает текст из буфера обмена."""
    try:
        return {"success": True, "text": pyperclip.paste()}
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_clipboard(text: str):
    """Копирует текст в буфер обмена."""
    try:
        pyperclip.copy(text)
        return {"success": True, "message": "Text copied to clipboard."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_volume_control():
    devices = AudioUtilities.GetSpeakers()
    if hasattr(devices, "EndpointVolume"):
        return devices.EndpointVolume
    if hasattr(devices, "Activate"):
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    if hasattr(devices, "_device") and hasattr(devices._device, "Activate"):
        interface = devices._device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    raise RuntimeError("Unable to acquire audio endpoint interface.")


def set_volume(level: int):
    """Устанавливает громкость 0-100."""
    try:
        level = max(0, min(100, level))
        volume = _get_volume_control()
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return {"success": True, "message": f"Volume set to {level}%."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def toggle_mute():
    """Переключает mute."""
    try:
        volume = _get_volume_control()
        is_muted = volume.GetMute()
        volume.SetMute(not is_muted, None)
        state = "unmuted" if is_muted else "muted"
        return {"success": True, "message": f"Sound {state}."}
    except Exception as e:
        return {"success": False, "error": str(e)}