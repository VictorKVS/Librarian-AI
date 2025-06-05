# 📄 Файл: email_utils.py
# 📂 Путь: utils/
# 📌 Назначение: Парсеры писем .eml, .msg, .mbox (заглушка на этапе 1)

# Заготовка — будет реализовано на следующем этапе
# 📄 Файл: email_utils.py
# 📂 Путь: utils/
# 📌 Назначение: Обработка email-файлов (.eml и .msg), извлечение текста и вложений

from email import policy
from email.parser import BytesParser
import extract_msg  # pip install extract-msg


def parse_email_eml(eml_path: str) -> dict:
    """
    Парсинг EML-файла: тема, отправитель, получатель, тело, вложения.
    """
    with open(eml_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)

    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                body += part.get_payload(decode=True).decode(errors='ignore')
    else:
        body = msg.get_payload(decode=True).decode(errors='ignore')

    attachments = [
        part.get_filename()
        for part in msg.walk()
        if part.get_filename() is not None
    ]

    return {
        "subject": msg['subject'],
        "from": msg['from'],
        "to": msg['to'],
        "body": body.strip(),
        "attachments": attachments
    }


def parse_email_msg(msg_path: str) -> dict:
    """
    Парсинг Outlook .msg-файла с помощью extract_msg
    """
    msg = extract_msg.Message(msg_path)
    msg.process()  # обязательный вызов для загрузки вложений

    attachments = [att.longFilename or att.shortFilename for att in msg.attachments]

    return {
        "subject": msg.subject,
        "from": msg.sender,
        "to": msg.to,
        "body": msg.body.strip() if msg.body else "",
        "attachments": attachments
    }