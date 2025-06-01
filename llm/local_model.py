# 📄 Файл: local_model.py
# 📂 Путь: librarian_ai/llm/local_model.py
""""
Установить: pip install transformers torch

Можно использовать любую поддерживаемую модель: gpt2, EleutherAI/gpt-neo-1.3B, NousResearch/llama-2-7b-hf и т.д.

Работает в связке с llm_router.py"""

import asyncio
import logging
from typing import List, AsyncGenerator
from .providers.base_llm import BaseLLM, ModelInfo, ModelType

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
except ImportError:
    AutoTokenizer = None
    AutoModelForCausalLM = None

logger = logging.getLogger(__name__)

class LocalLLM(BaseLLM):
    def _initialize_model_info(self) -> ModelInfo:
        return ModelInfo(
            name="LocalModel",
            provider="local",
            model_type=ModelType.CHAT,
            context_length=2048,
            supports_streaming=False,
            supports_embeddings=False,
            version="0.1",
            description="Локальная LLM на базе transformers"
        )

    async def _async_init(self):
        if not AutoTokenizer or not AutoModelForCausalLM:
            raise ImportError("🤖 Не установлены transformers. pip install transformers torch")

        model_path = self.config.get("model_path", "gpt2")
        device = self.config.get("device", "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        self.model.to(device)
        self.device = device

        logger.info(f"🧠 Локальная модель загружена: {model_path} [{device}]")

    async def generate_async(self, prompt: str, max_tokens: int = 200, **kwargs) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=kwargs.get("temperature", 0.7) > 0,
            temperature=kwargs.get("temperature", 0.7),
        )
        result = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return result[len(prompt):].strip()

    async def _stream_impl(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        response = await self.generate_async(prompt, **kwargs)
        yield response

    async def _get_embeddings_impl(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError("Эмбеддинги не поддерживаются в базовой локальной модели")

    async def _check_availability(self) -> bool:
        return self.model is not None