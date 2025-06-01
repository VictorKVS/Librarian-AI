from typing import List, Dict

class Parser:
    def tokenize(self, text: str, language: str) -> List[str]:
        return text.split()
    def filter_tokens(self, tokens: List[str]) -> List[str]:
        return [t for t in tokens if t.isalnum()]
    def parse(self, text: str, language: str) -> Dict[str, List[str]]:
        tokens = self.tokenize(text, language)
        return {"tokens": self.filter_tokens(tokens)}
    

from typing import List, Dict

class Parser:
    """Токенизатор и фильтрация текста"""
    def tokenize(self, text: str, language: str) -> List[str]:
        return text.split()

    def filter_tokens(self, tokens: List[str]) -> List[str]:
        return [t for t in tokens if t.isalnum()]

    def parse(self, text: str, language: str) -> Dict[str, List[str]]:
        tokens = self.tokenize(text, language)
        filtered = self.filter_tokens(tokens)
        return {"tokens": filtered}

from typing import List, Dict

class Parser:
    """Токенизатор и фильтрация текста"""
    def tokenize(self, text: str, language: str) -> List[str]:
        return text.split()

    def filter_tokens(self, tokens: List[str]) -> List[str]:
        return [t for t in tokens if t.isalnum()]

    def parse(self, text: str, language: str) -> Dict[str, List[str]]:
        tokens = self.tokenize(text, language)
        filtered = self.filter_tokens(tokens)
        return {"tokens": filtered}