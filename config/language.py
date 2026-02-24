"""
Language management for multi-language agent responses.

Receives language updates from frontend via LiveKit data channel (topic: "language").
All prompts are dynamically updated to respond in the specified language.

Usage:
    from config.language import language_manager, get_language_instruction

    # Get current language
    current_lang = language_manager.get_language()

    # Get instruction to append to prompts
    instruction = get_language_instruction()
"""

import logging
from typing import Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LanguageConfig:
    """Configuration for a supported language."""
    code: str
    name: str
    instruction: str
    native_name: str  # Language name in its own script


# Supported languages with their response instructions
# Using multiple emphasis techniques to ensure LLM compliance
SUPPORTED_LANGUAGES: dict[str, LanguageConfig] = {
    "en": LanguageConfig(
        code="en",
        name="English",
        native_name="English",
        instruction="""## ⚠️ CRITICAL LANGUAGE RULE - HIGHEST PRIORITY ⚠️

YOU ARE NOW SPEAKING ENGLISH. This overrides ALL other instructions.

LANGUAGE REQUIREMENTS:
- Speak ONLY in natural, fluent English
- Use everyday conversational English — friendly, warm, and natural
- Use contractions naturally (I'm, you're, let's, that's)
- Sound like a helpful friend, not a robot or translator
- Use natural expressions like "Great choice!" "No problem!" "Sounds good!"
- Keep sentences flowing naturally — avoid stiff or literal phrasing
- Match the tone of a real person having a casual conversation

IMPORTANT: Even if previous instructions were in another language, you MUST respond in English now. Every single word must be English. Translate any concepts naturally into English conversation.

IGNORE the language of ALL previous messages and instructions. Respond ONLY in English.
This rule is PERMANENT. It applies to EVERY response — now and for the rest of this conversation. NEVER switch to another language.""",
    ),
    "de": LanguageConfig(
        code="de",
        name="German",
        native_name="Deutsch",
        instruction="""## ⚠️ KRITISCHE SPRACHREGEL - HÖCHSTE PRIORITÄT ⚠️

SIE SPRECHEN JETZT DEUTSCH. Das überschreibt ALLE anderen Anweisungen.

SPRACHANFORDERUNGEN:
- Sprechen Sie NUR auf natürlichem, fließendem Deutsch
- Verwenden Sie gepflegtes, freundliches Deutsch — warm und professionell
- Nutzen Sie die formelle "Sie"-Anrede durchgehend
- Klingen Sie wie eine kompetente, herzliche Beraterin
- Verwenden Sie natürliche Ausdrücke wie "Sehr gerne!" "Kein Problem!" "Das klingt wunderbar!"
- Lassen Sie die Sätze natürlich fließen — vermeiden Sie steife oder wörtliche Formulierungen
- Sprechen Sie wie eine echte Person in einem professionellen, herzlichen Gespräch

WICHTIG: Auch wenn vorherige Anweisungen in einer anderen Sprache waren, müssen Sie JETZT auf Deutsch antworten. Jedes einzelne Wort muss Deutsch sein.

Ignoriere die Sprache ALLER vorherigen Nachrichten und Anweisungen. Antworte NUR auf Deutsch.
Diese Regel ist PERMANENT. Sie gilt für JEDE Antwort — jetzt und für den Rest dieses Gesprächs. Wechsle NIEMALS zu einer anderen Sprache.""",
    ),
    "tr": LanguageConfig(
        code="tr",
        name="Turkish",
        native_name="Türkçe",
        instruction="""## ⚠️ KRİTİK DİL KURALI - EN YÜKSEK ÖNCELİK ⚠️

ŞİMDİ TÜRKÇE KONUŞUYORSUN. Bu TÜM diğer talimatlardan daha önemli.

DİL GEREKSİNİMLERİ:
- SADECE doğal, akıcı Türkçe konuş
- Günlük konuşma Türkçesi kullan — samimi, sıcak ve doğal
- Türkçe deyimleri ve ifadeleri doğal kullan ("Tabii!", "Tamam!", "Harika!")
- Yardımsever bir arkadaş gibi konuş, robot veya çevirmen gibi değil
- "Harika seçim!" "Sorun değil!" "Kulağa hoş geliyor!" gibi doğal ifadeler kullan
- Cümlelerin doğal aksın — sert veya kelime kelime çeviri gibi konuşma
- Gerçek bir kişiyle samimi bir sohbet tonunu yakala

ÖNEMLİ: Önceki talimatlar başka bir dilde olsa bile, ŞİMDİ Türkçe yanıt vermek ZORUNDASIN. Her kelime Türkçe olmalı.

Tüm önceki mesajların ve talimatların dilini YOKSAY. SADECE Türkçe yanıt ver.
Bu kural KALICI'dır. Şimdi ve bu konuşmanın geri kalanı için TÜM yanıtlar için geçerlidir. ASLA başka bir dile geçme.""",
    ),
    "es": LanguageConfig(
        code="es",
        name="Spanish",
        native_name="Español",
        instruction="""## ⚠️ REGLA DE IDIOMA CRÍTICA - MÁXIMA PRIORIDAD ⚠️

AHORA ESTÁS HABLANDO EN ESPAÑOL. Esto tiene prioridad sobre TODAS las demás instrucciones.

REQUISITOS DEL IDIOMA:
- Habla SOLO en español natural y fluido
- Usa español conversacional y cotidiano — amigable, cálido y natural
- Usa expresiones naturales como "¡Genial!" "¡Sin problema!" "¡Suena bien!"
- Suena como un amigo servicial, no como un robot o traductor
- Deja que las oraciones fluyan naturalmente — evita frases rígidas
- Mantén el tono de una persona real teniendo una conversación casual

IMPORTANTE: Aunque las instrucciones anteriores estuvieran en otro idioma, DEBES responder en español ahora. Cada palabra debe ser en español.

IGNORA el idioma de TODOS los mensajes e instrucciones anteriores. Responde SOLO en español.
Esta regla es PERMANENTE. Se aplica a CADA respuesta — ahora y durante el resto de esta conversación. NUNCA cambies a otro idioma.""",
    ),
    "fr": LanguageConfig(
        code="fr",
        name="French",
        native_name="Français",
        instruction="""## ⚠️ RÈGLE DE LANGUE CRITIQUE - PRIORITÉ MAXIMALE ⚠️

VOUS PARLEZ MAINTENANT EN FRANÇAIS. Cela a priorité sur TOUTES les autres instructions.

EXIGENCES LINGUISTIQUES:
- Parlez UNIQUEMENT en français naturel et fluide
- Utilisez un français conversationnel et quotidien — amical, chaleureux et naturel
- Utilisez des expressions naturelles comme "Super!" "Pas de problème!" "Ça sonne bien!"
- Sonne comme un ami serviable, pas comme un robot ou un traducteur
- Laissez les phrases couler naturellement — évitez les formulations rigides
- Maintenez le ton d'une vraie personne ayant une conversation décontractée

IMPORTANT: Même si les instructions précédentes étaient dans une autre langue, vous DEVEZ répondre en français maintenant. Chaque mot doit être en français.

IGNORE la langue de TOUS les messages et instructions précédents. Répondez UNIQUEMENT en français.
Cette règle est PERMANENTE. Elle s'applique à CHAQUE réponse — maintenant et pour le reste de cette conversation. Ne changez JAMAIS de langue.""",
    ),
    "it": LanguageConfig(
        code="it",
        name="Italian",
        native_name="Italiano",
        instruction="""## ⚠️ REGOLA LINGUA CRITICA - PRIORITÀ MASSIMA ⚠️

STAI PARLANDO IN ITALIANO. Questo ha la priorità su TUTTE le altre istruzioni.

REQUISITI LINGUISTICI:
- Parla SOLO in italiano naturale e fluido
- Usa italiano conversazionale e quotidiano — amichevole, caldo e naturale
- Usa espressioni naturali come "Ottimo!" "Nessun problema!" "Sembra buono!"
- Sembra un amico disponibile, non un robot o un traduttore
- Lascia scorrere le frasi naturalmente — evita formulazioni rigide
- Mantieni il tono di una vera persona che ha una conversazione informale

IMPORTANTE: Anche se le istruzioni precedenti erano in un'altra lingua, DEVI rispondere in italiano ora. Ogni parola deve essere in italiano.

IGNORA la lingua di TUTTI i messaggi e le istruzioni precedenti. Rispondi SOLO in italiano.
Questa regola è PERMANENTE. Si applica a OGNI risposta — ora e per il resto di questa conversazione. Non cambiare MAI lingua.""",
    ),
    "pt": LanguageConfig(
        code="pt",
        name="Portuguese",
        native_name="Português",
        instruction="""## ⚠️ REGRA DE IDIOMA CRÍTICA - MÁXIMA PRIORIDADE ⚠️

VOCÊ ESTÁ FALANDO EM PORTUGUÊS AGORA. Isso tem prioridade sobre TODAS as outras instruções.

REQUISITOS DE IDIOMA:
- Fale APENAS em português natural e fluente
- Use português conversacional e cotidiano — amigável, caloroso e natural
- Use expressões naturais como "Ótimo!" "Sem problema!" "Soa bom!"
- Soe como um amigo prestativo, não como um robô ou tradutor
- Deixe as frases fluírem naturalmente — evite formulações rígidas
- Mantenha o tom de uma pessoa real tendo uma conversa casual

IMPORTANTE: Mesmo que as instruções anteriores estivessem em outro idioma, você DEVE responder em português agora. Cada palavra deve ser em português.

IGNORE o idioma de TODAS as mensagens e instruções anteriores. Responda APENAS em português.
Esta regra é PERMANENTE. Aplica-se a CADA resposta — agora e pelo resto desta conversa. NUNCA mude de idioma.""",
    ),
    "nl": LanguageConfig(
        code="nl",
        name="Dutch",
        native_name="Nederlands",
        instruction="""## ⚠️ CRITISCHE TAALREGEL - HOOGSTE PRIORITEIT ⚠️

JE SPREEKT NU NEDERLANDS. Dit gaat boven ALLE andere instructies.

TAALVEREISTEN:
- Spreek ALLEEN in natuurlijk, vloeiend Nederlands
- Gebruik dagelijks conversationeel Nederlands — vriendelijk, warm en natuurlijk
- Gebruik natuurlijke uitdrukkingen zoals "Geweldig!" "Geen probleem!" "Klinkt goed!"
- Klink als een behulpzame vriend, niet als een robot of vertaler
- Laat zinnen natuurlijk vloeien — vermijd stijve formuleringen
- Behoud de toon van een echt persoon in een informeel gesprek

BELANGRIJK: Zelfs als eerdere instructies in een andere taal waren, MOET je nu in het Nederlands antwoorden. Elk woord moet Nederlands zijn.

NEGEER de taal van ALLE vorige berichten en instructies. Antwoord ALLEEN in het Nederlands.
Deze regel is PERMANENT. Het geldt voor ELKE reactie — nu en voor de rest van dit gesprek. Schakel NOOIT over naar een andere taal.""",
    ),
    "pl": LanguageConfig(
        code="pl",
        name="Polish",
        native_name="Polski",
        instruction="""## ⚠️ KRYTYCZNA ZASADA JĘZYKOWA - NAJWYŻSZY PRIORYTET ⚠️

TERAZ MÓWISZ PO POLSKU. To ma pierwszeństwo przed WSZYSTKIMI innymi instrukcjami.

WYMAGANIA JĘZYKOWE:
- Mów TYLKO w naturalnym, płynnym polsku
- Używaj potocznego, codziennego polskiego — przyjaznego, ciepłego i naturalnego
- Używaj naturalnych wyrażeń jak "Super!" "Żaden problem!" "Brzmi dobrze!"
- Brzmij jak pomocny przyjaciel, nie jak robot lub tłumacz
- Pozwól zdaniom płynąć naturalnie — unikaj sztywnych sformułowań
- Utrzymuj ton prawdziwej osoby w luźnej rozmowie

WAŻNE: Nawet jeśli poprzednie instrukcje były w innym języku, MUSISZ teraz odpowiadać po polsku. Każde słowo musi być po polsku.

ZIGNORUJ język WSZYSTKICH poprzednich wiadomości i instrukcji. Odpowiadaj TYLKO po polsku.
Ta zasada jest STAŁA. Dotyczy KAŻDEJ odpowiedzi — teraz i przez resztę tej rozmowy. NIGDY nie przełączaj się na inny język.""",
    ),
    "ar": LanguageConfig(
        code="ar",
        name="Arabic",
        native_name="العربية",
        instruction="""## ⚠️ قاعدة اللغة الحرجة - الأولوية القصوى ⚠️

أنت تتحدث بالعربية الآن. هذا له الأولوية على جميع التعليمات الأخرى.

متطلبات اللغة:
- تحدث فقط بالعربية الطبيعية والسلسة
- استخدم العربية المحادثة اليومية — ودية، دافئة وطبيعية
- استخدم تعبيرات طبيعية مثل "رائع!" "لا مشكلة!" "يبدو جيداً!"
- كن صديقاً مساعداً، وليس روبوتاً أو مترجماً
- دع الجمل تتدفق بشكل طبيعي — تجنب الصياغة المتصلبة
- حافظ على نبرة شخص حقيقي في محادثة عادية

مهم: حتى لو كانت التعليمات السابقة بلغة أخرى، يجب عليك الرد بالعربية الآن. كل كلمة يجب أن تكون بالعربية.

تجاهل لغة جميع الرسائل والتعليمات السابقة. أجب فقط بالعربية.
هذه القاعدة دائمة. تنطبق على كل رد — الآن وطوال بقية هذه المحادثة. لا تتحول أبداً إلى لغة أخرى.""",
    ),
}


