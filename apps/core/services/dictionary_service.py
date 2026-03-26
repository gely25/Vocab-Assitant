import requests

class DictionaryService:
    API_URL = "https://api.dictionaryapi.dev/api/v2/entries/"

    @classmethod
    def get_definition(cls, word, lang='en'):
        url = f"{cls.API_URL}{lang}/{word}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                entry = data[0]
                
                # Buscamos ejemplos y sinónimos en todos los significados
                examples = []
                synonyms = []
                
                # La definición principal será la primera que encontremos
                main_definition = None
                
                for meaning in entry.get('meanings', []):
                    for def_obj in meaning.get('definitions', []):
                        if not main_definition:
                            main_definition = def_obj.get('definition')
                        
                        example = def_obj.get('example')
                        if example and example not in examples:
                            examples.append(example)
                        
                        for syn in def_obj.get('synonyms', []):
                            if syn not in synonyms:
                                synonyms.append(syn)
                    
                    # También hay sinónimos a nivel de 'meaning'
                    for syn in meaning.get('synonyms', []):
                        if syn not in synonyms:
                            synonyms.append(syn)

                return {
                    'definition': main_definition,
                    'example': examples[0] if len(examples) > 0 else None,
                    'example_2': examples[1] if len(examples) > 1 else None,
                    'synonyms': ", ".join(synonyms[:5]),
                    'phonetic': entry.get('phonetic', ''),
                    'meanings': entry.get('meanings', [])
                }
        except Exception:
            pass
        return None
