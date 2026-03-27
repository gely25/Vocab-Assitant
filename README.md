# VocabAssistant 🚀
**Tu compañero inteligente para la lectura y el aprendizaje de idiomas.**

VocabAssistant es una aplicación web diseñada para transformar la lectura de textos en idiomas extranjeros en una experiencia fluida y productiva. Combina herramientas de traducción en tiempo real, reconocimiento de texto desde imágenes (OCR) y un sistema de repetición espaciada (SM-2) para ayudarte a memorizar vocabulario nuevo de forma efectiva.

---

## ✨ Características Principales y Funciones

### 📖 Modo Lectura (Split-View)
- **Interfaz Dividida**: Un área de lectura amplia y una barra lateral de definiciones persistente y redimensionable para una experiencia sin interrupciones.
- **Traducción al Hover**: Solo pasa el ratón sobre una palabra para ver su traducción y fonética instantáneamente.
- **Selección de Frases**: Subraya frases completas para obtener traducciones precisas usando `deep-translator`.
- **Diseño Premium**: Interfaz moderna (recientemente rediseñada) usando tipografías premium (Fraunces y Figtree) con un tema claro sofisticado y colores de acento sutiles (lila/lavanda), permitiendo una excelente legibilidad sin distracciones.

### 📷 Módulo OCR (Imagen a Texto)
- **Extracción Inteligente**: Sube fotos de libros o documentos y el sistema extraerá el texto automáticamente para que puedas leerlo y traducirlo en la app.
- **Microservicio `ocr_service.py`**: Potenciado por el motor Tesseract OCR (vía `pytesseract`) capaz de detectar múltiples idiomas configurables y mapear códigos de idioma de manera eficiente.

### 🧠 Modo Repaso (Flashcards y SM-2)
- **Sistema Leitner / SM-2**: Motor de repetición espaciada nativo. La lógica de cálculo de intervalos, factor de facilidad (`ease_factor`) y retención está encapsulada directamente en el modelo de base de datos y gestionada por `flashcard_service.py`.
- **Diccionario Enriquecido**: Obtén definiciones, distintos contextos, sinónimos y fonética a través de `dictionary_service.py` (consumiendo `DictionaryAPI.dev` y apoyado en utilidades de red).
- **Tarjetas Interactivas**: Flashcards fluidas con efecto de volteo 3D y atajos para evaluar rápidamente el grado de retención y programar el próximo repaso automáticamente.

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Framework**: Django 6.0.3 (Python 3.12+)
- **Base de Datos**: SQLite (por defecto, ligero y configurable)
- **Librerías Clave**: 
  - `deep-translator` (Traducción de Google Translate veloz y libre de API keys).
  - `pytesseract` y `Pillow` (Extracción de texto y procesamiento de imágenes).
  - `beautifulsoup4` y `requests` (Consultas externas y herramientas de scraping/parsing).
  - `django-environ` (Manejo robusto de variables de entorno y configuración sensible).

### Frontend
- **Estructura y Estilos**: HTML5 Semántico, Vanilla CSS (CSS Grid, Flexbox, variables CSS para el sistema de diseño visual).
- **Interactividad**: Vanilla JavaScript (ES6+), Fetch API para peticiones asíncronas fluidas (traducción al vuelo, OCR y creación de tarjetas).
- **Integraciones Visuales**: Google Fonts (Fraunces Serif para elegancia, Figtree Sans para gran legibilidad).

---

## 📂 Estructura Arquitectónica del Proyecto

La aplicación sigue principios de diseño orientados al dominio, separando claramente las responsabilidades en la app principal `core`:

```text
VocabAssistant/
├── apps/
│   └── core/                 # Aplicación central de la plataforma
│       ├── models/           # Lógica de datos (Models)
│       │   └── flashcard.py  # Modelo Flashcard con lógica SM-2 embebida (`review()` state machine)
│       ├── services/         # Capa de Lógica de Negocio y API wrappers
│       │   ├── dictionary_service.py   # Interacciones con DictionaryAPI
│       │   ├── flashcard_service.py    # Gestión y agrupación de tarjetas de repaso
│       │   ├── ocr_service.py          # Wrapper de Pytesseract para extracción de texto
│       │   └── translation_service.py  # Adaptador de traducción para deep-translator
│       └── views/            # Controladores web y API
│           ├── api_views.py     # Endpoints JSON (Traducción AJAX, OCR, Guardado de Flashcards)
│           ├── home.py          # Renderizado y contexto de la vista de lectura principal
│           └── review_views.py  # Renderizado y lógica de presentación para los repasos
├── config/                   # Carpeta de configuración de Django (settings, urls, asgi/wsgi)
├── templates/
│   └── core/                 # Componentes de presentación (home.html, review.html)
└── requirements.txt          # Gestión de dependencias (bs4, django, pytesseract, etc.)
```

---

## ⚙️ Instalación y Configuración

Sigue estos pasos para poner en marcha el proyecto en tu entorno local:

### 1. Clonar y Preparar el Entorno
```bash
# Entrar al directorio
cd VocabAssitant

# Crear un entorno virtual
python -m venv venv

# Activar el entorno virtual (Windows)
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Instalar Tesseract OCR (Requerido para el OCR)
Para que la funcionalidad de "Imagen a Texto" funcione correctamente en Windows:
1.  **Descarga el instalador**: [Tesseract OCR Windows](https://github.com/UB-Mannheim/tesseract/wiki).
2.  **Instala en la ruta por defecto**: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
3.  El módulo `ocr_service.py` ya está diseñado para ubicar esta ruta de forma transparente.

### 3. Migraciones y Ejecución del Servidor
```bash
# Sincronizar modelos con la base de datos
python manage.py migrate

# Arrancar el servidor
python manage.py runserver
```

Abre tu navegador web en `http://127.0.0.1:8000` para comenzar.

---

## 👤 Autor
Desarrollado con pasión para mejorar el viaje en el aprendizaje autodidacta de idiomas. 🌍
