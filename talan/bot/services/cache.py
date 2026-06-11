"""
talan/bot/services/cache.py
Кешування одноразових AI-запитів (ask_ai_oneshot).
"""

import time
import hashlib
import logging

from talan.bot.ai_orchestrator import ai_orchestrator, AI_READY

log = logging.getLogger("Bot.Cache")

CACHE_TTL    = 86400        # 24 години
ONESHOT_CACHE: dict = {}
AUDIO_CACHE:  dict = {}


def ask_ai_oneshot(
    system_msg: str,
    user_msg: str,
    temperature: float = 0.7,
    use_cache: bool = False,
) -> str | None:
    """
    Одноразовий запит до активної AI-моделі без збереження контексту розмови.
    Підтримує кешування результату на CACHE_TTL секунд.
    """
    if not AI_READY:
        return None

    cache_key = None
    if use_cache:
        raw_key = f"{system_msg}_{user_msg}_{temperature}"
        cache_key = hashlib.md5(raw_key.encode("utf-8")).hexdigest()
        entry = ONESHOT_CACHE.get(cache_key)
        if entry and (time.time() - entry["time"] < CACHE_TTL):
            log.debug("Cache HIT (oneshot)")
            return entry["data"]

    try:
        answer = ai_orchestrator.ask(system_msg, user_msg)
        if use_cache and answer and cache_key:
            ONESHOT_CACHE[cache_key] = {"time": time.time(), "data": answer}
        return answer
    except Exception as e:
        log.error(f"ask_ai_oneshot error: {e}")
        return None
