# 📄 Файл: yandex_gpt.py
# 📂 Путь: librarian_ai/llm/providers/yandex_gpt.py

import aiohttp
import logging
from typing import List, Optional, AsyncGenerator
from .base_llm import BaseLLM, ModelInfo, ModelType

logger = logging.getLogger(__name__)

class YandexGPT(BaseLLM):
    def _initialize_model_info(self) -> ModelInfo:
        return ModelInfo(
            name="YandexGPT",
            provider="yandex",
            model_type=ModelType.CHAT,
            context_length=4000,
            supports_streaming=False,
            supports_embeddings=False,
            version="1.0",
            cost_per_token=None
        )

    async def _async_init(self) -> None:
        self.api_key = self.config.get("api_key")
        self.folder_id = self.config.get("folder_id")
        self.url = self.config.get("url", "https://llm.api.cloud.yandex.net/foundationModels/v1/completion")

        if not self.api_key or not self.folder_id:
            raise ValueError("YandexGPT requires 'api_key' and 'folder_id' in config")

        logger.info("✅ YandexGPT инициализирован")

    async def generate_async(
        self,
        prompt: str,
        *,
        temperature: float = 0.6,
        max_tokens: Optional[int] = 1000,
        **kwargs
    ) -> str:
        headers = {
            "Authorization": f"Api-Key {self.api_key}",
            "x-folder-id": self.folder_id,
            "Content-Type": "application/json"
        }

        payload = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt/latest",
            "completionOptions": {
                "temperature": temperature,
                "maxTokens": max_tokens or 1000,
                "stream": False
            },
            "messages": [{"role": "user", "text": prompt}]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload, headers=headers, timeout=30) as resp:
                    data = await resp.json()
                    return data["result"]["alternatives"][0]["message"]["text"]
        except Exception as e:
            logger.error(f"Ошибка генерации через YandexGPT: {e}")
            return "Ошибка генерации (YandexGPT)"

    async def _stream_impl(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        raise NotImplementedError("YandexGPT не поддерживает стриминг")

    async def _get_embeddings_impl(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("YandexGPT не поддерживает эмбеддинги")

    async def _check_availability(self) -> bool:
        try:
            test = await self.generate_async("Привет", temperature=0.3, max_tokens=20)
            return "Привет" in test
        except Exception as e:
            logger.warning(f"YandexGPT недоступен: {e}")
            return False