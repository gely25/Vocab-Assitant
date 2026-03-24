import pytesseract
from PIL import Image
import os

class OCRService:
    # Ruta común en Windows. Se puede configurar vía variable de entorno.
    TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    @classmethod
    def extract_text(cls, image_file):
        """
        Extrae texto de un archivo de imagen usando Tesseract OCR.
        """
        # Intentar configurar la ruta si existe
        if os.path.exists(cls.TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = cls.TESSERACT_PATH
        
        try:
            image = Image.open(image_file)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"Error en OCR: {e}")
            return None
