"""
talan/bot/ai_orchestrator.py
Multi-model AI Orchestrator: OpenAI / Anthropic / Gemini провайдери,
автоматичний fallback, chat-пам'ять та утиліта ask_ai().
"""

import os
import logging
from openai import OpenAI
import anthropic
import google.generativeai as genai

log = logging.getLogger("Bot.AI")

# Глобальна пам'ять розмов: {user_id: [{"role": ..., "content": ...}]}
chat_histories: dict[int, list] = {}


# ── Провайдери ────────────────────────────────────────────────────────────────

class BaseAIProvider:
    ready: bool = False

    def ask(self, system_prompt: str, user_text: str, history: list | None = None) -> str:
        raise NotImplementedError


class OpenAIProvider(BaseAIProvider):
    def __init__(self) -> None:
        self.key    = os.getenv("OPENAI_API_KEY")
        self.org_id = os.getenv("OPENAI_ORG_ID")
        self.client = None
        self.ready  = False
        if self.key:
            try:
                if self.org_id:
                    self.client = OpenAI(api_key=self.key, organization=self.org_id)
                    log.info(f"✅ OpenAI Provider: org {self.org_id[:10]}...")
                else:
                    self.client = OpenAI(api_key=self.key)
                    log.info("✅ OpenAI Provider: без org ID")
                self.ready = True
            except Exception as e:
                log.error(f"❌ OpenAI Init Error: {e}")

    def ask(self, system_prompt: str, user_text: str, history: list | None = None) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_text})
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )
        return response.choices[0].message.content


class AnthropicProvider(BaseAIProvider):
    def __init__(self) -> None:
        self.key    = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        self.ready  = False
        if self.key and "sk-ant" in self.key:
            try:
                self.client = anthropic.Anthropic(api_key=self.key)
                self.ready  = True
                log.info("✅ Anthropic Provider: готовий")
            except Exception as e:
                log.error(f"❌ Anthropic Init Error: {e}")

    def ask(self, system_prompt: str, user_text: str, history: list | None = None) -> str:
        messages = []
        if history:
            messages.extend({"role": m["role"], "content": m["content"]} for m in history)
        messages.append({"role": "user", "content": user_text})
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text


class GeminiProvider(BaseAIProvider):
    def __init__(self) -> None:
        self.key   = os.getenv("GEMINI_API_KEY")
        self.model = None
        self.ready = False
        if self.key:
            try:
                genai.configure(api_key=self.key)
                self.model = genai.GenerativeModel("gemini-1.5-flash")
                self.ready = True
                log.info("✅ Gemini Provider: готовий")
            except Exception as e:
                log.error(f"❌ Gemini Init Error: {e}")

    def ask(self, system_prompt: str, user_text: str, history: list | None = None) -> str:
        contents = [
            {"role": "user",  "parts": [system_prompt]},
            {"role": "model", "parts": ["Зрозумів. Я готовий допомагати як Антігравіті."]},
        ]
        if history:
            for m in history:
                role = "user" if m["role"] == "user" else "model"
                contents.append({"role": role, "parts": [m["content"]]})
        contents.append({"role": "user", "parts": [user_text]})
        return self.model.generate_content(contents).text


# ── Оркестратор ────────────────────────────────────────────────────────────────

class AIOrchestrator:
    FALLBACK_ORDER = ["gpt", "claude", "gemini"]

    def __init__(self) -> None:
        self.providers: dict[str, BaseAIProvider] = {
            "gpt":    OpenAIProvider(),
            "claude": AnthropicProvider(),
            "gemini": GeminiProvider(),
        }
        # Автовибір найбільш готової моделі
        self.active_model = "gpt"
        if not self.providers["gpt"].ready:
            for name in ["claude", "gemini"]:
                if self.providers[name].ready:
                    self.active_model = name
                    break

    def switch_model(self, model_name: str) -> bool:
        if model_name in self.providers and self.providers[model_name].ready:
            self.active_model = model_name
            return True
        return False

    def ask(self, system_prompt: str, user_text: str, history: list | None = None) -> str:
        provider = self.providers[self.active_model]
        try:
            return provider.ask(system_prompt, user_text, history)
        except Exception as e:
            log.warning(f"⚠️ Помилка {self.active_model}: {e}. Спробую fallback...")
            for name in self.FALLBACK_ORDER:
                if name == self.active_model:
                    continue
                if self.providers[name].ready:
                    try:
                        log.info(f"🔄 Fallback → {name}")
                        return self.providers[name].ask(system_prompt, user_text, history)
                    except Exception:
                        continue
            raise e


# ── Синглтони ─────────────────────────────────────────────────────────────────
ai_orchestrator = AIOrchestrator()
AI_READY = any(p.ready for p in ai_orchestrator.providers.values())


# ── ask_ai (з пам'яттю) ───────────────────────────────────────────────────────
def ask_ai(user_id: int, user_text: str) -> str:
    """Запит до активного AI-провайдера із збереженням контексту розмови."""
    from talan.bot.config import SYSTEM_PROMPT  # lazy import, уникаємо кола

    if not AI_READY:
        return "⚠️ ШІ-мозок не налаштований. Перевір API ключі у .env файлі."

    history = chat_histories.setdefault(user_id, [])

    try:
        answer = ai_orchestrator.ask(SYSTEM_PROMPT, user_text, history)
        history.append({"role": "user",      "content": user_text})
        history.append({"role": "assistant", "content": answer})
        if len(history) > 20:
            chat_histories[user_id] = history[-20:]
        return answer
    except Exception as e:
        log.error(f"AI Error: {e}")
        return "Друже, щось мій процесор перегрівся. Дай мені хвилину прийти до тями."