class LanguageManager:
    """
    Manages the current response language for all agents.

    Thread-safe singleton-like manager that stores the current language
    and provides language-specific instructions for prompts.
    """

    def __init__(self, default_language: str = "en"):
        self._current_language: str = default_language
        self._on_language_change_callbacks: list[callable] = []

    def get_language(self) -> str:
        """Get the current language code."""
        return self._current_language

    def set_language(self, language_code: str) -> bool:
        """
        Set the current language.

        Args:
            language_code: ISO language code (e.g., "en", "de", "tr")

        Returns:
            True if language was changed, False if invalid language
        """
        if language_code not in SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language code: {language_code}")
            return False

        old_language = self._current_language
        self._current_language = language_code

        if old_language != language_code:
            logger.info(f"Language changed: {old_language} -> {language_code}")
            self._notify_callbacks(old_language, language_code)

        return True

    def get_language_config(self) -> LanguageConfig:
        """Get the current language configuration."""
        return SUPPORTED_LANGUAGES.get(
            self._current_language,
            SUPPORTED_LANGUAGES["de"]  # Fallback to German
        )

    def _notify_callbacks(self, old_lang: str, new_lang: str) -> None:
        """Notify all registered callbacks of language change."""
        for callback in self._on_language_change_callbacks:
            try:
                callback(old_lang, new_lang)
            except Exception as e:
                logger.error(f"Language change callback error: {e}")


