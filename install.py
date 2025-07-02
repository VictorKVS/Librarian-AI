# 📄 Файл: install.py | Расположение: librarian_ai/install.py
# 📌 Назначение: инициализация проекта Librarian AI — создание файлов из шаблонов
# 📥 Получает: шаблонные .tpl-файлы из папки templates/
# 📤 Передаёт: готовые .py, .yaml и .md файлы в нужные директории проекта
# ⚠️ Папки должны быть созданы заранее вручную

import os

file_templates = {
    "main.py": "templates/main.py.tpl",
    "config/config.yaml": "templates/config.yaml.tpl",
    "llm/base.py": "templates/base_llm.py.tpl",
    "core/loader.py": "templates/loader.py.tpl",
    "README.md": "templates/readme.md.tpl",
    "agents/osint_plus/agent.yaml": "# YAML-описание OSINT агента\nname: osint_plus\nversion: 0.1\nrole: collector\n",
    "config/e_full.yaml": "# Полное описание агента Librarian AI в формате AgentDNA\nname: librarian_ai\nversion: 0.3\nrole: document_librarian\ntags: [\"NLP\", \"RAG\", \"KnowledgeBase\"]\ndescription: |\n  Агент для укладки, классификации и векторизации документов, сбора знаний и работы с ИИ.\nauthor: Viktor Kulichenko\norganization: AgentFarm Systems\ncompatibility: [\"OSINT+\", \"GigaChat\", \"YandexGPT\"]\n"
}

for path, tpl_path in file_templates.items():
    full_path = f"librarian_ai/{path}"
    if not os.path.exists(full_path):
        if tpl_path.endswith(".tpl"):
            with open(f"librarian_ai/{tpl_path}", "r", encoding="utf-8") as tpl_file:
                content = tpl_file.read()
        else:
            content = tpl_path or ""
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)

print("✅ Базовые файлы проекта Librarian AI созданы.")
