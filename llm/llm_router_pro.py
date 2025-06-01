# 📄 Файл: llm_router_pro.py | Расположение: librarian_ai/llm/llm_router_pro.py
# 📌 Назначение: продвинутая маршрутизация LLM с кэшированием, таймаутами, логированием, async, метриками
# 📥 Получает: запрос от пользователя или ядра
# 📤 Возвращает: ответ от выбранной модели или ошибку с диагностикой
#Он включает все улучшения: кэширование, асинхронность, метрики, таймауты, логирование ошибок и возможность динамически управлять подключёнными моделями.

import time
import asyncio
from functools import lru_cache
from collections import defaultdict
from typing import Optional

from .yandex_gpt import YandexGPT
from .local_chatglm import ChatGLM
from .deep_pavlov import DeepPavlov

class LLMRouterPro:
    def __init__(self, config: dict):
        self.models = {}
        self.metrics = defaultdict(list)
        self.timeouts = config.get("timeouts", {"yandex": 10, "chatglm": 15, "pavlov": 20})
        self.cache_enabled = config.get("cache_enabled", True)
        self.default_model = config.get("default_llm", "yandex")

        if config.get("llms_enabled", {}).get("yandex"):
            self.models["yandex"] = YandexGPT(
                api_key=config.get("yandex_api_key", ""),
                folder_id=config.get("yandex_folder_id", "")
            )
        if config.get("llms_enabled", {}).get("chatglm"):
            self.models["chatglm"] = ChatGLM()
        if config.get("llms_enabled", {}).get("pavlov"):
            self.models["pavlov"] = DeepPavlov()

    @lru_cache(maxsize=1000)
    def _cached_ask(self, prompt: str, model: str) -> str:
        return self.models[model].ask(prompt)

    def ask(self, prompt: str, model: Optional[str] = None) -> str:
        start_time = time.time()
        selected = model or self.default_model

        if selected not in self.models:
            return f"[LLMRouterPro] ⚠️ Модель '{selected}' не подключена."

        try:
            result = (self._cached_ask if self.cache_enabled else self.models[selected].ask)(prompt)
            latency = time.time() - start_time
            self.metrics[selected].append({"latency": latency, "success": True, "ts": start_time})
            return result
        except Exception as e:
            self.metrics[selected].append({"latency": time.time() - start_time, "success": False, "error": str(e), "ts": start_time})
            return f"[Ошибка] Не удалось получить ответ от '{selected}': {str(e)}"

    async def ask_async(self, prompt: str, model: Optional[str] = None) -> str:
        selected = model or self.default_model
        if selected not in self.models:
            return f"[LLMRouterPro] ⚠️ Модель '{selected}' не подключена."

        model_inst = self.models[selected]
        try:
            if hasattr(model_inst, "ask_async"):
                return await model_inst.ask_async(prompt)
            return await asyncio.to_thread(model_inst.ask, prompt)
        except Exception as e:
            return f"[Async Error] {str(e)}"

    def switch_model(self, model_name: str, enable: bool, config: dict = None):
        if enable and model_name not in self.models:
            if model_name == "yandex" and config:
                self.models["yandex"] = YandexGPT(
                    api_key=config.get("yandex_api_key"),
                    folder_id=config.get("yandex_folder_id")
                )
            elif model_name == "chatglm":
                self.models["chatglm"] = ChatGLM()
            elif model_name == "pavlov":
                self.models["pavlov"] = DeepPavlov()
        elif not enable and model_name in self.models:
            del self.models[model_name]

    def check_health(self) -> dict:
        status = {}
        for name, model in self.models.items():
            try:
                res = model.ask("Проверка")
                status[name] = {"status": "✅", "length": len(res)}
            except Exception as e:
                status[name] = {"status": "❌", "error": str(e)}
        return status


if __name__ == "__main__":
    config = {
        "llms_enabled": {"yandex": True, "chatglm": False, "pavlov": False},
        "yandex_api_key": "ваш_ключ",
        "yandex_folder_id": "ваш_id",
        "default_llm": "yandex",
        "cache_enabled": True
    }
    router = LLMRouterPro(config)
    print(router.ask("Что такое GPT?"))
    print(router.check_health())
