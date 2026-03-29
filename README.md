# VocabAssistant 🚀
**Domina cualquier idioma con la técnica de "Word Mining" — ya sea leyendo textos o viendo tus videos y películas favoritas.**

VocabAssistant es una plataforma integral diseñada para transformar el contenido nativo (video, audio, libros, imágenes) en un flujo de aprendizaje continuo. Su objetivo principal es facilitar el **Word Mining**: la captura instantánea de vocabulario desconocido en su contexto real para convertirlo en conocimiento duradero. Combina una interfaz web premium de lectura, un cliente de escritorio para subtítulos en vivo y un sistema de repetición espaciada (SM-2) potenciado por IA local.

---

## ✨ Características Principales

### 📖 Modo Lectura (Split-View Web)
- **Interfaz Dividida**: Área de lectura amplia + barra lateral de definiciones persistente y redimensionable.
- **Traducción y Fonética al Instante**: Pasa el ratón sobre cualquier palabra — pronunciación oficial, Pinyin con tonos y segmentación nativa para chino.
- **Audio Nativo Integrado**: Escucha la pronunciación perfecta offline usando la **Web Speech API** (incluye voces neuronales con IA).
- **Selección de Frases**: Subraya oraciones completas y obtén traducciones con contexto semántico.
- **Diseño Premium**: UI moderna con Fraunces, Figtree y animaciones Lottie.

### 🎙️ Cliente de Escritorio — Live Caption Hub *(NUEVO)*
Un cliente nativo PyQt6 que se sincroniza con el dashboard web para transcribir el audio del sistema en tiempo real.

#### 🔗 Sincronización Web-Escritorio (Real-time Status)
- **Latido de Conexión (Heartbeat)**: El asistente se comunica con la web cada 10 segundos.
- **Estado Dinámico**: El dashboard web muestra una burbuja de estado en tiempo real (**Asistente en línea ✓**) cuando detecta que el cliente de escritorio está activo.
- **Lanzamiento Remoto**: Inicia el asistente global con un solo clic directamente desde la interfaz web, sin necesidad de usar la terminal.

