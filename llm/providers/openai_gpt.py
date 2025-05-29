# 📄 Файл: openai_gpt.py
# 📂 Путь: librarian_ai/llm/providers/openai_gpt.py

import openai
import asyncio
from typing import List, AsyncGenerator, Optional, Dict, Any
from .base_llm import BaseLLM, ModelInfo, ModelType
import logging

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLM):
    def _initialize_model_info(self) -> ModelInfo:
        return ModelInfo(
            name=self.config.get("model", "gpt-4"),
            provider="openai",
            model_type=ModelType.CHAT,
            context_length=128000 if "gpt-4" in self.config.get("model", "") else 4096,
            supports_streaming=True,
            supports_embeddings=True,
            version="2024-05",
            description="OpenAI GPT-3.5/4",
            cost_per_token=0.00002 if "gpt-3.5" in self.config.get("model", "") else 0.0001
        )

    async def _async_init(self):
        openai.api_key = self.config.get("api_key")
        openai.base_url = self.config.get("base_url", "https://api.openai.com/v1")

    async def generate_async(
        self,
        prompt: str,
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 512,
        stream: bool = False,
        **kwargs
    ) -> str:
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.config.get("model", "gpt-4"),
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[OpenAI] Ошибка генерации: {str(e)}")
            raise

    async def _stream_impl(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = 512,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        try:
            stream = await openai.ChatCompletion.acreate(
                model=self.config.get("model", "gpt-4"),
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk["choices"][0]["delta"]
                if "content" in delta:
                    yield delta["content"]
        except Exception as e:
            logger.error(f"[OpenAI] Ошибка потока: {str(e)}")
            yield f"[Ошибка: {e}]"

    async def _get_embeddings_impl(self, texts: List[str]) -> List[List[float]]:
        try:
            response = await openai.Embedding.acreate(
                model="text-embedding-ada-002",
                input=texts
            )
            return [r["embedding"] for r in response["data"]]
        except Exception as e:
            logger.error(f"[OpenAI] Ошибка эмбеддинга: {str(e)}")
            raise

    async def _check_availability(self) -> bool:
        try:
            await openai.Model.alist()
            return True
        except Exception:
            return False