import requests
import json
from django.conf import settings

class AIService:
    @classmethod
    def get_ollama_url(cls):
        return getattr(settings, 'OLLAMA_API_URL', 'http://127.0.0.1:11434/api/generate')

    @classmethod
    def get_model(cls):
        return getattr(settings, 'OLLAMA_MODEL', 'llama3.2:latest')

    @classmethod
    def generate_examples(cls, word, context_sentence="", source_lang="en", target_lang="es"):
        url = cls.get_ollama_url()
        prompt = f"""Act as a helpful native language teacher. 
Provide 3 practical, everyday examples using the word/phrase '{word}'.
Context (if any): '{context_sentence}'.

Language Rules:
1. The example 'sentence' MUST be written in the language code '{source_lang}'.
2. The 'translation' MUST be written in the language code '{target_lang}'.

Output strictly in JSON format as follows:
{{
    "examples": [
        {{"sentence": "Example 1 in {source_lang}", "translation": "Translation 1 in {target_lang}"}},
        {{"sentence": "Example 2 in {source_lang}", "translation": "Translation 2 in {target_lang}"}},
        {{"sentence": "Example 3 in {source_lang}", "translation": "Translation 3 in {target_lang}"}}
    ]
}}
Do not write anything else outside the JSON block."""

        data = {
            "model": cls.get_model(),
            "prompt": prompt,
            "format": "json",
            "stream": False
        }

        try:
            response = requests.post(url, json=data, timeout=60)
            response.raise_for_status()
            result_json = response.json()
            return json.loads(result_json.get("response", "{}"))
        except Exception as e:
            print(f"Ollama API Error: {e}")
            return {"error": str(e)}

    @classmethod
    def explain_context(cls, word, context_sentence="", source_lang="en", target_lang="es"):
        url = cls.get_ollama_url()
        prompt = f"""Act as a helpful language teacher. Explain the nuance, tone, and why the word '{word}' was used in this context: '{context_sentence}'.

Language Rules:
1. Break down your explanation into individual, logical sentences.
2. Every sentence MUST be written entirely in the language code '{source_lang}'.

Output strictly in JSON format as follows:
{{
    "phonetic": "phonetic text here if known, else omit",
    "explanation_sentences": [
        "Sentence 1 of the explanation in {source_lang}",
        "Sentence 2 of the explanation in {source_lang}"
    ]
}}
Do not write anything else outside the JSON block."""

        data = {
            "model": cls.get_model(),
            "prompt": prompt,
            "format": "json",
            "stream": False
        }

        try:
            response = requests.post(url, json=data, timeout=60)
            response.raise_for_status()
            result_json = response.json()
            parsed_data = json.loads(result_json.get("response", "{}"))
            
            # Hybrid approach: Delegate the translation to the fast deep-translator
            from .translation_service import TranslationService
            final_sentences = []
            
            orig_sentences = parsed_data.get("explanation_sentences", [])
            for sent in orig_sentences:
                # Fallback if Ollama accidentally provided objects instead of strings
                text_to_translate = sent["original"] if isinstance(sent, dict) and "original" in sent else str(sent)
                target_text = TranslationService.translate(text_to_translate, target_lang=target_lang, source_lang=source_lang)
                final_sentences.append({"original": text_to_translate, "translation": target_text})
                
            parsed_data["explanation_sentences"] = final_sentences
            return parsed_data
            
        except Exception as e:
            print(f"Ollama API Error (Explain): {e}")
            return {"error": str(e)}

    @classmethod
    def get_synonyms(cls, word, context_sentence="", source_lang="en", target_lang="es"):
        url = cls.get_ollama_url()
        prompt = f"""Provide a list of 5-8 synonyms for the word '{word}'.
Context (if any): '{context_sentence}'.
For each synonym, provide a very short explanation of the nuance difference in '{target_lang}'.

Output strictly in JSON format:
{{
    "synonyms": [
        {{"word": "synonym1", "nuance": "short explanation in {target_lang}"}},
        ...
    ]
}}"""
        data = {"model": cls.get_model(), "prompt": prompt, "format": "json", "stream": False}
        try:
            response = requests.post(url, json=data, timeout=60)
            return json.loads(response.json().get("response", "{}"))
        except Exception as e: return {"error": str(e)}

    @classmethod
    def get_usage_caution(cls, word, source_lang="en", target_lang="es"):
        url = cls.get_ollama_url()
        prompt = f"""Explain when the word '{word}' should NOT be used. Mention common mistakes, social faux pas, or tone issues (e.g., too formal, too slang).
Provide the explanation as a list of points in '{target_lang}'.

Output strictly in JSON format:
{{
    "caution_points": ["Point 1", "Point 2"]
}}"""
        data = {"model": cls.get_model(), "prompt": prompt, "format": "json", "stream": False}
        try:
            response = requests.post(url, json=data, timeout=60)
            return json.loads(response.json().get("response", "{}"))
        except Exception as e: return {"error": str(e)}

    @classmethod
    def get_etymology(cls, word, target_lang="es"):
        url = cls.get_ollama_url()
        prompt = f"""Provide the etymology (origin and history) of the word '{word}'.
Explain it simply in '{target_lang}'.

Output strictly in JSON format:
{{
    "origin": "Short summary of origin",
    "history": "Brief history of how it evolved"
}}"""
        data = {"model": cls.get_model(), "prompt": prompt, "format": "json", "stream": False}
        try:
            response = requests.post(url, json=data, timeout=60)
            return json.loads(response.json().get("response", "{}"))
        except Exception as e: return {"error": str(e)}

    @classmethod
    def chat_about_word(cls, word, user_query, source_lang="en", target_lang="es"):
        url = cls.get_ollama_url()
        prompt = f"""Act as a professional and helpful language tutor. 
The user is learning the following word/phrase: '{word}'.
The user has asked this question: '{user_query}'

Instructions:
1. Provide a clear, educational, and accurate answer regarding '{word}'.
2. You MUST write your response entirely in '{target_lang}'. 
3. Do NOT use fake personas, strange regional slangs, or weird special characters.
4. If the user's question is about meaning or usage, provide clear examples.
5. Keep a professional but encouraging tone.
6. Ensure any non-standard characters from other languages are used only when necessary for linguistic explanation.

Output strictly in JSON format:
{{
    "answer": "Your detailed teaching response"
}}"""
        data = {"model": cls.get_model(), "prompt": prompt, "format": "json", "stream": False}
        try:
            response = requests.post(url, json=data, timeout=60)
            return json.loads(response.json().get("response", "{}"))
        except Exception as e: return {"error": str(e)}
