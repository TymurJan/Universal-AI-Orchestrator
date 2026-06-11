"""
crypto_utils.py — Модуль шифрування конфіденційних документів
Портал "Новий Шлях" | ГО Талан UA

Призначення:
    Шифрування персональних регуляторних документів спеціалістів:
    - Виписки з ДІЯ (ідентифікація)
    - Дипломи та сертифікати
    - Ліцензії на медичну / психологічну діяльність
    - Документи ФОП

Алгоритм: Fernet (AES-128-CBC + HMAC-SHA256) — бібліотека cryptography.
Ключ:     Зберігається у змінній середовища FERNET_KEY (файл .env).

Як підключити в db_manager.py (коли з'явиться реєстрація):
    from crypto_utils import encrypt_doc, decrypt_doc

    # При збереженні:
    encrypted = encrypt_doc(diploma_file_id)
    cursor.execute("UPDATE specialists SET diploma_enc = ?", (encrypted,))

    # При читанні (тільки для адміна):
    original = decrypt_doc(encrypted)
"""

import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. УПРАВЛІННЯ КЛЮЧЕМ
# ---------------------------------------------------------------------------

def _load_or_create_key() -> bytes:
    """
    Завантажує ключ Fernet із змінної середовища FERNET_KEY.

    Якщо FERNET_KEY не встановлений (режим розробки без .env) —
    генерує тимчасовий ключ і виводить ПОПЕРЕДЖЕННЯ в лог.
    У продакшні FERNET_KEY ОБОВ'ЯЗКОВО має бути у .env.
    """
    raw_key = os.environ.get("FERNET_KEY")

    if raw_key:
        return raw_key.encode("utf-8")

    # Режим розробки: генеруємо одноразовий ключ (дані не збережуться між сесіями!)
    logger.warning(
        "⚠️  FERNET_KEY не знайдено в оточенні! "
        "Використовується тимчасовий ключ. "
        "НІКОЛИ не допускай цього в продакшні — зашифровані дані будуть нечитабельними після перезапуску."
    )
    temp_key = Fernet.generate_key()
    logger.warning("🔑 Тимчасовий ключ (лише для розробки): %s", temp_key.decode())
    return temp_key


# Ініціалізуємо шифрувальник один раз при імпорті модуля
try:
    _FERNET_KEY = _load_or_create_key()
    _fernet = Fernet(_FERNET_KEY)
    logger.info("✅ crypto_utils: шифрувальник Fernet ініціалізований успішно.")
except Exception as e:
    logger.critical("❌ crypto_utils: не вдалось ініціалізувати Fernet: %s", e)
    raise RuntimeError(f"Критична помилка ініціалізації шифрування: {e}") from e


# ---------------------------------------------------------------------------
# 2. ШИФРУВАННЯ / РОЗШИФРУВАННЯ ТЕКСТОВИХ ПОЛІВ
# ---------------------------------------------------------------------------

def encrypt_doc(plaintext: str | None) -> str | None:
    """
    Шифрує рядок (Telegram file_id документа або текстовий ідентифікатор).

    Аргументи:
        plaintext: оригінальний рядок для шифрування.
                   Якщо None — повертає None (поле не заповнене).

    Повертає:
        Зашифрований рядок у форматі URL-safe Base64 (безпечний для SQLite TEXT).
    """
    if plaintext is None:
        return None
    try:
        token: bytes = _fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")
    except Exception as e:
        logger.error("encrypt_doc: помилка шифрування — %s", e)
        raise


def decrypt_doc(ciphertext: str | None) -> str | None:
    """
    Розшифровує рядок, зашифрований функцією encrypt_doc().

    Аргументи:
        ciphertext: зашифрований рядок із бази даних.
                    Якщо None — повертає None.

    Повертає:
        Оригінальний рядок або None при помилці.

    Винятки:
        InvalidToken — якщо ключ неправильний або дані пошкоджені.
    """
    if ciphertext is None:
        return None
    try:
        original: bytes = _fernet.decrypt(ciphertext.encode("utf-8"))
        return original.decode("utf-8")
    except InvalidToken:
        logger.error(
            "decrypt_doc: InvalidToken — неправильний ключ або пошкоджені дані. "
            "Переконайся, що FERNET_KEY не змінювався після шифрування."
        )
        raise
    except Exception as e:
        logger.error("decrypt_doc: несподівана помилка — %s", e)
        raise


