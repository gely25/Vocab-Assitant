print("=== SYSTEM START: MAIN APP SCRIPT LOADED ===", flush=True)

import sys
import threading
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

class HoverWorker(QObject):
    word_data_ready = pyqtSignal(dict, object, bool)  # word_data, QPoint, pinned

# Configurar logs para depuración
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from overlay_ui import SubtitleOverlay
    from stt_service import STTService
    from api_client import VocabAPIClient
    logging.info("Módulos cargados correctamente")
except Exception as e:
    print(f"ERROR CRÍTICO AL CARGAR MÓDULOS: {e}")
    logging.error(f"Error cargando módulos: {e}")
    sys.exit(1)

class VocabAssistantDesktop:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.api = VocabAPIClient()
        self.overlay = SubtitleOverlay()
        self.overlay.mode_toggled.connect(self.toggle_mode)
        self.mining_mode = True 
        
        # Servicio STT (Vosk)
        self.stt = STTService()
        self.stt.text_received.connect(self.overlay.set_text)
        self.stt.partial_text_received.connect(self.overlay.set_partial)
        self.stt.status_received.connect(self.handle_status)
        self.overlay.lang_changed.connect(self.stt.set_language)
        
        # Worker para Tooltip asíncrono seguro
        self.hover_worker = HoverWorker()
        self.hover_worker.word_data_ready.connect(self.show_hover_tooltip)
        
        # Conectar señales del área de transcripción (SelectableCaptions)
        self.overlay.captions_view.word_hovered.connect(self.handle_hover)
        self.overlay.captions_view.phrase_selected.connect(self.handle_phrase_hover)
        self.overlay.captions_view.word_clicked.connect(self.handle_mining_click)
        
        # Guardar desde el tooltip
        self.overlay.custom_tooltip.save_requested.connect(self.handle_save)

        # Estado de cancelación de peticiones (evita resultados desordenados)
        self._hover_request_id = 0
        self._translation_cache = {}   # word -> word_data dict
        
    def handle_status(self, msg):
        print(f"DEBUG: {msg}")
        
    def toggle_mode(self):
        self.mining_mode = not self.mining_mode
        self.overlay.set_mining_mode(self.mining_mode)

    def handle_hover(self, word, pos):
        """Hover = preview mode (auto-hides)"""
        self._hover_request_id += 1
        my_id = self._hover_request_id
        cache_key = f"{word}:{self.stt.current_lang}"
        if cache_key in self._translation_cache:
            self.overlay.custom_tooltip.show_data(self._translation_cache[cache_key], pos, pinned=False)
            return
        self.overlay.custom_tooltip.show_loading(word, pos, pinned=False)
        source_lang = self.stt.current_lang
        def fetch():
            try:
                data = self.api.get_definition(word.lower().strip(), source_lang=source_lang)
                if my_id != self._hover_request_id:
                    return
                if data:
                    data['word'] = word
                    self._translation_cache[cache_key] = data
                    self.hover_worker.word_data_ready.emit(data, pos, False)
                else:
                    if my_id == self._hover_request_id:
                        self.hover_worker.word_data_ready.emit({'original': word, 'translation': '(No encontrado)'}, pos, False)
            except Exception as e:
                print(f"Error en hover: {e}")
                if my_id == self._hover_request_id:
                    self.hover_worker.word_data_ready.emit({'original': word, 'translation': '(Sin conexión)'}, pos, False)
        threading.Thread(target=fetch, daemon=True).start()

    def handle_phrase_hover(self, phrase, pos):
        """Selection = pinned interactive modal with translation only"""
        self._hover_request_id += 1
        my_id = self._hover_request_id
        cache_key = f"{phrase}:{self.stt.current_lang}"
        if cache_key in self._translation_cache:
            self.overlay.custom_tooltip.show_data(self._translation_cache[cache_key], pos, pinned=True)
            return
        self.overlay.custom_tooltip.show_loading(phrase, pos, pinned=True)
        source_lang = self.stt.current_lang
        def fetch():
            try:
                data = self.api.get_definition(phrase.strip(), source_lang=source_lang)
                if my_id != self._hover_request_id:
                    return
                if data:
                    data['word'] = phrase
                    self._translation_cache[cache_key] = data
                    self.hover_worker.word_data_ready.emit(data, pos, True)
                else:
                    if my_id == self._hover_request_id:
                        self.hover_worker.word_data_ready.emit({'original': phrase, 'translation': '(No encontrado)', 'type': 'phrase'}, pos, True)
            except Exception as e:
                if my_id == self._hover_request_id:
                    self.hover_worker.word_data_ready.emit({'original': phrase, 'translation': '(Sin conexión)', 'type': 'phrase'}, pos, True)
        threading.Thread(target=fetch, daemon=True).start()

    def show_hover_tooltip(self, word_data, pos, pinned):
        self.overlay.custom_tooltip.show_data(word_data, pos, pinned=pinned)

    def handle_save(self, word_data):
        """Guarda la palabra del tooltip como flashcard"""
        threading.Thread(
            target=self.api.save_flashcard,
            args=({
                'word':       word_data.get('original', word_data.get('word', '')),
                'translation': word_data.get('translation', ''),
                'definition':  word_data.get('definition', ''),
                'phonetic':    word_data.get('phonetic', ''),
                'source_lang': self.stt.current_lang,
                'target_lang': 'es'
            },),
            daemon=True
        ).start()

    def handle_mining_click(self, word):
        """Click directo = guardar inmediatamente sin pasar por el modal"""
        source_lang = self.stt.current_lang
        def fetch_and_save():
            data = self.api.get_definition(word.lower(), source_lang=source_lang)
            if data:
                self.api.save_flashcard({
                    'word': word, 'translation': data.get('translation', ''),
                    'definition': data.get('definition', ''), 'phonetic': data.get('phonetic', ''),
                    'source_lang': source_lang, 'target_lang': 'es'
                })
        threading.Thread(target=fetch_and_save, daemon=True).start()

    def handle_mining(self, word):
        """Alias por compatibilidad"""
        self.handle_mining_click(word)

    def handle_meaning(self, word):
        data = self.api.get_definition(word)
        if data:
            msg = f"Significado de {word}:\n\n{data.get('definition', '...')}"
            QMessageBox.information(self.overlay, f"Significado: {word}", msg)

    def run(self):
        try:
            self.overlay.show()
            self.stt.start()
            code = self.app.exec()
            self.stt.stop()
            sys.exit(code)
        except Exception as e:
            QMessageBox.critical(None, "Error Asistente", f"Error inesperado: {e}")

if __name__ == "__main__":
    import os
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
    
    print("\n" + "="*40)
    print("INICIANDO VOCAB ASSISTANT (VOSK VERSION)")
    print("="*40 + "\n")
    
    try:
        assistant = VocabAssistantDesktop()
        assistant.run()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        input("Presiona Enter para cerrar...")
