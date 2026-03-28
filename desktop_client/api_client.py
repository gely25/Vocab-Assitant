import requests

class VocabAPIClient:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        
    def get_definition(self, word):
        """Obtiene la definición de una palabra desde el servidor Django"""
        try:
            params = {'word': word, 'source': 'en', 'target': 'es'}
            response = requests.get(f"{self.base_url}/api/define/", params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None
            
    def save_flashcard(self, word_data):
        """Guarda una palabra en el mazo del usuario"""
        try:
            # Reutilizamos el endpoint de guardado de Django
            response = requests.post(f"{self.base_url}/api/save/", json=word_data)
            return response.status_code == 200
        except Exception as e:
            print(f"API Error: {e}")
            return False

    def get_stats(self):
        """Obtiene las estadísticas de estudio para mostrar en el overlay"""
        try:
            response = requests.get(f"{self.base_url}/api/stats/")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"API Error: {e}")
            return None
