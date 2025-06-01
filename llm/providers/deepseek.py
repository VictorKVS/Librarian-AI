# 📄 Файл: deepseek.py
# 📂 Путь: librarian_ai/llm/providers/deepseek.py

import aiohttp
import logging
from typing import List, Optional, AsyncGenerator
from .base_llm import BaseLLM, ModelInfo, ModelType

logger = logging.getLogger(__name__)

class DeepSeekProvider(BaseLLM):
    def _initialize_model_info(self) -> ModelInfo:
        return ModelInfo(
            name="DeepSeek-V3",
            provider="deepseek",
            model_type=ModelType.CHAT,
            context_length=128000,
            supports_streaming=False,
            supports_embeddings=False,
            version="3.0",
            cost_per_token=None
        )

    async def _async_init(self):
        self.base_url = self.config.get("base_url", "https://api.deepseek.com/v1")
        self.api_key = self.config.get("api_key")
        if not self.api_key:
            raise ValueError("DeepSeekProvider requires 'api_key' in config")

    async def generate_async(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024,
        **kwargs
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/chat/completions", json=payload, headers=headers) as resp:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Ошибка в DeepSeek: {e}")
            return "Ошибка генерации (DeepSeek)"

    async def _stream_impl(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        raise NotImplementedError("DeepSeek не поддерживает потоковый вывод")

    async def _get_embeddings_impl(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("DeepSeek пока не поддерживает эмбеддинги")

    async def _check_availability(self) -> bool:
        try:
            result = await self.generate_async("Тест")
            return isinstance(result, str) and len(result) > 0
        except:
            return False
