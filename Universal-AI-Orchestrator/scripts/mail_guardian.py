import imaplib
import smtplib
import email
import os
import json
import logging
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from dotenv import load_dotenv
from contract_orchestrator import ContractOrchestrator

# Завантажуємо середовище
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Налаштування пошти (треба вказати в .env)
EMAIL_USER = os.getenv("EMAIL_USER", "ngo.talan.ua@gmail.com")
EMAIL_PASS = os.getenv("EMAIL_PASS")  # App Password
IMAP_SERVER = "imap.gmail.com"
SMTP_SERVER = "smtp.gmail.com"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MailGuardian:
    def __init__(self):
        self.orchestrator = ContractOrchestrator()

    def connect_imap(self):
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_USER, EMAIL_PASS)
            return mail
        except Exception as e:
            logging.error(f"IMAP Connection Error: {e}")
            return None

    def classify_email_with_ai(self, subject, body):
        """
        Тут ми б викликали OpenAI. 
        Логіка: якщо в тексті є 'рахунок', 'договір' та цифри ЄДРПОУ.
        """
        # Спрощена логіка для демонстрації (в реальності - GPT-4o-mini)
        text = (subject + " " + body).lower()
        if "рахунок" in text or "договір" in text or "єдрпоу" in text:
            # Шукаємо 8 цифр коду
            import re
            edrpou_match = re.search(r"\b\d{8}\b", text)
            if edrpou_match:
                return {
                    "category": "Saas Lead",
                    "edrpou": edrpou_match.group(0),
                    "tier": "Corporate" if "корп" in text else "Basic"
                }
        return {"category": "Other", "edrpou": None}

    def send_reply(self, to_email, subject, body, attachment_path=None):
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = to_email
            msg['Subject'] = f"Re: {subject}"
            msg.attach(MIMEText(body, 'plain'))

            if attachment_path:
                part = MIMEBase('application', 'octet-stream')
                with open(attachment_path, 'rb') as f:
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
                msg.attach(part)

            server = smtplib.SMTP_SSL(SMTP_SERVER, 465)
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            server.quit()
            logging.info(f"Відповідь надіслана на {to_email}")
        except Exception as e:
            logging.error(f"SMTP Send Error: {e}")

    def scan_inbox(self):
        mail = self.connect_imap()
        if not mail: return

        mail.select("inbox")
        _, data = mail.search(None, 'UNSEEN')
        
        for num in data[0].split():
            _, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            subject = msg['Subject']
            sender = msg['From']
            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
            else:
                body = msg.get_payload(decode=True).decode()

            logging.info(f"Новий лист від {sender}: {subject}")
            
            # --- Робота ШІ ---
            result = self.classify_email_with_ai(subject, body)
            
            if result['category'] == "Saas Lead":
                logging.info(f"🔥 Знайдено лід! ЄДРПОУ: {result['edrpou']}")
                
                # Генеруємо документи
                doc_path = self.orchestrator.process_request(
                    email=sender, 
                    edrpou=result['edrpou'], 
                    tier=result['tier'],
                    position="Директор (Автоматично)"
                )
                
                # Відповідаємо
                reply_text = (
                    f"Вітаємо! Наш ШІ розпізнав ваш запит на отримання документів.\n"
                    f"Ми підготували договір для компанії з ЄДРПОУ {result['edrpou']}.\n\n"
                    f"Документ у вкладенні. Будь ласка, підпишіть та надішліть скан-копію у відповідь.\n"
                    f"З повагою, AI Orchestrator ГО 'ТАЛАН ЮА'."
                )
                self.send_reply(sender, subject, reply_text, doc_path)
            
            # Позначаємо як прочитане
            mail.store(num, '+FLAGS', '\\Seen')

        mail.logout()

if __name__ == "__main__":
    guardian = MailGuardian()
    while True:
        try:
            guardian.scan_inbox()
        except Exception as e:
            logging.error(f"Loop Error: {e}")
        time.sleep(60) # Перевірка раз на хвилину
