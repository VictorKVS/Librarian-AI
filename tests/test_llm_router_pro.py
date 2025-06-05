# 📄 Файл: test_llm_router_pro.py | Расположение: tests/test_llm_router_pro.py
# 📌 Назначение: модульное, интеграционное и нагрузочное тестирование LLMRouterPro

import unittest
from unittest.mock import MagicMock
from librarian_ai.llm.llm_router_pro import LLMRouterPro

class TestLLMRouterPro(unittest.TestCase):
    def setUp(self):
        self.config = {
            "llms_enabled": {"yandex": True},
            "yandex_api_key": "test",
            "yandex_folder_id": "folder",
            "default_llm": "yandex",
            "cache_enabled": True
        }
        self.router = LLMRouterPro(self.config)

        # Подменим настоящую модель на заглушку
        mock_model = MagicMock()
        mock_model.ask.return_value = "ответ от заглушки"
        self.router.models["yandex"] = mock_model

    def test_ask_default_model(self):
        result = self.router.ask("Привет")
        self.assertEqual(result, "ответ от заглушки")

    def test_unknown_model(self):
        result = self.router.ask("Привет", model="несуществующая")
        self.assertIn("не подключена", result)

    def test_async_mode(self):
        import asyncio
        async def test():
            response = await self.router.ask_async("Что такое async?")
            self.assertEqual(response, "ответ от заглушки")
        asyncio.run(test())

    def test_metrics_collected(self):
        _ = self.router.ask("Кто ты?")
        self.assertIn("yandex", self.router.metrics)
        self.assertTrue(len(self.router.metrics["yandex"]) > 0)

    def test_health_check(self):
        health = self.router.check_health()
        self.assertIn("yandex", health)
        self.assertEqual(health["yandex"]["status"], "✅")


if __name__ == '__main__':
    unittest.main()