#### 🖥️ Subtítulos en Tiempo Real (Vosk STT)
- **Motor de STT local**: [Vosk](https://alphacephei.com/vosk/) — modelos pequeños, sin GPU, sin internet.
- **Ventana deslizante**: Muestra solo las últimas 2 oraciones — sin crecimiento infinito del texto.
- **Sincronización con el audio**: Arquitectura Productor-Consumidor (`queue.Queue` + `QThread`) que desacopla la captura de audio del motor STT para minimizar la latencia.
- **Captura del sistema**: Usa `soundcard` para escuchar la salida de audio del sistema (lo que suena por los altavoces), compatible con Windows.

#### 🔍 Traducción Interactiva (Hover + Selección)
- **Hover sobre palabra → Preview rápido**: Muestra la traducción en una tarjeta flotante que desaparece al quitar el ratón.
- **Selección de texto → Modal fijado**: Selecciona palabras o frases completas para obtener la traducción en un modal interactivo que permanece abierto.
  - Frases largas muestran **solo la traducción** (el original ya es visible en los subtítulos).
  - Palabras individuales muestran: palabra, fonética (IPA/Pinyin), traducción y definición.
- **Modal fijado**: Click dentro del modal → se fija. Click fuera → se cierra.
- **Cancelación de peticiones** (`_hover_request_id`): Si el usuario mueve el ratón rápidamente, las respuestas antiguas se descartan automáticamente.
- **Caché en memoria** (`_translation_cache`): Las palabras ya traducidas se muestran instantáneamente sin nueva petición HTTP.

#### 💾 Minería de Flashcards
- **Botón "＋ Guardar en mis tarjetas"**: Guarda la palabra directamente en el mazo de Django desde el overlay.
- **Feedback visual inmediato**:
  - 🟢 Verde `✓ Guardada en el mazo` → auto-cierre a los 2 segundos.
  - 🟠 Naranja `↩ Ya está en tus tarjetas` → duplicado detectado.
  - 🔴 Rojo `✗ Error — reintentar` → error de conexión.
- Las tarjetas guardadas aparecen inmediatamente en el **Modo Repaso** de la app web.

#### ⚙️ Configuración y Controles del Overlay
- Selector de idioma: `en-us`, `ja`, `zh-cn` — cambia el modelo Vosk en caliente.
- Botón de Mining Mode: activa/desactiva la interacción con el texto.
- Barra de subtítulos redimensionable y arrastrable.

---

### 🤖 Integración IA Local (Ollama)
- **Privacidad Total**: Explicaciones de gramática y ejemplos generados localmente, sin suscripciones.
- **Contexto Avanzado**: La IA explica el matiz de una palabra en el contexto de tu lectura.
- **Generación de Ejemplos**: Crea oraciones contextuales adaptadas al idioma que aprendes.

### 📷 Módulo OCR (Imagen a Texto)
- Sube fotos de libros o documentos → el texto se extrae automáticamente con **Tesseract OCR**.
- Potenciado por `pytesseract` + `Pillow`, con soporte multiidioma configurable.

### 🧠 Modo Repaso (Flashcards y SM-2)
- **Motor SM-2**: Repetición espaciada nativa via `flashcard_service.py`.
- **Tarjetas con volteo 3D** y atajos de teclado para evaluar retención.
- **Diccionario enriquecido**: Definiciones, sinónimos y fonética via `dictionary_service.py` (DictionaryAPI.dev).

---

## 🛠️ Tecnologías Utilizadas

### Backend (Django)
| Tecnología | Uso |
|---|---|
| **Django 6.0.3** | Framework web principal |
| **SQLite** | Base de datos de flashcards |
| `deep-translator` | Traducción veloz sin API keys |
| `pypinyin` | Fonética china con tonos |
| `pytesseract` + `Pillow` | OCR desde imágenes |
| `django-environ` | Variables de entorno |
| `requests` | Conexión a Ollama y diccionarios |

### Cliente de Escritorio *(NUEVO)*
| Tecnología | Uso |
|---|---|
| **PyQt6** | UI nativa del overlay de subtítulos |
| **Vosk** | Motor STT local, sin GPU ni internet |
| **soundcard** | Captura del audio del sistema (loopback) |
| **numpy** | Procesamiento del buffer de audio |
| `threading` + `queue.Queue` | Pipeline Productor-Consumidor para STT |
| `QThread` + `pyqtSignal` | Comunicación segura entre hilos en Qt |
| `requests` | Llamadas HTTP al backend Django |

### Frontend Web
| Tecnología | Uso |
|---|---|
| HTML5 + Vanilla JS | Estructura e interactividad |
| **Web Speech API** | Pronunciación de audio offline |
| **Intl.Segmenter** | Tokenización CJK |
| Google Fonts (DM Sans) | Tipografía estándar para máxima legibilidad |
| `@dotlottie/player-component` | Animaciones Lottie |
| Vanilla CSS | Sistema de diseño profesional "Deep Purple & White" |

---

## 📂 Estructura del Proyecto

```text
VocabAssistant/
├── apps/
│   └── core/
│       ├── models/
│       │   └── flashcard.py          # Modelo SM-2 integrado
│       ├── services/
│       │   ├── ai_service.py         # IA local via Ollama
│       │   ├── dictionary_service.py # Diccionarios externos
│       │   ├── flashcard_service.py  # Motor SM-2
│       │   ├── ocr_service.py        # Wrapper Tesseract
│       │   └── translation_service.py
│       └── views/
│           ├── api_views.py          # Endpoints REST (define, save, etc.)
│           ├── home.py
│           └── review_views.py
├── desktop_client/                   # ← CLIENTE DE ESCRITORIO (NUEVO)
│   ├── main_app.py                   # Orquestador: señales, caché, cancelación
│   ├── overlay_ui.py                 # UI PyQt6: overlay + tooltip interactivo
│   ├── stt_service.py                # Motor Vosk + pipeline de audio
│   └── api_client.py                 # Cliente HTTP al backend Django
├── config/                           # Settings y configuración
├── static/                           # Assets globales y animaciones Lottie
├── templates/                        # Vistas Django
├── DESKTOP_CLIENT.md                 # Documentación técnica del cliente
└── requirements.txt
```

---

## ⚙️ Instalación y Configuración

### 1. Clonar y Preparar el Entorno
```bash
cd VocabAssitant
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Instalar Tesseract OCR *(para el módulo de imagen)*
1. Descarga: [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
2. Instala en la ruta por defecto: `C:\Program Files\Tesseract-OCR\tesseract.exe`

### 3. Instalar Ollama *(para IA local)*
```bash
# Después de instalar Ollama desde ollama.com:
ollama run llama3.2:latest
```
Deja Ollama corriendo en segundo plano mientras uses VocabAssistant.

### 4. Migraciones y Servidor Web
```bash
python manage.py migrate
python manage.py runserver
```
Abre `http://127.0.0.1:8000` en tu navegador.

### 5. Cliente de Escritorio *(Live Captions — NUEVO)*

#### Requisitos adicionales
```bash
pip install PyQt6 soundcard vosk numpy requests
```

#### Descarga el modelo Vosk (inglés, ~50MB)
```bash
# Vosk descarga el modelo automáticamente en el primer uso.
# Para descargarlo manualmente:
python -c "import vosk; vosk.Model(lang='en-us')"
```

#### Ejecutar el overlay
```bash
# Con el servidor Django corriendo en http://127.0.0.1:8000:
python desktop_client/main_app.py
```

> **Flujo de uso:**
> 1. Abre cualquier video (YouTube, Netflix, podcast, reunión).
> 2. El overlay transcribe el audio del sistema en tiempo real.
> 3. Pasa el ratón sobre cualquier palabra para ver su traducción al instante.
> 4. Selecciona texto para traducir frases completas en un modal fijado.
> 5. Haz clic en **"＋ Guardar en mis tarjetas"** — aparece en tu Modo Repaso web.

---

## 🚀 Próximas Mejoras (Roadmap)

- **Cola de Contexto para IA Local**: Añadir un botón secundario en el modal de subtítulos ("Enviar a IA") para mandar palabras complejas a una cola de procesamiento. Esto permitirá realizar una indagación profunda (etimología, matices de uso, 5 ejemplos adicionales) mediante la IA local sin interrumpir el flujo de visualización de la película o video.
- **Sincronización de Audio Cloud**: Opción para guardar el fragmento de audio real de la película en la tarjeta de repaso.
- **Modo Inmersivo de Lectura**: Soporte para formatos EPUB y PDF con minería directa.

## 👤 Autor
Desarrollado con pasión para mejorar el viaje autodidacta en el aprendizaje de idiomas. 🌍
