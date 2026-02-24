from deep_translator import GoogleTranslator
from config.language import language_manager


def translate_transcribed_text(event):
    if event.type == "user_input_transcribed":
        try:
            original_text = event.transcript
            if original_text and original_text.strip():
                target_lang = language_manager.get_language()
                # Map language codes to Google Translator format
                lang_map = {
                    "en": "en",
                    "de": "de",
                    "tr": "tr",
                    "es": "es",
                    "fr": "fr",
                    "it": "it",
                    "pt": "pt",
                    "nl": "nl",
                    "pl": "pl",
                    "ar": "ar",
                }
                target_code = lang_map.get(target_lang, "en")
                translator = GoogleTranslator(source="auto", target=target_code)
                translated_text = translator.translate(original_text)
                event.transcript = translated_text
                print(f"Translated query from '{original_text}'\n to '{translated_text}'\n (target: {target_code})")
        except Exception as e:
            print(f"Translation failed: {e}")
            # Keep original text if translation fails