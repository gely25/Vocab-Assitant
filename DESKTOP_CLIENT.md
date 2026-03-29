# VocabAssistant — Desktop Live Caption Client

> Sistema de subtítulos en tiempo real con traducción interactiva por palabra, construido en PyQt6 + Vosk.

---

## ¿Qué hace?

Es una burbuja flotante que se superpone sobre cualquier ventana (YouTube, Netflix, etc.) y transcribe el audio del sistema en tiempo real, al estilo Windows Live Captions, permitiendo hacer clic o pasar el cursor sobre cualquier palabra para ver su traducción al instante y guardarla como flashcard.

---

################################# Problemas Resueltos ################################################

### 1. Crashes al iniciar (`faster-whisper` incompatible)
- **Problema**: `faster-whisper` requería instrucciones AVX/AVX-512 del procesador. En tu CPU eso causaba un **crash fatal a nivel C** (no manejable por Python), cerrando la app silenciosamente sin ningún mensaje de error.
- **Solución**: Migración completa a **Vosk** (motor STT offline, ~40MB, compatible con cualquier procesador desde 2008). No requiere GPU ni instrucciones especiales.

### 2. Audio que se perdía / transcripción asíncrona
- **Problema**: El hilo de reconocimiento de voz `AcceptWaveform()` bloqueaba la captura de audio, causando pérdida de frames (`data discontinuity`) y que el texto se retrasara varios segundos respecto al video.
- **Solución**: Arquitectura **Productor-Consumidor** con `queue.Queue`. Un hilo dedicado **solo graba audio** (sin interrupciones), y el hilo principal procesa los fragmentos desde la cola, garantizando cero pérdida de frames.

### 3. Texto infinito (modo consola)
- **Problema**: El texto se acumulaba indefinidamente como un log, haciendo crecer el overlay horizontalmente hasta salirse de la pantalla.
- **Solución**: Se implementó un **`CaptionManager` con Sliding Window**. Mantiene exactamente 2 oraciones finales + la oración parcial actual. Las oraciones viejas se eliminan automáticamente del buffer.

### 4. Hover/Click imposibles por re-renderizado violento
- **Problema**: La UI creaba y destruía todos los `QLabel` individuales 6 veces por segundo, haciendo imposible que el ratón se "enganchara" a una palabra. Además causaba `TypeError: sipBadCatcherResult` (crash de memoria PyQt).
- **Solución**: Se reemplazó el sistema de `WordLabel` + `FlowLayout` por **`SelectableCaptions(QTextBrowser)`**, que permite:
  - Selección nativa de texto (drag para seleccionar frases completas).
  - Detección de la palabra bajo el cursor vía `QTextCursor.WordUnderCursor`.
  - Resaltado visual sin recrear ningún widget.

### 5. Tooltip de traducción que desaparecía
- **Problema**: La tarjeta de traducción se ocultaba al instante (en el `leaveEvent` del `WordLabel`) antes de poder hacer clic en el botón `➕`.
- **Solución**: La `TranslationTooltip` ahora usa un `QTimer` de 200ms. Cuando el ratón entra en la tarjeta, el timer se cancela, manteniéndola abierta permanentemente hasta que el ratón salga de ella.

### 6. Traducciones fallando silenciosamente
- **Problema**: Al hacer hover, si el backend Django tardaba o fallaba, la tarjeta nunca actualizaba su texto y se veía "rota" sin ningún feedback.
- **Solución**: La tarjeta muestra **"Cargando..."** de forma inmediata y síncrona al hacer hover. La traducción llega asíncronamente desde un hilo de fondo y actualiza el texto cuando está lista, mostrando `(Error)` o `(No encontrado)` en caso de fallo.
### 7. DDoS al servidor y bloqueos `Read timed out` (Debounce)
- **Problema**: Pasar el ratón por el texto enviaba docenas de requests HTTP simultáneos a Django (`/define/`), agotando el pool de conexiones. Esto causaba "Read timed out" y que los clics de *Guardar* se quedaran encolados al infinito sin enviar.
- **Solución**: Implementación de un patrón "Debounce" con `QTimer` (450ms). El cliente espera a que el cursor se detenga sobre una palabra o selección antes de disparar un único request HTTP. Además, en `api_client.py` se separó una `requests.Session()` exclusiva para `/save/`, de manera que el guardado siempre viaja por un túnel libre garantizado.

