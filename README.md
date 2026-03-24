# VocabAssistant 🚀
**Tu compañero inteligente para la lectura y el aprendizaje de idiomas.**

VocabAssistant es una aplicación web diseñada para transformar la lectura de textos en idiomas extranjeros en una experiencia fluida y productiva. Combina herramientas de traducción en tiempo real, reconocimiento de texto desde imágenes (OCR) y un sistema de repetición espaciada (SM-2) para ayudarte a memorizar vocabulario nuevo de forma efectiva.

---

## ✨ Características Principales

### 📖 Modo Lectura (Split-View)
- **Interfaz Dividida**: Un área de lectura amplia y una barra lateral de definiciones persistente y redimensionable.
- **Traducción al Hover**: Solo pasa el ratón sobre una palabra para ver su traducción y fonética instantáneamente.
- **Selección de Frases**: Subraya frases completas para obtener traducciones precisas sin distracciones.
- **Diseño Premium**: Interfaz en modo oscuro (Deep Navy/Slate) con animaciones fluidas y estética profesional.

### 📷 Módulo OCR (Imagen a Texto)
- **Extracción Inteligente**: Sube fotos de libros o documentos y el sistema extraerá el texto automáticamente para que puedas leerlo y traducirlo en la app.
- **Basado en Tesseract**: Potenciado por el motor Tesseract OCR para una alta precisión.

### 🧠 Modo Repaso (Flashcards SM-2)
- **Repetición Espaciada**: Utiliza el algoritmo SM-2 para programar tus repasos basándose en tu nivel de retención.
- **Flashcards Premium**: Tarjetas interactivas con efecto de volteo y diseño unificado.

---

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django (Python 3.12+)
- **Frontend**: Vanilla JavaScript (ES6+), CSS Grid/Flexbox
- **APIs & Librerías**:
  - `deep-translator` (Google Translate Engine)
  - `pytesseract` & `Pillow` (OCR Engine)
  - `DictionaryAPI.dev` (Definiciones y Fonética)

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
Para que la funcionalidad de "Imagen a Texto" funcione en Windows:
1.  **Descarga el instalador**: [Tesseract OCR Windows](https://github.com/UB-Mannheim/tesseract/wiki).
2.  **Instala en la ruta por defecto**: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
3.  El sistema ya está configurado para buscar el ejecutable en esa ruta.

### 3. Migraciones y Base de Datos
```bash
python manage.py migrate
```

---

## 🏃 Cómo Ejecutar

1.  Asegúrate de que el entorno virtual esté activo.
2.  Inicia el servidor de desarrollo:
    ```bash
    python manage.py runserver
    ```
3.  Abre tu navegador en `http://127.0.0.1:8000`.

---

## 📂 Estructura del Proyecto

- `apps/core/`: Lógica principal (vistas, modelos, servicios).
  - `services/`: Capa de servicios para OCR, Diccionarios y Traducción.
- `templates/core/`: Plantillas HTML (Modo Lectura y Modo Repaso).
- `config/`: Configuración global de Django.

---

## 👤 Autor
Desarrollado con pasión para mejorar el aprendizaje autodidacta. 🌍
