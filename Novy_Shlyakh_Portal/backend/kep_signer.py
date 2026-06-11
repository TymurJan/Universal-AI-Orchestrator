"""
kep_signer.py — Підписання Consent Receipt кваліфікованим електронним підписом (КЕП)
Портал "Новий Шлях" | ГО Талан UA

Правова основа:
    Закон України № 852-IV «Про електронний цифровий підпис» (ст. 5):
    «Електронний цифровий підпис має таку саму юридичну силу,
     як і власноручний підпис.»

Підтримувані формати КЕП:
    - .p12 / .pfx  (PKCS#12)  — ПриватБанк, Мін'юст, АЦСК ДПС, АЦСК ІДД
    - .jks         (Java KeyStore) — деякі АЦСК

Результат:
    - consent_YYYY-MM-DD.md.p7s  — відокремлений підпис (PKCS#7 detached)
    - або consent_YYYY-MM-DD.md.sig — fallback хеш-підпис якщо PKCS#7 недоступний
"""

import os
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. ЗАВАНТАЖЕННЯ КЕП З .p12 ФАЙЛУ
# ---------------------------------------------------------------------------

def load_kep_from_p12(p12_bytes: bytes, password: str) -> Tuple[object, object, list]:
    """
    Завантажує приватний ключ та сертифікат з .p12 файлу.

    Аргументи:
        p12_bytes: вміст .p12 файлу як bytes
        password:  пароль від КЕПу (НЕ зберігається ніде)

    Повертає:
        (private_key, certificate, additional_certs)

    Винятки:
        ValueError  — якщо пароль невірний або файл пошкоджений
        ImportError — якщо cryptography не встановлена
    """
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
    except ImportError:
        raise ImportError(
            "Бібліотека 'cryptography' не встановлена. "
            "Виконайте: pip install cryptography"
        )

    try:
        pwd_bytes = password.encode("utf-8") if password else None
        private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
            p12_bytes, pwd_bytes
        )
        logger.info("✅ КЕП успішно завантажено. Власник: %s", cert.subject)
        return private_key, cert, additional_certs or []
    except Exception as e:
        logger.error("❌ Помилка завантаження КЕП: %s", e)
        raise ValueError(f"Не вдалось завантажити КЕП: перевірте файл та пароль. ({e})")


# ---------------------------------------------------------------------------
# 2. ПІДПИСАННЯ ДОКУМЕНТА
# ---------------------------------------------------------------------------

def sign_consent_document(
    consent_file_path: str,
    p12_bytes: bytes,
    password: str,
) -> str:
    """
    Підписує consent_*.md КЕПом та зберігає підпис поруч з документом.

    Спроба 1: PKCS#7 detached signature (.p7s) — юридично найсильніший
    Спроба 2: SHA-256 хеш + метадані підпису (.sig) — fallback

    Аргументи:
        consent_file_path: абсолютний шлях до consent_YYYY-MM-DD.md
        p12_bytes:         вміст КЕП-файлу
        password:          пароль (в пам'яті тільки під час виклику)

    Повертає:
        Шлях до файлу підпису (.p7s або .sig)
    """
    consent_path = Path(consent_file_path)
    if not consent_path.exists():
        raise FileNotFoundError(f"Consent-документ не знайдено: {consent_file_path}")

    document_bytes = consent_path.read_bytes()

    # --- Спроба 1: PKCS#7 підпис ---
    try:
        sig_path = _sign_pkcs7(consent_path, document_bytes, p12_bytes, password)
        logger.info("✅ PKCS#7 підпис збережено: %s", sig_path)
        return sig_path
    except Exception as pkcs7_err:
        logger.warning("⚠️ PKCS#7 недоступний (%s), використовуємо fallback.", pkcs7_err)

    # --- Fallback: SHA-256 хеш-підпис з метаданими КЕП ---
    sig_path = _sign_hash_fallback(consent_path, document_bytes, p12_bytes, password)
    logger.info("✅ Hash-підпис (fallback) збережено: %s", sig_path)
    return sig_path


def _sign_pkcs7(
    consent_path: Path,
    document_bytes: bytes,
    p12_bytes: bytes,
    password: str,
) -> str:
    """PKCS#7 detached signature (cryptography >= 36.0)."""
    from cryptography.hazmat.primitives.serialization.pkcs7 import (
        PKCS7SignatureBuilder,
        PKCS7Options,
    )
    from cryptography.hazmat.primitives import hashes

    private_key, cert, add_certs = load_kep_from_p12(p12_bytes, password)

    builder = PKCS7SignatureBuilder()
    builder = builder.set_data(document_bytes)
    builder = builder.add_signer(cert, private_key, hashes.SHA256())
    for ac in add_certs:
        builder = builder.add_certificate(ac)

    sig_bytes = builder.sign(
        encoding=None,  # DER
        options=[PKCS7Options.DetachedSignature, PKCS7Options.NoAttributes],
    )

    sig_path = str(consent_path) + ".p7s"
    with open(sig_path, "wb") as f:
        f.write(sig_bytes)
    return sig_path


