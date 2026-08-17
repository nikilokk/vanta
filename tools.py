import subprocess
import os
import time
import tempfile
import mss
import pynvml
import platform
import psutil
import pyperclip
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from datetime import datetime
from ddgs import DDGS
from pathlib import Path

PROGRAM_ALIASES = {
    "vs code": "visual studio code",
    "vscode": "visual studio code",
    "code": "visual studio code",
    "discord": "discord",
    "steam": "steam",
    "firefox": "firefox",
    "chrome": "google chrome",
}

def get_system_info():
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

def take_screenshot():
    try:
        # Папка img в корне вашего проекта D:\Vanta\img
        project_dir = os.path.dirname(os.path.abspath(__file__))
        img_dir = os.path.join(project_dir, "img")
        os.makedirs(img_dir, exist_ok=True)

        # Генерация уникального имени с меткой времени
        filename = f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        screenshot_path = os.path.join(img_dir, filename)

        with mss.mss() as sct:
            sct.shot(mon=1, output=screenshot_path)

        return {
            "success": True,
            "image_path": screenshot_path,
            "message": "Screenshot captured successfully.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_uptime():
    uptime_seconds = time.time() - psutil.boot_time()

    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    return {
        "success": True,
        "uptime": f"{hours} hours, {minutes} minutes"
    }

def close_program(program: str):
    program = program.lower().strip()

    if len(program) < 3:
        return {"success": False, "error": "Имя программы слишком короткое для поиска."}
    
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

            closed.append({
                "pid": process.info["pid"],
                "name": name
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    if not found:
        return {
            "success": False,
            "error": f"Program '{program}' is not running."
        }

    return {
        "success": True,
        "program": program,
        "closed": closed
    }

def web_search(query: str, max_results: int = 5):
    actual_limit = max(max_results, 5)
    results = []

    with DDGS() as ddgs:
        for result in ddgs.text(query, max_results=actual_limit):
            results.append({
                "title": result.get("title"),
                "url": result.get("href"),
                "snippet": result.get("body"),
            })

    return results

def get_running_processes(limit: int = 10):
    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "cpu_percent", "memory_percent"]
    ):
        try:
            info = process.info

            processes.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu_percent": info["cpu_percent"],
                "memory_percent": round(
                    info["memory_percent"], 2
                ),
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(
        key=lambda x: x["cpu_percent"],
        reverse=True
    )

    return {
        "success": True,
        "processes": processes[:limit]
    }

def get_gpu_info():
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
                handle,
                pynvml.NVML_TEMPERATURE_GPU
            )

            if isinstance(name, bytes):
                name = name.decode("utf-8")

            gpus.append({
                "name": name,
                "temperature_c": temperature,
                "gpu_usage_percent": utilization.gpu,
                "memory_usage_percent": utilization.memory,
                "vram_total_gb": round(
                    memory.total / (1024 ** 3), 2
                ),
                "vram_used_gb": round(
                    memory.used / (1024 ** 3), 2
                ),
                "vram_free_gb": round(
                    memory.free / (1024 ** 3), 2
                ),
            })

        pynvml.nvmlShutdown()

        return {
            "success": True,
            "gpus": gpus
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def find_program(program: str):
    program = program.lower().strip()

    search_name = PROGRAM_ALIASES.get(program, program)

    search_locations = [
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft/Windows/Start Menu/Programs",

        Path(os.environ.get("PROGRAMDATA", ""))
        / "Microsoft/Windows/Start Menu/Programs",
    ]

    matches = []

    for location in search_locations:

        if not location.exists():
            continue

        for path in location.rglob("*"):

            if not path.is_file():
                continue

            filename = path.stem.lower()

            if search_name in filename:
                matches.append(path)

    if matches:
        path = matches[0]

        return {
            "success": True,
            "name": path.stem,
            "path": str(path),
        }

    result = subprocess.run(
        ["where", search_name],
        capture_output=True,
        text=True,
        shell=True
    )

    if result.returncode == 0:

        path = result.stdout.strip().splitlines()[0]

        return {
            "success": True,
            "name": search_name,
            "path": path,
        }

    return {
        "success": False,
        "error": f"Program '{program}' was not found."
    }

def launch_program(program: str):
    result = find_program(program)

    if not result["success"]:
        return result

    path = result["path"]

    try:
        os.startfile(path)

        return {
            "success": True,
            "program": result["name"],
            "path": path,
            "message": f"Successfully launched {result['name']}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def open_program(program: str):
    try:
        os.startfile(program)

        return {
            "success": True,
            "message": f"Opened {program}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def open_website(url: str):
    try:
        os.startfile(url)

        return {
            "success": True,
            "message": f"Opened {url}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_current_datetime():
    from datetime import datetime

    now = datetime.now()

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "day": now.strftime("%A"),
    }

def get_clipboard():
    try:
        text = pyperclip.paste()
        return {"success": True, "text": text}
    except Exception as e:
        return {"success": False, "error": str(e)}


def set_clipboard(text: str):
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
    try:
        level = max(0, min(100, level))
        volume = _get_volume_control()
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return {"success": True, "message": f"Volume set to {level}%."}
    except Exception as e:
        return {"success": False, "error": str(e)}

def toggle_mute():
    try:
        volume = _get_volume_control()
        is_muted = volume.GetMute()
        volume.SetMute(not is_muted, None)
        state = "unmuted" if is_muted else "muted"
        return {"success": True, "message": f"Sound {state}."}
    except Exception as e:
        return {"success": False, "error": str(e)}