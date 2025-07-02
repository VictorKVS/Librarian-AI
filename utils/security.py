# utils/security.py
import mimetypes

ALLOWED_MIME_TYPES = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]

def is_allowed_mime(file_path: str) -> bool:
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type in ALLOWED_MIME_TYPES

def scan_for_viruses(file_path: str) -> bool:
    # TODO: интеграция с ClamAV или другой антивирусной системой
    return True