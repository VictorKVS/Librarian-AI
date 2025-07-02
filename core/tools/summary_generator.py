# 📂 core/tools/summary_generator.py
from typing import List, Dict, Optional
from enum import Enum
import re
from dataclasses import dataclass
from llm.llm_router import query_llm  # Ваш адаптер для LLM

class ContentType(Enum):
    TECHNICAL = "technical"
    LEGAL = "legal"
    LITERARY = "literary"
    BUSINESS = "business"
    GENERAL = "general"

@dataclass
class SummaryConfig:
    length: str = "medium"  # short/medium/long
    style: str = "professional"
    temperature: float = 0.7

class UniversalSummaryGenerator:
    def __init__(self, llm_backend: str = "gpt-4"):
        self.llm = LLMClient(llm_backend)
        self.role_profiles = self._load_role_profiles()

    def generate_summary(
        self,
        text: str,
        language: str = "ru",
        config: Optional[SummaryConfig] = None,
        custom_role: Optional[str] = None
    ) -> Dict:
        """Генерирует summary с автоматическим определением ролей"""
        config = config or SummaryConfig()
        
        # Анализ контента
        content_type = self._detect_content_type(text)
        suggested_roles = self._suggest_roles(text, content_type)
        
        # Генерация summary для каждой роли
        summaries = {}
        for role in suggested_roles:
            prompt = self._build_prompt(text, role, language, config)
            summaries[role.name] = self._clean_result(
                self.llm.query(prompt),
                role
            )
        
        # Кастомная роль если требуется
        if custom_role:
            prompt = self._build_custom_prompt(text, custom_role, language, config)
            summaries[custom_role] = self._clean_result(
                self.llm.query(prompt),
                custom_role
            )
        
        return {
            "content_type": content_type.value,
            "language": language,
            "summaries": summaries,
            "suggested_roles": [r.name for r in suggested_roles]
        }

    def _detect_content_type(self, text: str) -> ContentType:
        """Определяет тип контента"""
        text_lower = text.lower()
        if re.search(r"(техническ|код|алгоритм)", text_lower):
            return ContentType.TECHNICAL
        elif re.search(r"(закон|статья|регуляц)", text_lower):
            return ContentType.LEGAL
        elif re.search(r"(литератур|роман|персонаж)", text_lower):
            return ContentType.LITERARY
        elif re.search(r"(бизнес|стартап|маркетинг)", text_lower):
            return ContentType.BUSINESS
        return ContentType.GENERAL

    def _suggest_roles(self, text: str, content_type: ContentType) -> List[Role]:
        """Предлагает релевантные роли"""
        role_rules = {
            ContentType.TECHNICAL: [
                Role.DEVELOPER, 
                Role.ARCHITECT,
                Role.TECH_LEAD
            ],
            ContentType.LEGAL: [
                Role.LAWYER,
                Role.COMPLIANCE,
                Role.POLICY_MAKER
            ],
            ContentType.LITERARY: [
                Role.LITERARY_CRITIC,
                Role.HISTORIAN,
                Role.PSYCHOLOGIST
            ],
            ContentType.BUSINESS: [
                Role.CEO,
                Role.MARKETER,
                Role.INVESTOR
            ]
        }
        return role_rules.get(content_type, [Role.GENERAL_READER])

    def _build_prompt(
        self,
        text: str,
        role: Role,
        language: str,
        config: SummaryConfig
    ) -> str:
        """Строит промт для LLM"""
        length_map = {
            "short": "3-5 предложений",
            "medium": "1 абзац",
            "long": "развернутый анализ"
        }
        
        return f"""
        [Role]: {role.value}
        [Language]: {language}
        [Task]: Create {length_map[config.length]} summary focusing on:
        - Key points relevant to {role.value}
        - Practical implications
        - {role.value}-specific terminology
        
        [Style]: {config.style}
        [Text]: {text[:10000]}... [truncated]
        """

    def _build_custom_prompt(
        self,
        text: str,
        role: str,
        language: str,
        config: SummaryConfig
    ) -> str:
        """Промт для кастомных ролей"""
        return f"""
        Summarize this text from {role}'s perspective in {language}.
        Focus on aspects that would interest {role}.
        Length: {config.length}, Style: {config.style}
        
        Text: {text[:10000]}... [truncated]
        """

    def _clean_result(self, text: str, role: str) -> str:
        """Очистка и постобработка"""
        text = re.sub(r"\n+", "\n", text).strip()
        return f"🔹 [{role.upper()} SUMMARY]:\n{text}"

# 📂 models.py (дополнительно)
class Role(Enum):
    DEVELOPER = "Software Developer"
    ARCHITECT = "System Architect"
    TECH_LEAD = "Tech Lead"
    LAWYER = "Lawyer"
    COMPLIANCE = "Compliance Officer"
    POLICY_MAKER = "Policy Maker"
    LITERARY_CRITIC = "Literary Critic"
    HISTORIAN = "Historian"
    PSYCHOLOGIST = "Psychologist"
    CEO = "CEO"
    MARKETER = "Marketer"
    INVESTOR = "Investor"
    GENERAL_READER = "General Reader"