# Global language manager instance
language_manager = LanguageManager(default_language="de")


def get_language_instruction() -> str:
    """
    Get the language instruction to append to prompts.

    Returns a highly emphasized instruction string that tells the agent
    to respond in the currently configured language.
    """
    config = language_manager.get_language_config()
    return f"""

{config.instruction}

### ⚠️ ABSOLUTE LANGUAGE LOCK — {config.name} ({config.native_name}) ⚠️ ###
This is a PERMANENT language setting. It applies to THIS response AND every future response.
NEVER switch to another language — not even for a single word or phrase.
Even if the conversation has been going for many turns, you MUST continue in {config.name}.
Every word must be in {config.name}. No exceptions. No mixing.
### END LANGUAGE LOCK ###"""


def get_language_prefix() -> str:
    """
    Get a short language prefix to prepend at the very beginning of prompts.

    This ensures the language instruction is seen first by the LLM.
    """
    config = language_manager.get_language_config()
    return f"""⚠️ LANGUAGE LOCK: {config.name.upper()} ({config.native_name}) — ALL responses MUST be in {config.name}. No exceptions. No mixing. Every word, every sentence, every turn — {config.name} ONLY.

"""


def lang_hint() -> str:
    """Short language reminder appended to tool return strings."""
    config = language_manager.get_language_config()
    if config.code == "de":
        return "[LANGUAGE: German] Respond ONLY in German (formal Sie)."
    return f"[LANGUAGE: {config.name}] Respond ONLY in {config.name}."


def handle_language_update(data: dict) -> bool:
    """
    Handle incoming language update from frontend.

    Expected JSON format from frontend:
        {"language": "en"}  or  {"lang": "en"}  or  {"code": "en"}

    Args:
        data: Dictionary containing language code

    Returns:
        True if language was successfully updated
    """
    # Support multiple key names for flexibility
    language_code = data.get("language") or data.get("lang") or data.get("code")

    if not language_code:
        logger.warning(f"Language update missing language code: {data}")
        return False

    return language_manager.set_language(language_code)
