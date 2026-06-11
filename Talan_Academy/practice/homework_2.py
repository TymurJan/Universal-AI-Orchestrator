# Talan Academy: Практичне ДЗ №2
# Тема: Перевірка SSL-сертифікатів та безпека HTTPS-з'єднань

import ssl
import socket
from datetime import datetime


def check_ssl_certificate(hostname: str) -> dict:
    """
    Підключається до хоста через порт 443 (HTTPS) та зчитує SSL-сертифікат.
    Повертає словник зі статусом та деталями сертифіката.
    """
    result = {
        "hostname": hostname,
        "valid": False,
        "issued_to": "невідомо",
        "issued_by": "невідомо",
        "expires_on": "невідомо",
        "days_left": -1,
        "warning": None
    }

    try:
        # Створюємо захищений SSL-контекст (перевіряє ланцюжок довіри CA)
        context = ssl.create_default_context()

        # Відкриваємо звичайне TCP-підключення до порту 443
        with socket.create_connection((hostname, 443), timeout=10) as sock:
            # Обгортаємо TCP-сокет у SSL-шар (відбувається TLS-рукостискання)
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()

        # Парсимо дату закінчення дії сертифіката
        expires_str = cert.get("notAfter", "")
        if expires_str:
            expires_date = datetime.strptime(expires_str, "%b %d %H:%M:%S %Y %Z")
            days_left = (expires_date - datetime.utcnow()).days
            result["expires_on"] = expires_date.strftime("%d.%m.%Y")
            result["days_left"] = days_left

        # Отримуємо інформацію про власника та видавця сертифіката
        subject_dict = dict(item[0] for item in cert.get("subject", []))
        issuer_dict  = dict(item[0] for item in cert.get("issuer",  []))
        result["issued_to"] = subject_dict.get("commonName", hostname)
        result["issued_by"] = issuer_dict.get("organizationName", "невідомо")
        result["valid"] = True

        # Попередження, якщо залишилось менше 14 днів
        if 0 < days_left < 14:
            result["warning"] = f"Сертифікат закінчується менш ніж за {days_left} днів! Терміново оновіть через Certbot."
        elif days_left <= 0:
            result["warning"] = "Сертифікат вже ПРОСТРОЧЕНИЙ! З'єднання небезпечне."

    except ssl.SSLCertVerificationError:
        result["warning"] = "Сертифікат НЕ пройшов перевірку довіри. Можлива атака Man-in-the-Middle!"
    except socket.timeout:
        result["warning"] = f"Час очікування підключення до {hostname} вичерпано."
    except Exception as e:
        result["warning"] = f"Помилка перевірки: {e}"

    return result


def print_ssl_report(result: dict) -> None:
    """Виводить структурований звіт про SSL-сертифікат сайту."""
    print("\n" + "=" * 55)
    print(f"  Перевірка SSL-сертифікату для: {result['hostname']}")
    print("=" * 55)

    if result["valid"]:
        print(f"  Статус:          {'✅ Дійсний' if result['days_left'] > 0 else '❌ Прострочений'}")
        print(f"  Виданий для:     {result['issued_to']}")
        print(f"  Видавець (CA):   {result['issued_by']}")
        print(f"  Дійсний до:      {result['expires_on']}")
        print(f"  Днів залишилось: {result['days_left']}")
    else:
        print("  Статус:          ❌ Не вдалось перевірити")

    if result["warning"]:
        print(f"\n  ⚠️  {result['warning']}")

    print("=" * 55)


# --- Запуск перевірки ---
if __name__ == "__main__":
    sites_to_check = [
        "google.com",
        "github.com",
        "expired.badssl.com"  # Тестовий сайт з прострочений сертифікатом
    ]

    for site in sites_to_check:
        report = check_ssl_certificate(site)
        print_ssl_report(report)
