import requests

class VocabAPIClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        
    def get_definition(self, word, source_lang="en", target_lang="es"):
        """Obtiene la traducción y definición de una palabra desde el servidor Django"""
        try:
            params = {'word': word, 'source': source_lang, 'target': target_lang}
            response = requests.get(f"{self.base_url}/define/", params=params, timeout=3)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"API Error (get_definition): {e}")
            return None
            
    def save_flashcard(self, word_data):
        """Guarda una palabra en el mazo del usuario"""
        try:
            response = requests.post(f"{self.base_url}/save/", json=word_data, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"API Error (save_flashcard): {e}")
            return False

    def get_stats(self):
        """Obtiene las estadísticas de estudio para mostrar en el overlay"""
        try:
            response = requests.get(f"{self.base_url}/api/stats/", timeout=5)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"API Error (get_stats): {e}")
            return None
