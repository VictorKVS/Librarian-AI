# agents/project_analyzer/config.py

# agents/project_analyzer/config.py

import os

# ------------------------------------------------------
# 1) Абсолютный путь к корню репозитория (Librarian-AI)
# ------------------------------------------------------
ROOT_DIR = os.getenv(
    "PA_ROOT_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
)

# ------------------------------------------------------
# 2) Папка с архивами и сами ZIP-файлы
# ------------------------------------------------------
ARCHIVE_DIR = os.getenv("PA_ARCHIVE_DIR", os.path.join(ROOT_DIR, "archive"))
PREV_ZIP    = os.path.join(ARCHIVE_DIR, os.getenv("PA_PREV_ZIP_NAME", "prev_version.zip"))
CUR_ZIP     = os.path.join(ARCHIVE_DIR, os.getenv("PA_CUR_ZIP_NAME",  "current_version.zip"))

# ------------------------------------------------------
# 3) Папка для сохранения отчётов Markdown
# ------------------------------------------------------
REPORTS_DIR = os.getenv("PA_REPORTS_DIR", os.path.join(ROOT_DIR, "reports", "project_analyzer"))

# Создадим директории, если их не существуют
os.makedirs(ARCHIVE_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# ------------------------------------------------------
# 4) Какие расширения файлов анализировать
# ------------------------------------------------------
FILE_EXTENSIONS = os.getenv(
    "PA_FILE_EXTENSIONS", 
    ".py,.md,.yaml,.yml,.json,.txt"
).split(",")

# ------------------------------------------------------
# 5) Ограничения на чтение файлов
# ------------------------------------------------------
MAX_FILE_BYTES  = int(os.getenv("PA_MAX_FILE_BYTES", 500_000))   # в байтах
MAX_CHUNK_CHARS = int(os.getenv("PA_MAX_CHUNK_CHARS", 15_000))  # зарезервировано

# ------------------------------------------------------
# 6) Настройки для OpenAI GPT (если всё-таки понадобится)
# ------------------------------------------------------
GPT_MODEL       = os.getenv("PA_GPT_MODEL",       "gpt-4")
GPT_MAX_TOKENS  = int(os.getenv("PA_GPT_MAX_TOKENS", 1500))
GPT_TEMPERATURE = float(os.getenv("PA_GPT_TEMPERATURE", 0.2))

# ------------------------------------------------------
# 7) Выбор провайдера и ключи для него
# ------------------------------------------------------
# Возможные провайдеры: deepseek, gigachat, ollama, hf, openrouter
AI_PROVIDER = os.getenv("AI_PROVIDER", "deepseek").lower()

# DeepSeek
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# GigaChat (СберDevices)
GIGACHAT_API_OAUTH_URL = os.getenv("GIGACHAT_API_OAUTH_URL", "https://ngw.devices.sberbank.ru:9443/api/v2/oauth")
GIGACHAT_API_URL       = os.getenv("GIGACHAT_API_URL",       "https://gigachat.devices.sberbank.ru/api/v1/chat/completions")
GIGACHAT_API_KEY       = os.getenv("GIGACHAT_API_KEY",       "")

# Ollama (локальный сервер)
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# HuggingFace Inference
HF_API_URL = os.getenv(
    "HF_API_URL",
    "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
)
HF_TOKEN = os.getenv("HF_TOKEN", "")

# OpenRouter
OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# ------------------------------------------------------
# 8) Проверка наличия ключей
# ------------------------------------------------------
if AI_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY:
    print("⚠️  DeepSeek: не найден DEEPSEEK_API_KEY.")
if AI_PROVIDER == "gigachat" and not GIGACHAT_API_KEY:
    print("⚠️  GigaChat: не найден GIGACHAT_API_KEY.")
if AI_PROVIDER == "hf" and not HF_TOKEN:
    print("⚠️  HuggingFace: не найден HF_TOKEN.")
if AI_PROVIDER == "openrouter" and not OPENROUTER_API_KEY:
    print("⚠️  OpenRouter: не найден OPENROUTER_API_KEY.")
# Для Ollama допускаем, что он локальный и ключ не нужен
