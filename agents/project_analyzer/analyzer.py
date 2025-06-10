# agents/project_analyzer/analyzer.py

import os
import sqlite3
import hashlib
import zipfile
import tempfile
import shutil
from difflib import unified_diff
from datetime import datetime
from typing import Optional, Dict, List, Set

import requests
import httpx
import logging

from .config import (
    ROOT_DIR,
    PREV_ZIP, CUR_ZIP, REPORTS_DIR,
    FILE_EXTENSIONS, MAX_FILE_BYTES, MAX_CHUNK_CHARS,
    AI_PROVIDER,
    # DeepSeek
    DEEPSEEK_API_URL, DEEPSEEK_API_KEY,
    # GigaChat
    GIGACHAT_API_OAUTH_URL, GIGACHAT_API_URL, GIGACHAT_API_KEY,
    # Ollama
    OLLAMA_URL, OLLAMA_MODEL,
    # HuggingFace
    HF_API_URL, HF_TOKEN,
    # OpenRouter
    OPENROUTER_URL, OPENROUTER_API_KEY
)
from config.secrets import Settings

settings = Settings()

# ============ Инициализация логгера ============

logger = logging.getLogger("project_analyzer")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(ch)


# ============ Cache System ============

class AICache:
    def __init__(self):
        self.db_path = os.path.join(ROOT_DIR, "cache_ai.db")
        self.conn = self._init_db()
        
    def _init_db(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_cache (
                prompt_hash TEXT PRIMARY KEY,
                response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                provider TEXT
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON ai_cache(timestamp)
        """)
        conn.commit()
        return conn
    
    def get_response(self, prompt: str) -> Optional[str]:
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT response FROM ai_cache WHERE prompt_hash = ?",
            (prompt_hash,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    
    def set_response(self, prompt: str, response: str, provider: str):
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO ai_cache 
               (prompt_hash, response, provider) VALUES (?, ?, ?)""",
            (prompt_hash, response, provider)
        )
        self.conn.commit()
    
    def cleanup_old_entries(self, days_old: int = 30):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM ai_cache WHERE timestamp < datetime('now', ?) ",
            (f" -{days_old} days",)
        )
        self.conn.commit()

# Создаём одиночный экземпляр кеша
cache = AICache()



# ============ Core Comparison Logic ============

