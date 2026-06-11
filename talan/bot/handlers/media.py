"""
talan/bot/handlers/media.py
Обробник фото та документів: OCR-сканування і збереження у Vault.
"""

import io
import os
import logging
from datetime import datetime

from telebot.types import Message

from talan.bot.config import bot, VAULT_PATH, OCR_ENABLED
from talan.bot.handlers.admin import guard, safe_send

log = logging.getLogger("Bot.Media")


@bot.message_handler(content_types=["photo", "document"])
@guard
def handle_media(msg: Message) -> None:
    safe_send(msg.chat.id, "⏳ Секунду, просканую документ через зір Антігравіті...")
    try:
        if msg.content_type == "photo":
            file_id = msg.photo[-1].file_id
            ext     = ".jpg"
        else:
            file_id = msg.document.file_id
            ext     = os.path.splitext(msg.document.file_name)[1]

        data = bot.download_file(bot.get_file(file_id).file_path)

        recon_text = ""
        if OCR_ENABLED and ext.lower() in (".jpg", ".png", ".jpeg"):
            import pytesseract
            from PIL import Image
            img        = Image.open(io.BytesIO(data))
            recon_text = pytesseract.image_to_string(img, lang="ukr+eng").lower()

        fname = f"DOC_{datetime.now().strftime('%H%M%S')}{ext}"
        (VAULT_PATH / fname).write_bytes(data)

        safe_send(msg.chat.id,
            f"✅ Документ збережено у Сховищі.\n"
            f"Розпізнано тексту: {len(recon_text)} симв. Далі я з ним попрацюю!")

    except Exception as e:
        log.error(f"Media Error: {e}")
        safe_send(msg.chat.id, "❌ Сталася помилка при обробці документа.")
