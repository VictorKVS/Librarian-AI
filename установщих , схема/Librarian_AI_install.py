
# ┌────────────────────────────────────────┐
# | 📆 Установщик: Librarian_AI_install.py (Python) |
# └────────────────────────────────────────┘

# install.py — универсальный установщик: может быть переиспользован для создания фабрики агентов, баз документов и др.

"""
install.py — создаёт структуру проекта Librarian AI
"""
import os

folders = [
    "config", "llm", "core", "db", "knowledge/vector_store",
    "utils", "cli", "telegram", "agents/factory", "agents/osint_plus", "templates"
]

file_templates = {
    "main.py": "templates/main.py.tpl",
    "config/config.yaml": "templates/config.yaml.tpl",
    "llm/base.py": "templates/base_llm.py.tpl",
    "core/loader.py": "templates/loader.py.tpl",
    "README.md": "templates/readme.md.tpl",
    "db/librarian.db": None,  # Пустой файл
    "agents/osint_plus/agent.yaml": "# YAML-описание OSINT агента\nname: osint_plus\nversion: 0.1\nrole: collector\n",
    "config/e_full.yaml": "# Полное описание агента Librarian AI в формате AgentDNA\nname: librarian_ai\nversion: 0.3\nrole: document_librarian\ntags: ["NLP", "RAG", "KnowledgeBase"]\ndescription: |
  Агент для укладки, классификации и векторизации документов, сбора знаний и работы с ИИ.\nauthor: Viktor Kulichenko\norganization: AgentFarm Systems\ncompatibility: ["OSINT+", "GigaChat", "YandexGPT"]\n"
}

for folder in folders:
    os.makedirs(f"librarian_ai/{folder}", exist_ok=True)

for path, tpl_path in file_templates.items():
    full_path = f"librarian_ai/{path}"
    if not os.path.exists(full_path):
        if tpl_path and tpl_path.endswith(".tpl"):
            with open(f"librarian_ai/{tpl_path}", "r", encoding="utf-8") as tpl_file:
                content = tpl_file.read()
        else:
            content = tpl_path or ""
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

print("✅ Librarian AI структура с OSINT агентом и e_full.yaml создана.")
