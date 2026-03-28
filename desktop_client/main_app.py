print("=== SYSTEM START: MAIN APP SCRIPT LOADED ===", flush=True)

import sys
import threading
import os
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt6.QtCore import QObject, pyqtSignal, Qt, QTimer, QPoint, pyqtSlot

class HoverWorker(QObject):
    word_data_ready = pyqtSignal(dict, QPoint, bool)  # word_data, pos, pinned
    save_result = pyqtSignal(dict)   # {status, message}

# Configurar logs para depuración
log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug.log")
logging.basicConfig(filename=log_path, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from overlay_ui import SubtitleOverlay, LanguageSelectorDialog
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
        self.app.setQuitOnLastWindowClosed(False)
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
        
        # Worker para cross-thread signals seguros
        # HoverWorker es QObject en el hilo principal → las señales cross-thread
        # son encoladas automáticamente por Qt (Qt.ConnectionType.QueuedConnection)
        self.hover_worker = HoverWorker()
        # Asegurar que el worker vive en el hilo principal de Qt
        self.hover_worker.moveToThread(QApplication.instance().thread())
        self.hover_worker.word_data_ready.connect(self.show_hover_tooltip)
        self.hover_worker.save_result.connect(self.on_save_result)
        
        # Conectar señales del área de transcripción (SelectableCaptions)
        self.overlay.captions_view.word_hovered.connect(self.handle_hover)
        self.overlay.captions_view.phrase_selected.connect(self.handle_phrase_hover)
        self.overlay.captions_view.word_clicked.connect(self.handle_mining_click)
        
        # Guardar desde el tooltip
        self.overlay.custom_tooltip.save_requested.connect(self.handle_save)

        # Configuracion en tiempo de ejecucion (engranaje)
        self.overlay.open_settings.connect(self.show_settings_dialog)

        # Estado de cancelación de peticiones
        self._hover_request_id = 0
        self._translation_cache = {}

        # Debounce del hover: evita inundar el servidor con requests
        self._hover_timer = QTimer()
        self._hover_timer.setSingleShot(True)
        self._hover_timer.timeout.connect(self._fire_hover_request)
        self._hover_pending = None   # (word, pos, source_lang, my_id, is_pinned)

    def handle_status(self, msg):
        print(f"DEBUG: {msg}")
        
    def toggle_mode(self):
        self.mining_mode = not self.mining_mode
        self.overlay.set_mining_mode(self.mining_mode)

    def handle_hover(self, word, pos):
        """Hover → debounce 450ms antes de lanzar request al servidor."""
        self._hover_request_id += 1
        my_id = self._hover_request_id
        cache_key = f"{word}:{self.stt.current_lang}"

        # Cache hit → instantáneo, sin tocar el servidor
        if cache_key in self._translation_cache:
            self.overlay.custom_tooltip.show_data(
                self._translation_cache[cache_key], pos, pinned=False)
            return

        # Mostrar "Buscando..." y programar el request con debounce
        self.overlay.custom_tooltip.show_loading(word, pos, pinned=False)
        self._hover_pending = (word, pos, self.stt.current_lang, my_id, False)
        self._hover_timer.start(450)  # 450ms sin nuevo hover → dispara el request

    def _fire_hover_request(self):
        """Ejecuta el request HTTP tras el debounce."""
        if not self._hover_pending:
            return
        word, pos, source_lang, my_id, is_pinned = self._hover_pending
        self._hover_pending = None

        def fetch():
            try:
                tgt_lang = getattr(self, 'target_lang', 'es')
                data = self.api.get_definition(word.lower().strip(),
                                               source_lang=source_lang,
                                               target_lang=tgt_lang)
                if my_id != self._hover_request_id:
                    return  # Resultado desfasado, descartar
                if data:
                    data['original'] = word
                    if is_pinned and len(word.split()) > 1:
                        data['type'] = 'phrase'
                    self._translation_cache[f"{word}:{source_lang}"] = data
                    self.hover_worker.word_data_ready.emit(data, pos, is_pinned)
                else:
                    err_data = {'original': word, 'translation': '(No encontrado)'}
                    if is_pinned and len(word.split()) > 1:
                        err_data['type'] = 'phrase'
                    self.hover_worker.word_data_ready.emit(err_data, pos, is_pinned)
            except Exception as e:
                if 'timed out' not in str(e).lower():
                    print(f"[hover] Error: {e}")
                if my_id == self._hover_request_id:
                    err_data = {'original': word, 'translation': '(Sin conexión)'}
                    if is_pinned and len(word.split()) > 1:
                        err_data['type'] = 'phrase'
                    self.hover_worker.word_data_ready.emit(err_data, pos, is_pinned)
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
        self._hover_pending = (phrase, pos, self.stt.current_lang, my_id, True)
        self._hover_timer.start(300)  # selección es más intencional, menor debounce


    def show_hover_tooltip(self, word_data, pos, pinned):
        self.overlay.custom_tooltip.show_data(word_data, pos, pinned=pinned)

    def handle_save(self, word_data):
        """Guarda la palabra del tooltip como flashcard."""
        try:
            word = word_data.get('original') or word_data.get('word', '')
            print(f"[handle_save] Iniciando guardado de: '{word}'")
            payload = {
                'word':        word,
                'translation': word_data.get('translation', ''),
                'definition':  word_data.get('definition', ''),
                'phonetic':    word_data.get('phonetic', ''),
                'source_lang': self.stt.current_lang,
                'target_lang': getattr(self, 'target_lang', 'es')
            }
            def do_save():
                print(f"[do_save] POST /save/ word='{word}'")
                result = self.api.save_flashcard(payload)
                print(f"[do_save] Respuesta del servidor: {result}")
                if not isinstance(result, dict):
                    result = {'status': 'error', 'message': 'Respuesta inválida del servidor'}
                self.hover_worker.save_result.emit(result)
            threading.Thread(target=do_save, daemon=True).start()
        except Exception as ex:
            print(f"[handle_save] CRITICAL ERROR: {ex}")
            try: self.hover_worker.save_result.emit({'status':'error', 'message': str(ex)})
            except: pass

    def on_save_result(self, result):
        """Actualiza el botón de guardar con el resultado del servidor"""
        print(f"[on_save_result] {result}")
        self.overlay.custom_tooltip.show_save_result(result)

    def handle_mining_click(self, word):
        """Click directo = guardar inmediatamente sin pasar por el modal"""
        source_lang = self.stt.current_lang
        target_lang = getattr(self, 'target_lang', 'es')
        def fetch_and_save():
            data = self.api.get_definition(word.lower(), source_lang=source_lang)
            if data:
                self.api.save_flashcard({
                    'word': word, 'translation': data.get('translation', ''),
                    'definition': data.get('definition', ''), 'phonetic': data.get('phonetic', ''),
                    'source_lang': source_lang, 'target_lang': target_lang
                })
        threading.Thread(target=fetch_and_save, daemon=True).start()

    def handle_mining(self, word):
        """Alias por compatibilidad"""
        self.handle_mining_click(word)

    def show_settings_dialog(self):
        """Llamado cuando el usuario presiona el engranaje o la píldora de idioma."""
        dialog = LanguageSelectorDialog()
        
        # Pre-seleccionar los idiomas actuales en los combobox
        src_idx = dialog.src_combo.findData(self.stt.current_lang)
        if src_idx >= 0: dialog.src_combo.setCurrentIndex(src_idx)
        
        tgt_idx = dialog.tgt_combo.findData(getattr(self, 'target_lang', 'es'))
        if tgt_idx >= 0: dialog.tgt_combo.setCurrentIndex(tgt_idx)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            src_code, tgt_code = dialog.get_selection()
            self.target_lang = tgt_code
            
            # Si el idioma fuente (audio) cambió, reconfigurar STT
            if src_code != self.stt.current_lang:
                self.stt.set_language(src_code)
                src_name = list(filter(lambda x: x["code"] == src_code, self.overlay.LANGUAGES))[0]["name"]
                self.overlay.current_lang_idx = [i for i, x in enumerate(self.overlay.LANGUAGES) if x["code"] == src_code][0]
                self.overlay.lang_pill.setText(src_name)
                self.overlay.set_status_message(f"Cambiando Vosk a {src_name}...")

    def handle_meaning(self, word):
        data = self.api.get_definition(word)
        if data:
            msg = f"Significado de {word}:\n\n{data.get('definition', '...')}"
            QMessageBox.information(self.overlay, f"Significado: {word}", msg)

    def run(self):
        try:
            # Show configuration dialog before doing anything
            dialog = LanguageSelectorDialog()
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return  # User closed or cancelled

            src_code, tgt_code = dialog.get_selection()
            self.stt.set_language(src_code)  # This safely updates vosk lang
            self.target_lang = tgt_code
            
            # Map code to readable name for UI
            src_name = list(filter(lambda x: x["code"] == src_code, self.overlay.LANGUAGES))[0]["name"]
            
            # Setup initial state
            self.overlay.current_lang_idx = [i for i, x in enumerate(self.overlay.LANGUAGES) if x["code"] == src_code][0]
            self.overlay.lang_pill.setText(src_name)
            self.overlay.set_status_message(f"Listo para escuchar en {src_name}...")
            
            # Show transparent UI and connect microphone
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
    
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        import traceback
        print("\n[CRITICAL ERROR] Python Exception in PyQt Slot:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        sys.exit(1)
        
    sys.excepthook = global_exception_handler

    try:
        assistant = VocabAssistantDesktop()
        assistant.run()
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        input("Presiona Enter para cerrar...")
