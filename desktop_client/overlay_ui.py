import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QTextBrowser, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRect, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QTextCursor

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
                                  Qt.WindowType.Tool |
                                  Qt.WindowType.WindowDoesNotAcceptFocus)
        # NOTE: do NOT set WA_ShowWithoutActivating — it blocks mouse clicks on Windows
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(self.FIXED_W)

        self._word_data   = {}
        self._current_word = ''
        self._pinned      = False
        self._last_pos    = QPoint()

        # ── stylesheet ──────────────────────────────────────────────
        self.setStyleSheet("""
            QWidget#card {
                background: #1E1E24;
                border: 1px solid #3A3A4C;
                border-radius: 14px;
            }
            QLabel#word_lbl  { color: #E8E8F0; font-size:15px; font-weight:700; }
            QLabel#phone_lbl { color: #7E7E93; font-size:11px; font-style:italic; }
            QLabel#trans_lbl { color: #F7B731; font-size:16px; font-weight:700; }
            QLabel#def_lbl   { color: #AEAEB2; font-size:12px; }
            QLabel#status_lbl{ color: #6E6E7E; font-size:11px; }
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

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(16, 12, 16, 14)
        vbox.setSpacing(4)

        # header: word + ✕
        hdr = QHBoxLayout()
        self.word_lbl = QLabel()
        self.word_lbl.setObjectName("word_lbl")
        self.word_lbl.setWordWrap(False)
        self.word_lbl.setMaximumWidth(240)
        hdr.addWidget(self.word_lbl, 1)
        close_lbl = QLabel("✕")
        close_lbl.setStyleSheet("color:#555; font-size:13px; padding:0 2px;")
        close_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        close_lbl.mousePressEvent = lambda _e: self._force_close()
        hdr.addWidget(close_lbl)
        vbox.addLayout(hdr)

        self.phone_lbl = QLabel()
        self.phone_lbl.setObjectName("phone_lbl")
        self.phone_lbl.hide()
        vbox.addWidget(self.phone_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#333; margin:2px 0;")
        sep.setFixedHeight(1)
        vbox.addWidget(sep)

        self.trans_lbl = QLabel("…")
        self.trans_lbl.setObjectName("trans_lbl")
        self.trans_lbl.setWordWrap(True)
        self.trans_lbl.setFixedWidth(self.FIXED_W - 32)
        vbox.addWidget(self.trans_lbl)

        self.def_lbl = QLabel()
        self.def_lbl.setObjectName("def_lbl")
        self.def_lbl.setWordWrap(True)
        self.def_lbl.setFixedWidth(self.FIXED_W - 32)
        self.def_lbl.hide()
        vbox.addWidget(self.def_lbl)

        self.status_lbl = QLabel("Hover para ver • click para guardar")
        self.status_lbl.setObjectName("status_lbl")
        vbox.addWidget(self.status_lbl)

        self.save_btn = QPushButton("＋ Guardar en mis tarjetas")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setFixedWidth(self.FIXED_W - 32)
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save)
        vbox.addWidget(self.save_btn)

        # outer layout just holds the card — no margins so card fills all space
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
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
        return False

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
        """Position ABOVE the given point without calling adjustSize()."""
        screen = QApplication.primaryScreen().availableGeometry()
        h = self.sizeHint().height()   # use sizeHint, not adjustSize()
        x = max(screen.left() + 8,
                min(global_pos.x() - self.FIXED_W // 2,
                    screen.right() - self.FIXED_W - 8))
        y = global_pos.y() - h - 10
        if y < screen.top() + 8:
            y = global_pos.y() + 20    # fallback below if near top
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
        self._place(global_pos)
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
    word_hovered = pyqtSignal(str, object)
    word_clicked = pyqtSignal(str)
    phrase_selected = pyqtSignal(str, object)  # full selection text, QPoint
    
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
        self.setFont(QFont("Figtree", 18, QFont.Weight.Medium))
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
    def __init__(self, max_lines=2):
        self.lines = []
        self.current_partial = ""
        self.max_lines = max_lines

    def add_final(self, text):
        if text:
            self.lines.append(text.strip())
            if len(self.lines) > self.max_lines:
                self.lines.pop(0)
        self.current_partial = ""

    def update_partial(self, text):
        self.current_partial = text.strip() if text else ""

    def get_display_text(self):
        display = list(self.lines)
        if self.current_partial:
            display.append(self.current_partial)
        
        if len(display) > self.max_lines:
            display = display[-self.max_lines:]
            
        return " ".join(display)

class SubtitleOverlay(QWidget):
    on_word_clicked = None
    on_word_hovered = None
    on_word_right_clicked = None
    mode_toggled = pyqtSignal()
    lang_changed = pyqtSignal(str) # Emite el código de idioma (en, zh-CN, etc)

    LANGUAGES = [
        {"name": "🇺🇸 Ingles", "code": "en"},
        {"name": "🇨🇳 Chino", "code": "zh-CN"},
        {"name": "🇯🇵 Japones", "code": "ja"},
        {"name": "🇫🇷 Frances", "code": "fr"}
    ]

    def __init__(self):
        super().__init__()
        self.current_lang_idx = 0
        self.caption_manager = CaptionManager(max_lines=2)
        self.custom_tooltip = TranslationTooltip()
        self.custom_tooltip.save_btn.mousePressEvent = lambda e: self.on_word_clicked(self.custom_tooltip.src_label.text().lower()) if self.on_word_clicked else None
        self.initUI()
        self.mining_mode = True
        
    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.layout = QVBoxLayout()
        self.container = QFrame()
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 25, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        
        self.content_layout = QHBoxLayout(self.container)
        self.content_layout.setContentsMargins(20, 10, 20, 10)
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
        self.lang_pill.mousePressEvent = self.cycle_language
        self.content_layout.addWidget(self.lang_pill)

        # Status Label (The "Title" style from image)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-size: 15px; font-weight: 400;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.status_label, 1) # Expand 1
        
        # Words Area (Selectable Captions)
        self.captions_view = SelectableCaptions()
        self.content_layout.addWidget(self.captions_view, 1)
        self.captions_view.hide()
        
        # Gear Icon
        self.settings_btn = QLabel("⚙")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.setStyleSheet("color: rgba(255,255,255,0.6); font-size: 18px;")
        self.settings_btn.mousePressEvent = self.cycle_language # Shortcut for now
        self.content_layout.addWidget(self.settings_btn)
        
        # Close Area
        self.close_btn = QLabel("✕")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("color: rgba(255,255,255,0.4); font-size: 16px;")
        self.close_btn.mousePressEvent = lambda e: self.close()
        self.content_layout.addWidget(self.close_btn)
        
        self.layout.addWidget(self.container)
        self.setLayout(self.layout)
        
        # Sizing and centering (Slimmer like Windows)
        screen = QApplication.primaryScreen().geometry()
        self.resize(1000, 60)
        self.move((screen.width() - 1000) // 2, screen.height() - 100)
        self.oldPos = self.pos()

    def cycle_language(self, event):
        self.current_lang_idx = (self.current_lang_idx + 1) % len(self.LANGUAGES)
        lang = self.LANGUAGES[self.current_lang_idx]
        self.lang_pill.setText(lang["name"])
        self.lang_changed.emit(lang["code"])
        self.set_status(f"Listo para mostrar subtítulos en directo en {lang['name']}")

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
        
        # Conservar el cursor si no hay selección manual del usuario
        cursor = self.captions_view.textCursor()
        had_selection = cursor.hasSelection()
        
        if not had_selection:
            # Reemplazar texto limpiamente
            self.captions_view.setPlainText(text)
            # Ir al final para auto-scroll
            self.captions_view.moveCursor(QTextCursor.MoveOperation.End)

    def set_mining_mode(self, enabled):
        self.mining_mode = enabled
        if enabled:
            # Prevenir arrastre desde el texto para no interferir con selección
            self.container.setStyleSheet("QFrame { background-color: rgba(26, 15, 53, 0.85); border: 2px solid #8B6DD0; border-radius: 20px; }")
        else:
            self.container.setStyleSheet("QFrame { background-color: rgba(26, 15, 53, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; }")
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
