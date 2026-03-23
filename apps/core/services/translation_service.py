from deep_translator import GoogleTranslator

class TranslationService:
    @staticmethod
    def translate(text, target_lang='es', source_lang='auto'):
        try:
            return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        except Exception as e:
            # En un entorno real, loguearíamos el error
            return f"Error al traducir: {str(e)}"
