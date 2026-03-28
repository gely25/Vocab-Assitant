import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, 
                             QFrame, QTextBrowser, QPushButton, QDialog, QComboBox, QScrollArea)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRect, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QTextCursor

class LanguageSelectorDialog(QDialog):
    """
    Startup modal to select source (audio) and target (translation) languages.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("VocabAssistant - Preparar")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main layout
        layout = QVBoxLayout(self)
        
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(35, 15, 65, 0.95);
                border: 1px solid rgba(139, 109, 208, 0.4);
                border-radius: 14px;
            }
            QLabel { color: #E8E8F0; font-size: 14px; font-weight: bold; }
            QComboBox {
                background: #1E1235; color: white;
                border: 1px solid #4A3A75; border-radius: 6px;
                padding: 6px; font-size: 13px;
            }
            QPushButton {
                background: #7B5EA7; color: white; border: none;
                border-radius: 8px; padding: 10px 0; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: #9B7EC8; }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(24, 24, 24, 24)
        container_layout.setSpacing(16)

        title = QLabel("Configurar Sesión")
        title.setStyleSheet("font-size: 18px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)

        # Source Audio (Vosk)
        container_layout.addWidget(QLabel("Idioma del Audio (Vosk):"))
        self.src_combo = QComboBox()
        for lang in SubtitleOverlay.LANGUAGES:
            self.src_combo.addItem(lang["name"], lang["code"])
        container_layout.addWidget(self.src_combo)

        # Target Translation (API)
        container_layout.addWidget(QLabel("Traducir al:"))
        self.tgt_combo = QComboBox()
        for lang in SubtitleOverlay.LANGUAGES:
            self.tgt_combo.addItem(lang["name"], lang["code"])
        container_layout.addWidget(self.tgt_combo)

        # Start button
        start_btn = QPushButton("Iniciar Asistente")
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.clicked.connect(self.accept)
        container_layout.addWidget(start_btn)

        layout.addWidget(container)
        self.setFixedSize(300, 360)

    def get_selection(self):
        return self.src_combo.currentData(), self.tgt_combo.currentData()


class TranslationTooltip(QWidget):
    """
    Floating translation card.
    - Hover → shows for HOVER_MS ms after mouse leaves
    - Text selection → pinned (stays until ✕ or click-outside)
    - Save button always visible (grayed while loading)
    """
    save_requested = pyqtSignal(dict)

    FIXED_W   = 300          # fixed width — avoids adjustSize() geometry errors
    HOVER_MS  = 1200         # ms to keep visible after mouse leaves (hover mode)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint |
                                  Qt.WindowType.WindowStaysOnTopHint |
                                  Qt.WindowType.Tool)
        # WindowDoesNotAcceptFocus removed: on Windows it blocks child widget clicks
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(self.FIXED_W)

        self._word_data   = {}
        self._current_word = ''
        self._pinned      = False
        self._last_pos    = QPoint()

        # ── stylesheet ──────────────────────────────────────────────
        self.setStyleSheet("""
            QWidget#card {
                background: rgba(30, 10, 60, 0.98);  /* Morado ultra-opaco */
                border: 1px solid rgba(139, 109, 208, 0.35);
                border-radius: 14px;
            }
            QLabel#word_lbl  { color: #FFFFFF; font-size:15px; font-weight:700; }
            QLabel#phone_lbl { color: #8C8CAB; font-size:11px; font-style:italic; }
            QLabel#trans_lbl { color: #FFFFFF; font-size:17px; font-weight:800; }
            QLabel#def_lbl   { color: #D1D1D1; font-size:12px; }
            QLabel#status_lbl{ color: #888899; font-size:11px; }
            QPushButton#save_btn {
                background:#7B5EA7; color:white; border:none;
                border-radius:8px; padding:7px 0; font-size:13px; font-weight:600;
            }
            QPushButton#save_btn:hover   { background:#9B7EC8; }
            QPushButton#save_btn:disabled{ background:#3A3A4A; color:#666; }
        """)

        # ── card container ───────────────────────────────────────────
        card = QWidget(self)
        card.setObjectName("card")
        card.setFixedWidth(self.FIXED_W)
        
        self.card_vbox = QVBoxLayout(card)
        self.card_vbox.setContentsMargins(16, 12, 16, 16)
        self.card_vbox.setSpacing(10)

        # 1. Header (Static/Top)
        hdr = QHBoxLayout()
        self.word_lbl = QLabel()
        self.word_lbl.setObjectName("word_lbl")
        self.word_lbl.setWordWrap(False)
        self.word_lbl.setMaximumWidth(220)
        hdr.addWidget(self.word_lbl, 1)
        
        close_lbl = QLabel("✕")
        close_lbl.setStyleSheet("color:#888; font-size:14px; padding:2px;")
        close_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        close_lbl.mousePressEvent = lambda _e: self._force_close()
        hdr.addWidget(close_lbl)
        self.card_vbox.addLayout(hdr)

        # 2. Content
        self.phone_lbl = QLabel()
        self.phone_lbl.setObjectName("phone_lbl")
        self.phone_lbl.hide()
        self.card_vbox.addWidget(self.phone_lbl)

        self.trans_lbl = QLabel("…")
        self.trans_lbl.setObjectName("trans_lbl")
        self.trans_lbl.setWordWrap(True)
        self.trans_lbl.setFixedWidth(self.FIXED_W - 32)
        self.card_vbox.addWidget(self.trans_lbl)

        self.def_lbl = QLabel()
        self.def_lbl.setObjectName("def_lbl")
        self.def_lbl.setWordWrap(True)
        self.def_lbl.setFixedWidth(self.FIXED_W - 32)
        self.def_lbl.hide()
        self.card_vbox.addWidget(self.def_lbl)

        # 3. Footer
        self.status_lbl = QLabel("Click para guardar")
        self.status_lbl.setObjectName("status_lbl")
        self.card_vbox.addWidget(self.status_lbl)

        self.save_btn = QPushButton("＋ Guardar en mis tarjetas")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setFixedHeight(36)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save)
        self.card_vbox.addWidget(self.save_btn)

        # Add card to window
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(card)

        # ── hide timer ───────────────────────────────────────────────
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._auto_hide)

        QApplication.instance().installEventFilter(self)

    # ── event filter: close pinned on click-outside ──────────────────
    def eventFilter(self, obj, event):
        try:
            from PyQt6.QtCore import QEvent
            if (self._pinned and self.isVisible()
                    and event.type() == QEvent.Type.MouseButtonPress
                    and hasattr(event, 'globalPosition')):
                if not self.geometry().contains(event.globalPosition().toPoint()):
                    self._force_close()
        except Exception:
            pass
        return super().eventFilter(obj, event)

    # ── internal helpers ─────────────────────────────────────────────
    def _force_close(self):
        self._pinned = False
        self._hide_timer.stop()
        self._reset_btn_style()
        self.hide()

    def _auto_hide(self):
        if not self._pinned:
            self.hide()

    def _reset_btn_style(self):
        self.save_btn.setStyleSheet("")
        self.save_btn.setText("＋ Guardar en mis tarjetas")
        self.save_btn.setEnabled(False)

    def _place(self, global_pos):
        """Position ABOVE with adaptive height and safety margin."""
        # Force layout to recalculate the height for our fixed width
        h = self.layout().heightForWidth(self.FIXED_W) + 20
        self.setFixedSize(self.FIXED_W, h)

        screen = QApplication.primaryScreen().availableGeometry()
        x = max(screen.left() + 8,
                min(global_pos.x() - self.FIXED_W // 2,
                    screen.right() - self.FIXED_W - 8))
        
        # Position further up (60px offset) to avoid covering the subtitle bar
        y = global_pos.y() - h - 60
        if y < screen.top() + 8:
            y = global_pos.y() + 40    # fallback below if near top
        self.move(x, y)

    # ── public API ───────────────────────────────────────────────────
    def show_loading(self, word: str, global_pos, pinned: bool = False):
        self._hide_timer.stop()
        self._pinned      = pinned
        self._word_data   = {}
        self._current_word = word
        self._reset_btn_style()

        self.word_lbl.setText(word)
        self.phone_lbl.hide()
        self.trans_lbl.setText("Buscando traducción…")
        self.def_lbl.hide()
        self.status_lbl.setText("🔄 Traduciendo…" if pinned else "Hover para ver • click para guardar")
        self._last_pos = global_pos
        self._place(global_pos)
        self.show()
        self.raise_()

    def show_data(self, word_data: dict, global_pos, pinned: bool = False):
        if not self.isVisible() and not pinned:
            return   # user moved away; discard

        self._word_data    = word_data
        self._current_word = word_data.get('original', word_data.get('word', ''))
        self._last_pos     = global_pos

        is_phrase = (word_data.get('type') == 'phrase' or
                     len(self._current_word.split()) > 1)

        # header row visibility
        if is_phrase:
            self.word_lbl.setText("Selección")
        else:
            self.word_lbl.setText(self._current_word)

        phonetic = word_data.get('phonetic', '')
        if phonetic and not is_phrase:
            self.phone_lbl.setText(phonetic)
            self.phone_lbl.show()
        else:
            self.phone_lbl.hide()

        self.trans_lbl.setText(word_data.get('translation', '—'))

        defn = '' if is_phrase else word_data.get('definition', '')
        if defn and len(defn) > 5:
            self.def_lbl.setText(defn[:140] + ('…' if len(defn) > 140 else ''))
            self.def_lbl.show()
        else:
            self.def_lbl.hide()

        if pinned or self._pinned:
            self._pinned = True
            self.status_lbl.setText("📌 Fijado — click fuera para cerrar")
            self._reset_btn_style()
            self.save_btn.setEnabled(True)
        else:
            self.status_lbl.setText("Click para fijar y guardar")

        self._hide_timer.stop()
        self._place(global_pos) # Trigger sizing/placing with final text
        self.show()
        self.raise_()

    def show_save_result(self, result: dict):
        status = result.get('status', 'error')
        if status == 'ok':
            self.save_btn.setText("✓ Guardada en el mazo")
            self.save_btn.setStyleSheet(
                "QPushButton#save_btn{background:#2E7D32;color:white;border:none;"
                "border-radius:8px;padding:7px 0;font-size:13px;font-weight:600;}")
            self.status_lbl.setText("✅ Agregada a tus tarjetas")
            QTimer.singleShot(1800, self._force_close)
        elif status == 'duplicate':
            self.save_btn.setText("↩ Ya está en tus tarjetas")
            self.save_btn.setStyleSheet(
                "QPushButton#save_btn{background:#4A3600;color:#FFA000;border:none;"
                "border-radius:8px;padding:7px 0;font-size:13px;font-weight:600;}")
            self.status_lbl.setText("Ya existe en tu mazo")
        else:
            self.save_btn.setText("✗ Error — reintentar")
            self.save_btn.setEnabled(True)
            self.save_btn.setStyleSheet(
                "QPushButton#save_btn{background:#7D1010;color:white;border:none;"
                "border-radius:8px;padding:7px 0;font-size:13px;font-weight:600;}")
            self.status_lbl.setText(f"Error: {result.get('message','')[:60]}")

    # ── hover events ─────────────────────────────────────────────────
    def enterEvent(self, event):
        self._hide_timer.stop()
        if not self._pinned and self._word_data:
            self.save_btn.setEnabled(True)   # enable as soon as mouse enters & data ready
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._pinned:
            self._hide_timer.start(self.HOVER_MS)
        super().leaveEvent(event)

    # ── save ─────────────────────────────────────────────────────────
    def _on_save(self):
        # Pin the modal when saving
        self._pinned = True
        self._hide_timer.stop()
        self.status_lbl.setText("💾 Guardando…")

        word = (self._word_data.get('original') or
                self._word_data.get('word') or
                self._current_word or
                self.word_lbl.text())
        if not word:
            print("[SAVE] Sin palabra")
            self.status_lbl.setText("❌ Sin palabra para guardar")
            return
        payload = dict(self._word_data) if self._word_data else {}
        if 'original' not in payload and 'word' not in payload:
            payload['word'] = word
        print(f"[SAVE] → emitiendo save_requested: word='{word}'")
        self.save_btn.setText("Guardando…")
        self.save_btn.setEnabled(False)
        self.save_requested.emit(payload)


class SelectableCaptions(QTextBrowser):
    word_hovered = pyqtSignal(str, QPoint)
    word_clicked = pyqtSignal(str)
    phrase_selected = pyqtSignal(str, QPoint)  # full selection text, QPoint
    
    def __init__(self):
        super().__init__()
        self.setOpenLinks(False)
        self.setMouseTracking(True)
        self.setStyleSheet("""
            QTextBrowser {
                background: transparent; 
                color: white; 
                border: none; 
                selection-background-color: rgba(139, 109, 208, 180);
            }
        """)
        font = QFont("Figtree", 16, QFont.Weight.Bold)
        font.setFamilies(["Figtree", "Segoe UI", "Arial"])
        self.setFont(font)
        self.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.last_hovered_word = ""
        self._is_selecting = False

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        # Don't trigger hover while user is actively selecting text
        if self._is_selecting or self.textCursor().hasSelection():
            self.setExtraSelections([])
            return

        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText().strip()
        
        if word and word.isalpha():
            if word != self.last_hovered_word:
                self.last_hovered_word = word
                selection = QTextBrowser.ExtraSelection()
                selection.cursor = cursor
                selection.format.setBackground(QColor(255, 255, 255, 50))
                selection.format.setForeground(QColor("#C8B8F0"))
                self.setExtraSelections([selection])
                
                rect = self.cursorRect(cursor)
                global_pos = self.viewport().mapToGlobal(rect.topLeft())
                self.word_hovered.emit(word, global_pos)
        else:
            self.last_hovered_word = ""
            self.setExtraSelections([])

    def mousePressEvent(self, event):
        self._is_selecting = event.button() == Qt.MouseButton.LeftButton
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_selecting = False
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.textCursor()
            selected = cursor.selectedText().strip()
            if len(selected.split()) > 1:  # Frase (2+ palabras)
                rect = self.cursorRect(cursor)
                global_pos = self.viewport().mapToGlobal(rect.bottomLeft())
                self.phrase_selected.emit(selected, global_pos)
            elif selected and selected.isalpha():  # Palabra individual (click sin arrastrar)
                pass  # hover ya lo maneja

    def leaveEvent(self, event):
        self._is_selecting = False
        self.last_hovered_word = ""
        self.setExtraSelections([])
        super().leaveEvent(event)


class CaptionManager:
    def __init__(self, max_words=18):
        self.lines = []
        self.current_partial = ""
        self.max_words = max_words

    def add_final(self, text):
        if text:
            words = text.strip().split()
            self.lines.extend(words)
            self._prune()
        self.current_partial = ""

    def update_partial(self, text):
        self.current_partial = text.strip() if text else ""
        self._prune()

    def _prune(self):
        # Limit the number of total words in the history
        if len(self.lines) > self.max_words:
            self.lines = self.lines[-self.max_words:]

    def get_display_text(self):
        # Only show a limited window of words to keep it to ~1-2 lines max
        combined = list(self.lines)
        if self.current_partial:
            combined.extend(self.current_partial.split())
            
        if len(combined) > self.max_words:
            combined = combined[-self.max_words:]
            
        return " ".join(combined)

class SubtitleOverlay(QWidget):
    on_word_clicked = None
    on_word_hovered = None
    on_word_right_clicked = None
    mode_toggled = pyqtSignal()
    lang_changed = pyqtSignal(str) # Emite el código de idioma (en, zh-CN, etc)
    open_settings = pyqtSignal()

    LANGUAGES = [
        {"name": "🇺🇸 Ingles", "code": "en"},
        {"name": "🇪🇸 Español", "code": "es"},
        {"name": "🇨🇳 Chino", "code": "zh-CN"},
        {"name": "🇯🇵 Japones", "code": "ja"},
        {"name": "🇫🇷 Frances", "code": "fr"},
        {"name": "🇩🇪 Alemán", "code": "de"},
        {"name": "🇮🇹 Italiano", "code": "it"},
        {"name": "🇵🇹 Portugués", "code": "pt"},
        {"name": "🇷🇺 Ruso", "code": "ru"},
        {"name": "🇰🇷 Coreano", "code": "ko"}
    ]

    def __init__(self):
        super().__init__()
        self.current_lang_idx = 0
        self.caption_manager = CaptionManager(max_words=18)
        self.custom_tooltip = TranslationTooltip()
        self.initUI()
        self.mining_mode = True
        
    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout()
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 10, 45, 0.88); /* Morado profundo translúcido */
                border: 1px solid rgba(139, 109, 208, 0.25);
                border-radius: 12px;
            }
        """)
        
        self.content_layout = QHBoxLayout(self.container)
        self.content_layout.setContentsMargins(20, 8, 20, 8)
        self.content_layout.setSpacing(15)
        
        # Gear icon (Left/Right?) User said "engranaje la opcion de cmahair idioma"
        # In Windows captions it's on the right.
        
        # Language Pill (Small)
        self.lang_pill = QLabel(self.LANGUAGES[self.current_lang_idx]["name"])
        self.lang_pill.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lang_pill.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.7);
                padding: 4px 10px;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel:hover { background-color: rgba(255, 255, 255, 0.15); }
        """)
        self.lang_pill.mousePressEvent = lambda e: self.open_settings.emit()
        self.content_layout.addWidget(self.lang_pill)

        # Status Label (The "Title" style from image)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-size: 15px; font-weight: 400;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.status_label) 

        # Words Area (Selectable Captions)
        self.captions_view = SelectableCaptions()
        self.content_layout.addWidget(self.captions_view, 1)

        # Gear Icon
        self.settings_btn = QLabel("⚙")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 18px;")
        self.settings_btn.mousePressEvent = lambda e: self.open_settings.emit()
        self.content_layout.addWidget(self.settings_btn)
        
        # Close Area
        self.close_btn = QLabel("✕")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 14px; padding: 4px;")
        self.close_btn.mousePressEvent = lambda e: QApplication.instance().quit()
        self.content_layout.addWidget(self.close_btn)
        
        self.layout.addWidget(self.container)
        self.setLayout(self.layout)
        
        # Sizing and centering (Slimmer like Windows)
        screen = QApplication.primaryScreen().geometry()
        self.resize(1000, 110)
        self.move((screen.width() - 1000) // 2, screen.height() - 140)
        self.oldPos = self.pos()

    def set_status_message(self, msg: str):
        """Muestra un estado inicial con estilo tenue e itálico usando HTML."""
        self.status_label.hide()
        self.captions_view.show()
        self.captions_view.setStyleSheet("QTextBrowser { background: transparent; border: none; }")
        self.captions_view.setHtml(f"<div style='color: rgba(255,255,255,0.5); font-style: italic; font-size: 16px;'>{msg}</div>")


    def set_status(self, text):
        self.captions_view.hide()
        self.status_label.show()
        self.status_label.setText(text)

    def set_partial(self, partial_text):
        if not partial_text: return
        self.caption_manager.update_partial(partial_text)
        self._render_words_ui(self.caption_manager.get_display_text())

    def set_text(self, text):
        if "(" in text or "..." in text:
            self.set_status(text)
            return
            
        if not text: return
        self.caption_manager.add_final(text)
        self._render_words_ui(self.caption_manager.get_display_text())

    def _render_words_ui(self, text):
        self.status_label.hide()
        self.captions_view.show()
        
        # Restaurar estilos intensos (100% opacidad)
        self.captions_view.setStyleSheet("""
            QTextBrowser {
                background: transparent; 
                color: #FFFFFF; 
                border: none; 
                selection-background-color: rgba(139, 109, 208, 180);
            }
        """)

        # Conservar el cursor si no hay selección manual del usuario
        cursor = self.captions_view.textCursor()
        had_selection = cursor.hasSelection()
        
        if not had_selection:
            # Reemplazar texto limpiamente (esto quita el HTML previo)
            self.captions_view.setPlainText(text)
            # Ir al final para auto-scroll
            self.captions_view.moveCursor(QTextCursor.MoveOperation.End)

    def set_mining_mode(self, enabled):
        self.mining_mode = enabled
        if enabled:
            # Opaco casi total (0.98) para que no se trasluzcan subtítulos del video original
            self.container.setStyleSheet("QFrame { background-color: rgba(20, 10, 45, 0.98); border: 2px solid #8B6DD0; border-radius: 20px; }")
        else:
            self.container.setStyleSheet("QFrame { background-color: rgba(20, 10, 45, 0.92); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; }")
        self.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.mode_toggled.emit()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        # Permite arrastrar la ventana, pero idealmente lo haríamos desde una zona limpia
        # Como usamos QTextBrowser, los clicks ahí no llegan a la ventana padre directamente.
        if event.button() == Qt.MouseButton.RightButton:
            self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = SubtitleOverlay()
    overlay.show()
    sys.exit(app.exec())
