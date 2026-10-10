import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from interfaces.tts import speak
import time

speak("Сейчас 2024 год. У меня 3 яблока и 50 процентов заряда. Цена — 1500 рублей.")
time.sleep(12)