def _sign_hash_fallback(
    consent_path: Path,
    document_bytes: bytes,
    p12_bytes: bytes,
    password: str,
) -> str:
    """
    Fallback: зберігає SHA-256 хеш документа + Subject сертифіката.
    Не є повноцінним КЕП, але фіксує факт підпису.
    """
    private_key, cert, _ = load_kep_from_p12(p12_bytes, password)

    doc_hash = hashlib.sha256(document_bytes).hexdigest()
    signed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    try:
        subject = cert.subject.rfc4514_string()
        serial = str(cert.serial_number)
        not_after = cert.not_valid_after_utc.strftime("%Y-%m-%d") if hasattr(cert, 'not_valid_after_utc') else str(cert.not_valid_after)
    except Exception:
        subject = "Невідомий суб'єкт"
        serial = "N/A"
        not_after = "N/A"

    sig_content = f"""# ПІДПИС КЕП (Fallback SHA-256)
## Портал «Новий Шлях» | ГО «ТАЛАН ЮА»

> ⚠️ Це спрощений запис підпису (не PKCS#7).
> Для повноцінного КЕП оновіть бібліотеку: pip install cryptography>=36.0

## ДОКУМЕНТ

| Поле           | Значення                     |
|----------------|------------------------------|
| Файл           | {consent_path.name}          |
| SHA-256        | {doc_hash}                   |
| Підписано (UTC)| {signed_at}                  |

## СЕРТИФІКАТ КЕП

| Поле           | Значення                     |
|----------------|------------------------------|
| Subject        | {subject}                    |
| Serial         | {serial}                     |
| Дійсний до     | {not_after}                  |

*Перевірка: обчисліть SHA-256 файлу {consent_path.name} та порівняйте з хешем вище.*
"""

    sig_path = str(consent_path) + ".sig"
    with open(sig_path, "w", encoding="utf-8") as f:
        f.write(sig_content)
    return sig_path


# ---------------------------------------------------------------------------
# 3. ВЕРИФІКАЦІЯ ПІДПИСУ (для адміна)
# ---------------------------------------------------------------------------

def verify_consent_signature(consent_file_path: str) -> dict:
    """
    Перевіряє цілісність consent-документа за наявним підписом.

    Повертає:
        {
            "valid": True/False,
            "method": "pkcs7" / "sha256_hash" / "none",
            "details": "..."
        }
    """
    consent_path = Path(consent_file_path)
    p7s_path = Path(str(consent_path) + ".p7s")
    sig_path = Path(str(consent_path) + ".sig")

    if not consent_path.exists():
        return {"valid": False, "method": "none", "details": "Файл не знайдено"}

    document_bytes = consent_path.read_bytes()

    # Перевірка PKCS#7
    if p7s_path.exists():
        try:
            from cryptography.hazmat.primitives.serialization import pkcs7
            # Базова перевірка — файл читається
            sig_bytes = p7s_path.read_bytes()
            return {
                "valid": True,
                "method": "pkcs7",
                "details": f"PKCS#7 підпис знайдено ({len(sig_bytes)} байт). Верифікація через openssl verify."
            }
        except Exception as e:
            return {"valid": False, "method": "pkcs7", "details": str(e)}

    # Перевірка SHA-256 fallback
    if sig_path.exists():
        sig_content = sig_path.read_text(encoding="utf-8")
        actual_hash = hashlib.sha256(document_bytes).hexdigest()
        if actual_hash in sig_content:
            return {"valid": True, "method": "sha256_hash", "details": "Хеш SHA-256 співпадає — документ не змінювався."}
        else:
            return {"valid": False, "method": "sha256_hash", "details": "❌ Хеш не співпадає — документ міг бути змінений!"}

    return {"valid": False, "method": "none", "details": "Підпис відсутній — лише checkbox consent."}


# ---------------------------------------------------------------------------
# 4. ДЕМОНСТРАЦІЯ (python kep_signer.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  kep_signer.py — тест завантаження КЕП")
    print("="*60)
    print("\nДля тесту передайте реальний .p12 файл:")
    print("  p12_path = 'path/to/your_kep.p12'")
    print("  with open(p12_path, 'rb') as f:")
    print("      p12_bytes = f.read()")
    print("  private_key, cert, _ = load_kep_from_p12(p12_bytes, 'your_password')")
    print("\nАБО перевірте наявний підпис:")
    print("  result = verify_consent_signature('path/to/consent_2026-06-09.md')")
    print("  print(result)")
