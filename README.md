# VocabAssistant 🚀
**Tu compañero inteligente para la lectura y el aprendizaje de idiomas.**

VocabAssistant es una aplicación web diseñada para transformar la lectura de textos en idiomas extranjeros en una experiencia fluida y productiva. Combina herramientas de traducción en tiempo real, reconocimiento de texto desde imágenes (OCR), un sistema de repetición espaciada (SM-2), y **ahora cuenta con una integración de Inteligencia Artificial Local (Ollama) para explicar contextos y dar ejemplos nativos.**

---

## ✨ Características Principales y Funciones

### 📖 Modo Lectura (Split-View)
- **Interfaz Dividida**: Un área de lectura amplia y una barra lateral de definiciones persistente y redimensionable para una experiencia sin interrupciones.
- **Traducción y Fonética al Instante**: Pasa el ratón o selecciona una palabra para ver su pronunciación oficial (incluye Pinyin con tonos y segmentación de palabras nativa para el Chino).
- **Audio Nativo Integrado**: Escucha la pronunciación perfecta en cualquier idioma al instante utilizando el motor de audio de tu dispositivo (vía la **Web Speech API** integrada), completamente offline e incluyendo soporte a voces Neuronales con IA.
- **Selección de Frases**: Subraya oraciones completas generadas por Intl.Segmenter y obtén traducciones de contexto.
- **Diseño Premium**: Interfaz moderna usando tipografías premium (Fraunces y Figtree) con animaciones Lottie integradas.

### 🤖 Integración IA Local (Ollama)
- **Privacidad Total**: Las explicaciones de gramática y los ejemplos se generan en tu propia máquina mediante modelos de lenguaje (LLM) locales, sin suscripciones ni fugas de datos.
- **Contexto Avanzado**: Pide a la IA que te explique el matiz de una palabra específica en el contexto de tu lectura.
- **Traducciones Híbridas (Oración por Oración)**: La IA genera la explicación nativa, la formatea como oraciones individuales y luego el sistema las traduce y las presenta en la UI con formato de "acordeón/subtítulos" interactivos debajo de cada bloque de texto.
- **Generación de Ejemplos**: Crea oraciones contextuales adaptadas al idioma que estás aprendiendo.

### 📷 Módulo OCR (Imagen a Texto)
- **Extracción Inteligente**: Sube fotos de libros o documentos y el sistema extraerá el texto automáticamente para que puedas leerlo y traducirlo en la app.
- **Microservicio `ocr_service.py`**: Potenciado por el motor Tesseract OCR (vía `pytesseract`) capaz de detectar múltiples idiomas configurables y mapear códigos de idioma de manera eficiente.

### 🧠 Modo Repaso (Flashcards y SM-2)
- **Sistema Leitner / SM-2**: Motor de repetición espaciada nativo gestionado por `flashcard_service.py`.
- **Diccionario Enriquecido**: Obtén definiciones, distintos contextos, sinónimos y fonética a través de `dictionary_service.py` (consumiendo `DictionaryAPI.dev`).
- **Tarjetas Interactivas**: Flashcards fluidas con efecto de volteo 3D y atajos para evaluar rápidamente el grado de retención y programar el próximo repaso.

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Framework**: Django 6.0.3 (Python 3.12+)
- **Base de Datos**: SQLite (por defecto, ligero y configurable)
- **Librerías Clave**: 
  - `requests` (Conexión asíncrona a modelos LLM locales).
  - `deep-translator` (Traducción veloz y libre de API keys).
  - `pypinyin` (Para la correcta restitución fonética china con todos sus tonos).
  - `pytesseract` y `Pillow` (Procesamiento de imágenes y OCR).
  - `django-environ` (Variables de entorno).

### Frontend
- **Estructura Arquitectónica**: HTML5, Vanilla JavaScript (Fetch API).
- **Motor de Pronunciación**: Usa la **Web Speech API** del navegador (`window.speechSynthesis`) en lugar de servicios de pago para lograr respuestas inmediatas de audio multilingüe.
- **Segmentación Inteligente**: Soporte para tokenización de caracteres CJK mediante la moderna API web `Intl.Segmenter`.
- **Estética y Visuales**: Web Components (`@dotlottie/player-component`), Variables Vanilla CSS, y Google Fonts (Fraunces & Figtree).

---

## 📂 Estructura Arquitectónica del Proyecto

La aplicación separa las responsabilidades en su app central `core`:

```text
VocabAssistant/
├── apps/
│   └── core/                 
│       ├── models/           
│       │   └── flashcard.py  # Modelo SM-2 integrado
│       ├── services/         
│       │   ├── ai_service.py           # Conexión local a Ollama para generación de contexto
│       │   ├── dictionary_service.py   # Consultas a diccionarios externos
│       │   ├── flashcard_service.py    # SM-2 y revisión inteligente
│       │   ├── ocr_service.py          # Wrapper de Pytesseract
│       │   └── translation_service.py  # Traducciones rápidas
│       └── views/            
│           ├── api_views.py     
│           ├── home.py          
│           └── review_views.py  
├── config/                   # Configuración y Settings
├── static/                   # Recursos globales y animaciones (loading.lottie)
├── templates/                # Motor de vistas de Django
└── requirements.txt          # Dependencias
```

---

## ⚙️ Instalación y Configuración

Sigue estos pasos detallados para configurar y levantar localmente todo el ecosistema de VocabAssistant.

### 1. Clonar y Preparar el Entorno Python
```bash
# Entrar al directorio del proyecto
cd VocabAssitant

# Crear y activar un entorno virtual (Windows)
python -m venv venv
.\venv\Scripts\activate

# Instalar dependencias backend
pip install -r requirements.txt
```

### 2. Instalar Tesseract OCR (Requerido para leer imágenes)
La extracción de texto desde capturas necesita tener instalado Tesseract nativamente.
1. **Descarga el instalador de Windows**: [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki).
2. **Instala forzosamente en la ruta por defecto**: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
3. El módulo `ocr_service.py` interceptará automáticamente este ejecutable. Si lo instalaste en otro lado, revisa ese archivo para cambiar la ruta.

### 3. Instalar Ollama (Obligatorio para la IA / Explicaciones)
VocabAssistant depende de Ollama para brindar ejemplos contextuales y explicaciones gramaticales generadas nativamente, cuidando la privacidad mediante el uso de LLMs 100% locales en tu PC.

1. **Descarga Oficial**: Instala Ollama desde su sitio web [ollama.com](https://ollama.com).
2. **Despliega el Modelo**: Una vez instalado, abre tu terminal principal (PowerShell o CMD) y descarga el motor de Llama 3.2. Ejecuta el comando:
   ```bash
   ollama run llama3.2:latest
   ```
   *Nota: La primera descarga pesa unos GB. Cuando el comando termine y te salude, significa que ya está listo.*
3. Tu backend de Django en `VocabAssistant` está programado en `settings.py` para consultar la dirección estándar HTTP que usa este servicio (`http://127.0.0.1:11434/api/generate`). **Debes dejar corriendo Ollama en segundo plano** mientras uses VocabAssistant.

### 4. Migraciones y Ejecución del Servidor
Con tu motor OCR y tu LLM local encendidos, arranca el servidor web.

```bash
# Sincronizar y generar la base de datos de tarjetas (SQLite)
python manage.py migrate

# Arrancar el servidor de VocabAssistant
python manage.py runserver
```

Abre tu navegador en `http://127.0.0.1:8000` y ¡disfruta aprendiendo idiomas asistido por IA Local!

---

## 👤 Autor
Desarrollado con pasión para mejorar el viaje en el aprendizaje autodidacta de idiomas. 🌍
