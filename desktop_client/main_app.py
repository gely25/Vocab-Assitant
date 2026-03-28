print("=== SYSTEM START: MAIN APP SCRIPT LOADED ===", flush=True)

import sys
import threading
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal

class HoverWorker(QObject):
    translation_ready = pyqtSignal(str, str, object)

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
        self.hover_worker.translation_ready.connect(self.show_hover_tooltip)
        
        # Conectar señales del área de transcripción (SelectableCaptions)
        self.overlay.captions_view.word_hovered.connect(self.handle_hover)
        self.overlay.captions_view.word_clicked.connect(self.handle_mining)
        
    def handle_status(self, msg):
        print(f"DEBUG: {msg}")
        
    def toggle_mode(self):
        self.mining_mode = not self.mining_mode
        self.overlay.set_mining_mode(self.mining_mode)

    def handle_hover(self, word, pos):
        # pos is now a QPoint from SelectableCaptions signal
        self.overlay.custom_tooltip.show_loading(word, pos)
        def fetch():
            try:
                clean_word = word.lower().strip()
                data = self.api.get_definition(clean_word)
                if data and 'translation' in data:
                    self.hover_worker.translation_ready.emit(word, data['translation'], pos)
                else:
                    self.hover_worker.translation_ready.emit(word, "(No encontrado)", pos)
            except Exception as e:
                print(f"Error fetching definition: {e}")
                self.hover_worker.translation_ready.emit(word, "(Error)", pos)
        threading.Thread(target=fetch, daemon=True).start()

    def show_hover_tooltip(self, word, trans, pos):
        self.overlay.custom_tooltip.show_translation(word, trans, pos)

    def handle_mining(self, word):
        data = self.api.get_definition(word)
        if data:
            self.api.save_flashcard({
                'word': word, 'translation': data.get('translation', '...'),
                'definition': data.get('definition', ''), 'phonetic': data.get('phonetic', ''),
                'source_lang': self.stt.current_lang, 'target_lang': 'es'
            })

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
