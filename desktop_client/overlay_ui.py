import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QTextBrowser, QPushButton
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QRect, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QTextCursor

class TranslationTooltip(QFrame):
    save_requested = pyqtSignal(dict)   # emits full word_data dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._word_data = {}

        self.setStyleSheet("""
            QFrame {
                background-color: #1C1C1E;
                border: 1px solid #3A3A3C;
                border-radius: 12px;
            }
            QLabel#word_lbl  { color: #E0E0E0; font-size: 15px; font-weight: 700; }
            QLabel#phone_lbl { color: #8E8E93; font-size: 12px; font-style: italic; }
            QLabel#trans_lbl { color: #F7B731; font-size: 15px; font-weight: 700; }
            QLabel#def_lbl   { color: #AEAEB2; font-size: 12px; }
            QPushButton#save_btn {
                background-color: #8B6DD0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 6px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton#save_btn:hover { background-color: #A98BE8; }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(6)

        # Row 1: word + close btn
        row1 = QHBoxLayout()
        self.word_lbl = QLabel()
        self.word_lbl.setObjectName("word_lbl")
        row1.addWidget(self.word_lbl, 1)
        close = QLabel("✕")
        close.setStyleSheet("color:#555; font-size:12px;")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.mousePressEvent = lambda e: self.hide()
        row1.addWidget(close)
        outer.addLayout(row1)

        # Phonetic (IPA / pinyin)
        self.phone_lbl = QLabel()
        self.phone_lbl.setObjectName("phone_lbl")
        self.phone_lbl.hide()
        outer.addWidget(self.phone_lbl)

        # Divider
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background:#333; margin: 2px 0;")
        sep.setFixedHeight(1)
        outer.addWidget(sep)

        # Translation
        self.trans_lbl = QLabel()
        self.trans_lbl.setObjectName("trans_lbl")
        outer.addWidget(self.trans_lbl)

        # Definition snippet
        self.def_lbl = QLabel()
        self.def_lbl.setObjectName("def_lbl")
        self.def_lbl.setWordWrap(True)
        self.def_lbl.setMaximumWidth(320)
        self.def_lbl.hide()
        outer.addWidget(self.def_lbl)

        # Save button
        self.save_btn = QPushButton("＋ Guardar en mis tarjetas")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self._on_save)
        outer.addWidget(self.save_btn)

        self.hide_timer = QTimer()
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

    def _on_save(self):
        if self._word_data:
            self.save_requested.emit(self._word_data)
            self.save_btn.setText("✓ Guardada")
            self.save_btn.setEnabled(False)

    def show_loading(self, word, global_pos):
        self.hide_timer.stop()
        self._word_data = {}
        self.word_lbl.setText(word)
        self.phone_lbl.hide()
        self.trans_lbl.setText("Buscando traducción...")
        self.def_lbl.hide()
        self.save_btn.setText("＋ Guardar en mis tarjetas")
        self.save_btn.setEnabled(False)
        self.adjustSize()
        self._reposition(global_pos)
        self.show()

    def show_data(self, word_data, global_pos):
        self.hide_timer.stop()
        self._word_data = word_data
        self.word_lbl.setText(word_data.get('original', word_data.get('word', '')))
        phonetic = word_data.get('phonetic', '')
        if phonetic:
            self.phone_lbl.setText(phonetic)
            self.phone_lbl.show()
        else:
            self.phone_lbl.hide()
        self.trans_lbl.setText(word_data.get('translation', '—'))
        definition = word_data.get('definition', '')
        if definition and len(definition) > 5:
            self.def_lbl.setText(definition[:140] + ('...' if len(definition) > 140 else ''))
            self.def_lbl.show()
        else:
            self.def_lbl.hide()
        self.save_btn.setText("＋ Guardar en mis tarjetas")
        self.save_btn.setEnabled(True)
        self.adjustSize()
        self._reposition(global_pos)
        self.show()

    def _reposition(self, global_pos):
        screen = QApplication.primaryScreen().geometry()
        x = global_pos.x()
        y = global_pos.y() + 30
        if x + self.width() > screen.right() - 10:
            x = screen.right() - self.width() - 10
        if y + self.height() > screen.bottom() - 10:
            y = global_pos.y() - self.height() - 10
        self.move(x, y)

    def enterEvent(self, event):
        self.hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hide_timer.start(800)   # 800ms to comfortably reach the tooltip
        super().leaveEvent(event)


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
