import pytesseract
from PIL import Image
import os

class OCRService:
    # Ruta común en Windows. Se puede configurar vía variable de entorno.
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Mapeo de códigos de idioma a códigos de Tesseract
    TESSERACT_LANG_MAP = {
        'en': 'eng',
        'es': 'spa',
        'fr': 'fra',
        'de': 'deu',
        'it': 'ita',
        'pt': 'por',
        'zh-CN': 'chi_sim',
        'ja': 'jpn',
        'ko': 'kor',
        'ru': 'rus'
    }

    @classmethod
    def extract_text(cls, image_file, lang='en'):
        """
        Extrae texto de un archivo de imagen usando Tesseract OCR.
        """
        # Intentar configurar la ruta si existe
        if os.path.exists(cls.TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = cls.TESSERACT_PATH
        
        # Obtener el código de tesseract, por defecto inglés
        tess_lang = cls.TESSERACT_LANG_MAP.get(lang, 'eng')
        
        try:
            image = Image.open(image_file)
            text = pytesseract.image_to_string(image, lang=tess_lang)
            return text.strip()
        except Exception as e:
            print(f"Error en OCR: {e}")
            return None
