import io
import queue
import sys
import os

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_LOGGING_WARNINGS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"


import wave
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from rich.console import Console

if sys.platform == "win32":
    site_packages = os.path.join(sys.prefix, "Lib", "site-packages")
    cublas_path = os.path.join(site_packages, "nvidia", "cublas", "bin")
    cudnn_path = os.path.join(site_packages, "nvidia", "cudnn", "bin")

    if os.path.exists(cublas_path):
        os.add_dll_directory(cublas_path)
    if os.path.exists(cudnn_path):
        os.add_dll_directory(cudnn_path)

console = Console()

# Параметры записи аудио
SAMPLE_RATE = 16000
CHANNELS = 1

# Загрузка модели Faster-Whisper
# Для RTX 3060 оптимально использовать модель 'small' или 'medium' на float16
console.print("[dim]Loading Whisper voice recognition model...[/dim]")
try:
    whisper_model = WhisperModel("small", device="cuda", compute_type="float16")
    console.print("[bold green]✔ Voice model loaded on GPU (CUDA).[/bold green]")
except Exception as e:
    console.print(f"[yellow]⚠️ CUDA fallback to CPU: {e}[/yellow]")
    whisper_model = WhisperModel("small", device="cpu", compute_type="int8")


def record_audio(silence_threshold=0.01, silence_duration=1.5, max_duration=15):
    """
    Записывает аудио с микрофона с автоматическим детектором тишины.
    Останавливает запись, когда пользователь замолкает.
    """
    audio_queue = queue.Queue()

    def callback(indata, frames, time, status):
        if status:
            console.print(f"[red]Audio status: {status}[/red]")
        audio_queue.put(indata.copy())

    console.print(
        "\n[bold cyan]🎙️ Listening... Speak now (stop speaking to process)[/bold cyan]"
    )

    recorded_chunks = []
    silent_chunks_count = 0
    chunk_duration = 0.1  # 100ms chunks
    chunks_for_silence = int(silence_duration / chunk_duration)
    max_chunks = int(max_duration / chunk_duration)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        callback=callback,
        blocksize=int(SAMPLE_RATE * chunk_duration),
    ):
        has_spoken = False

        for _ in range(max_chunks):
            data = audio_queue.get()
            recorded_chunks.append(data)

            # Вычисление громкости (RMS)
            volume_norm = np.linalg.norm(data) / np.sqrt(len(data))

            if volume_norm > silence_threshold:
                has_spoken = True
                silent_chunks_count = 0
            else:
                if has_spoken:
                    silent_chunks_count += 1

            # Прекращаем запись, если после начала речи наступила тишина
            if has_spoken and silent_chunks_count >= chunks_for_silence:
                break

    if not recorded_chunks or not has_spoken:
        return None

    audio_data = np.concatenate(recorded_chunks, axis=0)
    audio_int16 = (audio_data * 32767).astype(np.int16)

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())

    wav_io.seek(0)
    return wav_io


def listen_and_transcribe():
    """
    Слушает микрофон и возвращает распознанный текст.
    """
    audio_stream = record_audio()

    if not audio_stream:
        return None

    console.print("[dim]Transcribing speech...[/dim]")

    segments, _ = whisper_model.transcribe(
        audio_stream, language="ru", beam_size=2
    )

    text = " ".join([segment.text for segment in segments]).strip()
    return text if text else None