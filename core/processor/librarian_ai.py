# 📄 core/librarian_ai.py
# 📄 core/librarian_ai.py
from typing import Dict, List, Optional
from db.service import get_session_entities, get_knowledge_graph
from llm.llm_router import query_llm
from config.secrets import ANALYSIS_PROVIDER
import logging

logger = logging.getLogger(__name__)


class LibrarianAI:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or ANALYSIS_PROVIDER

    def analyze_session(self, session_id: str) -> Dict:
        """
        Анализирует сессию: извлекает сущности, граф знаний и формирует логические выводы
        """
        logger.info(f"🔍 Анализ сессии: {session_id}")

        entities = get_session_entities(session_id)
        graph = get_knowledge_graph(session_id)

        if not entities:
            logger.warning("❌ Нет сущностей в сессии")
            return {"insights": [], "actions": [], "status": "no_entities"}

        summary_prompt = self._build_prompt(entities, graph)
        logger.debug(f"🧠 Промт LLM:\n{summary_prompt}")

        response = query_llm(summary_prompt, provider=self.provider)

        return {
            "insights": self._extract_insights(response),
            "actions": self._extract_actions(response),
            "raw": response
        }

    def _build_prompt(self, entities: List[Dict], graph: Dict) -> str:
        """
        Формирует промт для LLM на основе сущностей и графа
        """
        entity_text = "\n".join([f"- {e['type']}: {e['value']}" for e in entities])
        graph_summary = f"Обнаружено {len(graph.get('nodes', []))} узлов и {len(graph.get('edges', []))} связей."

        return f"""
        Проведи анализ сессии.
        🧩 Сущности:
        {entity_text}
        
        🔗 Граф знаний:
        {graph_summary}
        
        📌 Вопросы:
        1. Какие ключевые выводы можно сделать?
        2. Есть ли признаки нарушений, угроз, закономерностей?
        3. Какие действия ты рекомендуешь?

        Ответ представь в формате:
        - [Вывод 1] ...
        - [Рекомендация 1] ...
        """

    def _extract_insights(self, response: str) -> List[str]:
        """Извлекает ключевые выводы"""
        return [line.strip("-• ") for line in response.splitlines() if "вывод" in line.lower()]

    def _extract_actions(self, response: str) -> List[str]:
        """Извлекает рекомендации"""
        return [line.strip("-• ") for line in response.splitlines() if "рекоменд" in line.lower()]
