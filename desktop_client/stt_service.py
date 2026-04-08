import sys
import os

# CONFIGURACIÓN DE CODIFICACIÓN PARA WINDOWS CONSOLE
if sys.platform == 'win32':
    try:
        if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

import time
import json
import numpy as np
import soundcard as sc
import ctypes
import vosk
import queue
import threading
from PyQt6.QtCore import QThread, pyqtSignal

class STTService(QThread):
    text_received = pyqtSignal(str)
    partial_text_received = pyqtSignal(str)
    status_received = pyqtSignal(str)

    def __init__(self, device="cpu"):
        super().__init__()
        self.device = device
        self.running = False
        self.model = None
        self.recognizer = None
        self.current_lang = "en" # default (en, zh-CN, ja, fr)
        self.samplerate = 16000
        # Map full locale to short code used by Vosk model downloader
        self.lang_map = {
            "en": "en-us",
            "es": "es",
            "zh-CN": "cn",
            "ja": "ja",
            "fr": "fr",
            "de": "de",
            "it": "it",
            "pt": "pt",
            "ru": "ru",
            "ko": "ko"
        }

    def set_language(self, lang_code):
        if lang_code != self.current_lang:
            self.current_lang = lang_code
            if self.running:
                self.load_model()

    def load_model(self):
        try:
            vosk_lang = self.lang_map.get(self.current_lang, "en-us")
            print(f"DEBUG [STT]: Cargando modelo Vosk para {vosk_lang}...", flush=True)
            self.status_received.emit(f"Cargando modelo {vosk_lang} (Vosk)...")
            
            # Esto descarga el modelo automáticamente si no existe (~40MB)
            self.model = vosk.Model(lang=vosk_lang)
            self.recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)
            print("DEBUG [STT]: Vosk listo.", flush=True)
            return True
        except Exception as e:
            print(f"DEBUG [STT]: Error Vosk: {e}", flush=True)
            self.status_received.emit(f"Error Vosk: {e}")
            return False

    def run(self):
        self.running = True
        try:
            # Inicializar COM para Windows
            try:
                ctypes.windll.ole32.CoInitialize(None)
            except: pass

            if not self.load_model():
                self.running = False
                return

            try:
                print("DEBUG [STT]: Buscando dispositivos de audio...", flush=True)
                default_speaker = sc.default_speaker()
                mic = sc.get_microphone(id=str(default_speaker.name), include_loopback=True)
                print(f"DEBUG [STT]: Capturando: {mic.name}", flush=True)
                self.status_received.emit("Asistente conectado (Vosk)")
            except Exception as e:
                print(f"DEBUG [STT]: Error de audio: {e}", flush=True)
                self.status_received.emit(f"Error de audio: {e}")
                self.running = False
                return

            audio_q = queue.Queue()
            chunk_frames = int(self.samplerate * 0.15) # 150ms for faster updates
            
            def audio_worker():
                try:
                    with mic.recorder(samplerate=self.samplerate) as recorder:
                        while self.running:
                            data = recorder.record(numframes=chunk_frames)
                            if self.running:
                                audio_q.put(data)
                except Exception as ex:
                    print(f"DEBUG [STT]: Error en hilo de audio: {ex}", flush=True)

            t_audio = threading.Thread(target=audio_worker, daemon=True)
            t_audio.start()

            while self.running:
                try:
                    data = audio_q.get(timeout=0.1)
                except queue.Empty:
                    continue

                if data.ndim > 1:
                    data = np.mean(data, axis=1)
                
                pcm_data = (data * 32767).astype(np.int16).tobytes()
                
                if self.recognizer.AcceptWaveform(pcm_data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        self.text_received.emit(text)
                else:
                    partial = json.loads(self.recognizer.PartialResult())
                    partial_text = partial.get("partial", "")
                    if partial_text:
                        self.partial_text_received.emit(partial_text)
        finally:
            try:
                ctypes.windll.ole32.CoUninitialize()
            except: pass

    def stop(self):
        self.running = False
        self.wait()