def unzip_to_tmp(zip_path: str) -> str:
    """Распаковывает ZIP во временную папку."""
    prefix = "prev_" if "prev" in os.path.basename(zip_path) else "current_"
    tmp_dir = tempfile.mkdtemp(prefix=f"proj_{prefix}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(tmp_dir)
    except Exception as e:
        logger.error(f"Failed to unzip {zip_path}: {e}")
        raise
    return tmp_dir

def gather_files(root: str, exts: Optional[List[str]] = None) -> Set[str]:
    """Собирает все файлы с указанными расширениями."""
    files = set()
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if exts is None or any(fname.endswith(ext) for ext in exts):
                rel_path = os.path.relpath(os.path.join(dirpath, fname), root)
                files.add(rel_path)
    return files

def read_file_safely(path: str, max_bytes: int = MAX_FILE_BYTES) -> List[str]:
    """Читает файл с ограничением по размеру и обработкой ошибок."""
    try:
        size = os.path.getsize(path)
        if size > max_bytes:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(max_bytes)
            return content.splitlines(True) + [f"\n...(truncated at {max_bytes} bytes)..."]
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()
    except Exception as e:
        logger.warning(f"Error reading file {path}: {e}")
        return [f"# Error reading file: {str(e)}\n"]

def diff_files(prev_dir: str, curr_dir: str) -> Dict[str, List]:
    """Сравнивает две версии проекта, возвращает dict с added/removed/modified."""
    prev_files = gather_files(prev_dir, FILE_EXTENSIONS)
    curr_files = gather_files(curr_dir, FILE_EXTENSIONS)
    
    added   = sorted(curr_files - prev_files)
    removed = sorted(prev_files - curr_files)
    common  = prev_files & curr_files
    
    modified = []
    for f in sorted(common):
        prev_lines = read_file_safely(os.path.join(prev_dir, f))
        curr_lines = read_file_safely(os.path.join(curr_dir, f))
        if prev_lines != curr_lines:
            diff_snippet = "".join(list(unified_diff(
                prev_lines, curr_lines, fromfile=f, tofile=f, lineterm=""
            ))[:50])
            modified.append({"file": f, "diff": diff_snippet})
    
    return {
        "added": added,
        "removed": removed,
        "modified": modified
    }

def build_project_summary(root: str, files: Set[str]) -> str:
    """Генерирует сводку структуры проекта."""
    total_files = len(files)
    total_size = sum(
        os.path.getsize(os.path.join(root, f))
        for f in files
        if os.path.exists(os.path.join(root, f))
    )
    avg_size = total_size // total_files if total_files else 0
    
    modules = {
        os.sep.join(f.split(os.sep)[:2])
        for f in files
        if len(f.split(os.sep)) > 1
    }
    
    lines = [
        f"Project root: {root}",
        f"Total files: {total_files}",
        f"Total size: {total_size:,} bytes",
        f"Average file size: {avg_size:,} bytes",
        "",
        "Main modules/directories:"
    ]
    for m in sorted(modules)[:50]:
        lines.append(f"  • {m}")
    if len(modules) > 50:
        lines.append("  ... (more modules)")
    
    return "\n".join(lines)

def build_changes_report(changes: Dict) -> str:
    """Собирает человекочитаемую сводку изменений."""
    parts: List[str] = []
    
    if changes["added"]:
        parts.append("Added files:")
        for f in changes["added"]:
            parts.append(f"  + {f}")
        parts.append("")
    
    if changes["removed"]:
        parts.append("Removed files:")
        for f in changes["removed"]:
            parts.append(f"  - {f}")
        parts.append("")
    
    if changes["modified"]:
        parts.append("Modified files (first 50 diff lines):")
        for mod in changes["modified"]:
            parts.append(f"--- {mod['file']} ---")
            parts.append("```diff")
            parts.append(mod["diff"])
            parts.append("```")
            parts.append("")
    
    return "\n".join(parts)


# ============ AI Providers ============

class AIProvider:
    @staticmethod
    async def ask_deepseek(prompt: str) -> str:
        """DeepSeek Chat API (асинхронный)."""
        if not DEEPSEEK_API_KEY:
            msg = "DeepSeek error: DEEPSEEK_API_KEY not configured"
            logger.error(msg)
            return msg
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    DEEPSEEK_API_URL,
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    },
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    }
                )
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            msg = f"DeepSeek API error: {e}"
            logger.error(msg)
            return msg

    @staticmethod
    def ask_gigachat(prompt: str) -> str:
        """GigaChat API (с OAuth)."""
        if not GIGACHAT_API_KEY:
            msg = "GigaChat error: GIGACHAT_API_KEY not configured"
            logger.error(msg)
            return msg
        
        try:
            # Получаем access_token
            auth_resp = requests.post(
                GIGACHAT_API_OAUTH_URL,
                headers={"Authorization": f"Bearer {GIGACHAT_API_KEY}"},
                verify=False,
                timeout=10
            )
            auth_resp.raise_for_status()
            token = auth_resp.json().get("access_token")
            if not token:
                msg = "GigaChat error: no access token returned"
                logger.error(msg)
                return msg
            
            # Запрашиваем чат
            api_resp = requests.post(
                GIGACHAT_API_URL,
                json={
                    "model": "GigaChat",
                    "messages": [{"role": "user", "content": prompt}]
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            api_resp.raise_for_status()
            return api_resp.json()["choices"][0]["message"]["content"]
        
        except Exception as e:
            msg = f"GigaChat API error: {e}"
            logger.error(msg)
            return msg

    @staticmethod
    def ask_ollama(prompt: str) -> str:
        """Ollama (локальный HTTP-сервис)."""
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=60
            )
            resp.raise_for_status()
            return resp.json().get("message", {}).get("content", "No content")
        except Exception as e:
            msg = f"Ollama API error: {e}"
            logger.error(msg)
            return msg

    @staticmethod
    def ask_huggingface(prompt: str) -> str:
        """HuggingFace Inference API."""
        if not HF_TOKEN:
            msg = "HuggingFace error: HF_TOKEN not configured"
            logger.error(msg)
            return msg
        
        try:
            resp = requests.post(
                HF_API_URL,
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json={"inputs": prompt},
                timeout=30
            )
            resp.raise_for_status()
            result = resp.json()
            if isinstance(result, list) and result:
                return result[0].get("generated_text", "No generated_text")
            return result.get("generated_text", "No generated_text")
        except Exception as e:
            msg = f"HuggingFace API error: {e}"
            logger.error(msg)
            return msg

    @staticmethod
    def ask_openrouter(prompt: str) -> str:
        """OpenRouter API (агрегатор)."""
        if not OPENROUTER_API_KEY:
            msg = "OpenRouter error: OPENROUTER_API_KEY not configured"
            logger.error(msg)
            return msg
        
        try:
            resp = requests.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://github.com/Librarian-AI",
                    "X-Title": "Librarian-AI"
                },
                json={
                    "model": AI_PROVIDER,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            msg = f"OpenRouter API error: {e}"
            logger.error(msg)
            return msg


# ============ Unified AI Interface with Caching ============

async def get_ai_response(prompt: str) -> str:
    """
    Получает ответ от AI: сначала проверяется кеш, 
    потом вызывается нужный провайдер, а результат сохраняется в кеш.
    """
    # 1) Проверяем кеш
    cached = cache.get_response(prompt)
    if cached is not None:
        return cached

    # 2) Выбираем провайдера
    prov = AI_PROVIDER.lower()
    result = ""
    try:
        if prov == "deepseek":
            result = await AIProvider.ask_deepseek(prompt)
        elif prov == "gigachat":
            result = AIProvider.ask_gigachat(prompt)
        elif prov == "ollama":
            result = AIProvider.ask_ollama(prompt)
        elif prov in ("huggingface", "hf"):
            result = AIProvider.ask_huggingface(prompt)
        elif prov == "openrouter":
            result = AIProvider.ask_openrouter(prompt)
        else:
            result = f"Error: Unknown AI provider '{AI_PROVIDER}'"
            logger.error(result)
    except Exception as e:
        result = f"AI request failed: {e}"
        logger.error(result)

    # 3) Сохраняем результат в кеш, если это не сообщение об ошибке
    if result and not result.lower().startswith("error"):
        cache.set_response(prompt, result, prov)

    return result


# ============ Report Generation ============

def save_analysis_report(
    recommendations: str,
    structure: str,
    changes: str
) -> str:
    """Сохраняет отчёт в формате Markdown."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORTS_DIR, f"analysis_{timestamp}.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Project Analysis Report ({timestamp})\n\n")
        f.write("## Project Structure\n```\n")
        f.write(structure)
        f.write("\n```\n\n## Changes\n```\n")
        f.write(changes)
        f.write("\n```\n\n## Recommendations\n\n")
        f.write(recommendations)
    
    return report_path

def update_reference_version():
    """Обновляет previous_version.zip копированием current_version.zip."""
    if os.path.exists(CUR_ZIP):
        try:
            shutil.copyfile(CUR_ZIP, PREV_ZIP)
        except Exception as e:
            logger.warning(f"Failed to update prev_version.zip: {e}")


# ============ Main Analysis Flow ============

async def analyze_project() -> Optional[str]:
    """Основной асинхронный поток анализа."""
    # 1) Проверяем, что оба архива существуют. Если нет — выводим конкретную ошибку.
    if not os.path.exists(PREV_ZIP):
        logger.error(f"Missing archive: {PREV_ZIP}")
        return None
    if not os.path.exists(CUR_ZIP):
        logger.error(f"Missing archive: {CUR_ZIP}")
        return None
    
    # 2) Распаковываем оба архива во временные директории
    prev_dir = unzip_to_tmp(PREV_ZIP)
    curr_dir = unzip_to_tmp(CUR_ZIP)
    
    try:
        # 3) Структура текущей версии
        curr_files = gather_files(curr_dir, FILE_EXTENSIONS)
        structure = build_project_summary(curr_dir, curr_files)
        
        # 4) Сравниваем с предыдущей версией
        changes_dict   = diff_files(prev_dir, curr_dir)
        changes_report = build_changes_report(changes_dict)
        
        # 5) Формируем единый prompt
        prompt = (
            "Project structure:\n```\n" + structure + "\n```\n\n"
            "Recent changes:\n```\n" + changes_report + "\n```\n\n"
            "Provide recommendations:\n"
            "1) Potential bugs to check\n"
            "2) Areas needing tests\n"
            "3) Refactoring opportunities\n"
            "4) Architectural improvements"
        )
        
        # 6) Запрашиваем у AI
        recommendations = await get_ai_response(prompt)
        
        # 7) Сохраняем отчёт
        report_path = save_analysis_report(
            recommendations,
            structure,
            changes_report
        )
        
        # 8) Обновляем prev_version.zip
        update_reference_version()
        
        return report_path
    
    finally:
        # 9) Удаляем временные папки и чистим старые записи кеша
        shutil.rmtree(prev_dir, ignore_errors=True)
        shutil.rmtree(curr_dir, ignore_errors=True)
        cache.cleanup_old_entries(days_old=30)

def analyze_and_report() -> Optional[str]:
    """
    Синхронная обёртка над async-функцией analyze_project(),
    чтобы можно было вызывать из runner.py как обычную функцию.
    """
    import asyncio
    return asyncio.run(analyze_project())