### 8. Crashes y corrupción de memoria (`sipBadCatcherResult`)
- **Problema**: El hilo de STT o el de descargas intentaban comunicar posiciones de pantalla (`QPoint`) al hilo principal (UI thread) usando un tipo genérico de Python (`object` en `pyqtSignal`). En PyQt6, enviar un wrapper de puntero C++ indiscriminado por una conexión encolada daña la memoria.
- **Solución**: Tipado seguro y estricto en el puente de hilos: `pyqtSignal(dict, QPoint, bool)`. PyQt detecta el tipo C++ y se encarga de serializarlo sanamente antes de enviarlo al Event Loop principal.

### 9. Clics nulos (Botón inerte en Windows)
- **Problema**: La señal de clic no llegaba nunca tras un rediseño de UI porque se estaba instanciando erróneamente una lambda con referencias muertas, y porque el atributo de ventana `Qt.WindowDoesNotAcceptFocus` bloqueaba todo input de usuario en el modal.
- **Solución**: Se eliminó la etiqueta restrictiva del OS y se arregló el sistema de propagación de eventos (`super().eventFilter()`). La interfaz ahora recibe y procesa interacciones correctamente sobre el overlay en Windows sin robar foco activo.

### 10. Subtítulos que "bailan", se cortan o se amontonan
- **Problema**: Inicialmente, borrar palabras viejas una por una causaba un "temblor" horizontal constante (jitter) que hacía imposible leer. Además, el texto a veces se desbordaba en 3 líneas o se le cortaba la "cabeza" o la "cola" a las letras (descenders/ascenders).
- **Solución**: **Discrete Rolling Captions (Desplazamiento por Línea)**.
  - **Lógica de Ventana Discreta**: El `CaptionManager` ahora segmenta el buffer de palabras en "líneas virtuales" de 12 palabras. Solo se muestran las últimas 2 líneas unidas por un `\n`.
  - **Estabilidad Total**: Mientras hablas, la línea actual está fija y la de abajo se va llenando. Solo cuando se llena la segunda línea, la primera desaparece y la segunda "sube" a su lugar en un solo salto limpio. No hay movimiento palabra-a-palabra.
  - **Fijación Geométrica**: El área de texto se fijó a **65px de alto**. Esto es el tamaño exacto para 2 líneas de 15px con holgura para letras como la 'g', 'p', 'y', haciendo físicamente imposible que asome una tercera línea por debajo.
  - **Alineación Top-Left**: Se ancló el texto a la esquina superior izquierda (`AlignTop | AlignLeft`) para que el punto de inicio de lectura sea siempre el mismo.

---

## Arquitectura

```
main_app.py (Orquestador)
│
├── STTService (QThread)
│   ├── audio_worker Thread   ─── captura loopback del sistema (soundcard)
│   ├── queue.Queue           ─── buffer de fragmentos de audio crudos
│   └── Vosk KaldiRecognizer  ─── STT offline, emite partiales + frases completas
│
├── SubtitleOverlay (QWidget, siempre encima)
│   ├── SelectableCaptions (QTextBrowser)
│   │   ├── word_hovered signal → QPoint  (hover = mostrar tooltip)
│   │   └── word_clicked signal → str     (click = guardar flashcard)
│   ├── TranslationTooltip (QFrame flotante)
│   │   ├── show_loading()   → aparece inmediatamente
│   │   └── show_translation() → actualiza con traducción real
│   └── CaptionManager
│       ├── add_final(text)       → agrega palabras finales al buffer circular
│       ├── update_partial(text)  → actualiza la frase en progreso
│       └── get_display_text()    → segmenta en líneas y retorna ventana de 2 líneas (Rolling Window)
│
└── HoverWorker (QObject)
    └── translation_ready signal → actualiza tooltip desde hilo de fondo de forma thread-safe
```

---

## Instalación

```bash
# Activar entorno virtual
venv\Scripts\activate

# Instalar dependencias del cliente
pip install PyQt6 soundcard numpy vosk
```

**Para ejecutar (requiere el servidor Django corriendo):**
```bash
# Terminal 1
python manage.py runserver

# Terminal 2
python desktop_client/main_app.py
```

---

## Archivos clave

| Archivo | Rol |
|---|---|
| `desktop_client/main_app.py` | Punto de entrada, orquesta todos los módulos |
| `desktop_client/stt_service.py` | Motor STT (Vosk) con cola de audio multi-hilo |
| `desktop_client/overlay_ui.py` | UI del overlay (ventana flotante, captions, tooltip) |
| `desktop_client/api_client.py` | Cliente HTTP para comunicarse con el backend Django |
