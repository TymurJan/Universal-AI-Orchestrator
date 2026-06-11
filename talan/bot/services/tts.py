"""
talan/bot/services/tts.py
Text-to-Speech через OpenAI та веб-пошук через OpenAI Responses API.
"""

import io
import time
import hashlib
import logging

from talan.bot.ai_orchestrator import ai_orchestrator, AI_READY
from talan.bot.services.cache import ask_ai_oneshot, AUDIO_CACHE, CACHE_TTL

log = logging.getLogger("Bot.TTS")


def generate_audio_summary(text: str, voice: str = "nova") -> io.BytesIO | None:
    """
    Генерує аудіо-файл (opus) з тексту через OpenAI TTS.
    Спочатку стискає текст до підсумку, потім озвучує.
    Підтримує кеш AUDIO_CACHE.
    """
    if not AI_READY:
        return None

    cache_key = hashlib.md5(f"audio_{text}_{voice}".encode("utf-8")).hexdigest()
    entry = AUDIO_CACHE.get(cache_key)
    if entry and (time.time() - entry["time"] < CACHE_TTL):
        log.info("Serving Audio TTS from cache.")
        return io.BytesIO(entry["data"])

    try:
        summary = ask_ai_oneshot(
            "Ти — асистент. Зроби чіткий, стислий підсумок наступного тексту українською мовою. "
            "Максимум 3000 символів. Підсумок має бути зрозумілим на слух як аудіо-запис.",
            text,
            use_cache=True,
        )
        if not summary:
            return None

        gpt = ai_orchestrator.providers.get("gpt")
        if not gpt or not gpt.ready:
            log.error("TTS Error: OpenAI provider недоступний.")
            return None

        response = gpt.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=summary,
            response_format="opus",
        )

        audio_data = io.BytesIO()
        for chunk in response.iter_bytes():
            audio_data.write(chunk)

        AUDIO_CACHE[cache_key] = {"time": time.time(), "data": audio_data.getvalue()}
        audio_data.seek(0)
        return audio_data

    except Exception as e:
        log.error(f"TTS Error: {e}")
        return None


def web_search(query: str) -> str:
    """
    Пошук в інтернеті через OpenAI Responses API (web_search_preview).
    Fallback: звичайний запит до активного AI-провайдера.
    """
    if not AI_READY:
        return "⚠️ ШІ не налаштований."

    try:
        gpt = ai_orchestrator.providers.get("gpt")
        if not gpt or not gpt.ready:
            raise RuntimeError("OpenAI client unavailable for web search")

        response = gpt.client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=f"Знайди актуальну інформацію українською мовою: {query}",
        )
        result_text = ""
        for item in response.output:
            if hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text"):
                        result_text += block.text

        return result_text or "Не вдалося знайти інформацію."

    except Exception as e:
        log.error(f"Web Search Error: {e}")
        fallback = ask_ai_oneshot(
            "Ти — дослідник. Дай найкращу відповідь на запит користувача, базуючись на своїх знаннях. "
            "Відповідай українською.",
            query,
        )
        return fallback or f"❌ Помилка пошуку: {e}"
