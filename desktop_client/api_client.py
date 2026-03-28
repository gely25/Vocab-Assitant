import requests

class VocabAPIClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self._save_session = requests.Session()
        
    def get_definition(self, word, source_lang="en", target_lang="es"):
        """Obtiene la traducción y definición de una palabra desde el servidor Django"""
        try:
            params = {'word': word, 'source': source_lang, 'target': target_lang}
            response = requests.get(f"{self.base_url}/define/", params=params, timeout=3)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            if 'timed out' not in str(e).lower():
                print(f"API Error (get_definition): {e}")
            return None
            
    def save_flashcard(self, word_data):
        """Guarda una palabra en el mazo del usuario"""
        try:
            # Usamos una sesión dedicada para que los timeouts del hover no saturen el pool TCP del SO
            response = self._save_session.post(f"{self.base_url}/save/", json=word_data, timeout=5)
            if response.status_code == 200:
                return response.json()  # {'status': 'ok'|'duplicate', 'message': '...'}
            return {'status': 'error', 'message': f'HTTP {response.status_code}'}
        except Exception as e:
            print(f"API Error (save_flashcard): {e}")
            return {'status': 'error', 'message': str(e)}

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
