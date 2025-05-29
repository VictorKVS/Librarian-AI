# 📂 llm/llm_router.py
import os
import logging
import requests
from enum import Enum
from typing import Optional, Literal, Dict, Callable
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider(str, Enum):
    """Поддерживаемые LLM-провайдеры"""
    OPENROUTER = "openrouter"  # Бесцензурные модели (Weaver)
    GIGACHAT = "gigachat"      # Бесплатный русскоязычный (Сбер)
    YANDEXGPT = "yandexgpt"    # Yandex Cloud LLM
    MISTRAL = "mistral"        # Локальная модель (без цензуры)
    DOLPHIN = "dolphin"        # Dolphin-Mixtral через OpenRouter

class LLMRouter:
    def __init__(self, default_provider: LLMProvider = LLMProvider.GIGACHAT):
        """Инициализация маршрутизатора"""
        self.default_provider = default_provider
        self._init_providers()
        
    def _init_providers(self) -> Dict[LLMProvider, Callable]:
        """Инициализация провайдеров"""
        self.providers = {
            LLMProvider.OPENROUTER: self._query_openrouter,
            LLMProvider.GIGACHAT: self._query_gigachat,
            LLMProvider.YANDEXGPT: self._query_yandexgpt,
            LLMProvider.DOLPHIN: self._query_dolphin,
            LLMProvider.MISTRAL: self._init_mistral()
        }
    
    def generate(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        **kwargs
    ) -> str:
        """
        Генерация ответа через выбранный провайдер
        Args:
            prompt: Текст запроса
            provider: Провайдер (если None - используется default_provider)
            kwargs: Параметры для модели (temperature, max_tokens и т.д.)
        Returns:
            Ответ LLM
        """
        provider = provider or self.default_provider
        logger.info(f"Используется провайдер: {provider.value}")
        
        try:
            return self.providers[provider](prompt, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка в {provider.value}: {str(e)}")
            return self._fallback(prompt)

    # === Реализации провайдеров ===

    def _query_openrouter(self, prompt: str, **kwargs) -> str:
        """OpenRouter API (Mancer/Weaver)"""
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_KEY')}",
            "HTTP-Referer": "https://librarian.ai",
        }
        data = {
            "model": "mancer/weaver",
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        return response.json()["choices"][0]["message"]["content"]

    def _query_gigachat(self, prompt: str, **kwargs) -> str:
        """GigaChat API (Сбер)"""
        headers = {
            "Authorization": f"Bearer {os.getenv('GIGACHAT_SECRET')}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "GigaChat:latest",
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        response = requests.post(
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15
        )
        return response.json()["choices"][0]["message"]["content"]

    def _query_yandexgpt(self, prompt: str, **kwargs) -> str:
        """YandexGPT API"""
        headers = {
            "Authorization": f"Api-Key {os.getenv('YANDEX_API_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "general",
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        response = requests.post(
            "https://llm.api.cloud.yandex.net/llm/v1alpha/instruct",
            headers=headers,
            json=data,
            timeout=10
        )
        return response.json()["result"]["alternatives"][0]["message"]["text"]

    def _query_dolphin(self, prompt: str, **kwargs) -> str:
        """Dolphin-Mixtral (через OpenRouter)"""
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENROUTER_KEY')}",
        }
        data = {
            "model": "cognitivecomputations/dolphin-mixtral",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            **kwargs
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=15
        )
        return response.json()["choices"][0]["message"]["content"]

    def _init_mistral(self) -> Callable:
        """Ленивая инициализация локальной Mistral"""
        model = None
        tokenizer = None

        def generate(prompt: str, **kwargs) -> str:
            nonlocal model, tokenizer
            if model is None:
                logger.info("Загрузка локальной модели Mistral...")
                model = AutoModelForCausalLM.from_pretrained(
                    "mistralai/Mistral-7B-Instruct-v0.2",
                    device_map="auto",
                    torch_dtype=torch.float16,
                    load_in_4bit=True
                )
                tokenizer = AutoTokenizer.from_pretrained(
                    "mistralai/Mistral-7B-Instruct-v0.2"
                )
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            outputs = model.generate(**inputs, max_new_tokens=512)
            return tokenizer.decode(outputs[0], skip_special_tokens=True)

        return generate

    def _fallback(self, prompt: str) -> str:
        """Резервный механизм при ошибках"""
        logger.warning("Используется резервный провайдер (GigaChat)")
        try:
            return self._query_gigachat(prompt)
        except Exception as e:
            logger.critical("Ошибка fallback провайдера: " + str(e))
            return "Не удалось обработать запрос."

# Глобальный экземпляр маршрутизатора
default_router = LLMRouter()

def query_llm(
    prompt: str,
    provider: Optional[Literal["openrouter", "gigachat", "yandexgpt", "mistral", "dolphin"]] = None,
    **kwargs
) -> str:
    """
    Упрощенный интерфейс для генерации текста
    Args:
        prompt: Текст запроса
        provider: Имя провайдера (если None - используется default_router)
        kwargs: Дополнительные параметры для LLM
    """
    return default_router.generate(
        prompt,
        provider=LLMProvider(provider) if provider else None,
        **kwargs
    )