# ---------------------------------------------------------------------------
# 3. ШИФРУВАННЯ / РОЗШИФРУВАННЯ БІНАРНИХ ФАЙЛІВ (для майбутнього)
# ---------------------------------------------------------------------------

def encrypt_file(file_bytes: bytes) -> bytes:
    """
    Шифрує сирі байти файлу (PDF, JPG тощо).
    Використовувати для зберігання документів на диску сервера.

    Аргументи:
        file_bytes: вміст файлу як bytes.

    Повертає:
        Зашифровані байти (можна зберегти у .enc файл).
    """
    return _fernet.encrypt(file_bytes)


def decrypt_file(encrypted_bytes: bytes) -> bytes:
    """
    Розшифровує байти файлу, зашифрованого encrypt_file().

    Аргументи:
        encrypted_bytes: зашифрований вміст файлу.

    Повертає:
        Оригінальні байти файлу.
    """
    return _fernet.decrypt(encrypted_bytes)


# ---------------------------------------------------------------------------
# 4. УТИЛІТИ ДЛЯ АДМІНІСТРАТОРА
# ---------------------------------------------------------------------------

def generate_new_key() -> str:
    """
    Генерує новий Fernet-ключ і виводить його.

    Використовувати ОДИН РАЗ при першому деплої на хостинг.
    Результат скопіювати у .env як FERNET_KEY=<ключ>

    Приклад виводу:
        FERNET_KEY=dGhpcyBpcyBhIHRlc3Qga2V5IGZvciBkZW1v_base64_url_safe_chars
    """
    key = Fernet.generate_key().decode("utf-8")
    print(f"\n{'='*60}")
    print("  🔑 НОВИЙ FERNET-КЛЮЧ (скопіюй у .env на сервері)")
    print(f"{'='*60}")
    print(f"  FERNET_KEY={key}")
    print(f"{'='*60}")
    print("  ⚠️  Зберігай цей ключ у надійному місці!")
    print("  ⚠️  Якщо ключ буде втрачено — зашифровані документи")
    print("  ⚠️  стануть НЕЧИТАБЕЛЬНИМИ назавжди!")
    print(f"{'='*60}\n")
    return key


# ---------------------------------------------------------------------------
# 5. ДЕМОНСТРАЦІЙНИЙ ЗАПУСК (python crypto_utils.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Демонстрація crypto_utils.py — портал 'Новий Шлях'")
    print("="*60)

    # Генеруємо ключ для деплою
    print("\n[1] Генерація ключа для .env:")
    generate_new_key()

    # Тест шифрування текстового Telegram file_id
    test_file_id = "BQACAgIAAxkBAAIBmWX5abc123def456diploma"
    print(f"[2] Оригінальний file_id диплому: {test_file_id}")

    encrypted = encrypt_doc(test_file_id)
    print(f"[2] Зашифровано (у БД зберігається так): {encrypted[:60]} [скорочено]")

    decrypted = decrypt_doc(encrypted)
    print(f"[2] Розшифровано (адміном): {decrypted}")
    assert decrypted == test_file_id, "❌ ПОМИЛКА: результат не співпав!"
    print("    ✅ Перевірка пройдена — дані цілісні\n")

    # Тест з None (незаповнене поле)
    print(f"[3] Шифрування None (поле не заповнене): {encrypt_doc(None)}")
    print(f"[3] Розшифрування None: {decrypt_doc(None)}")
    print("\n✅ Всі тести пройдено. Модуль готовий до підключення в db_manager.py")
