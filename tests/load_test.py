#load_test.py,
import pytest
import asyncio
from httpx import AsyncClient, Response, Request
from httpx._transports.mock import MockTransport
from your_module import GigaChatLLM, ChatMessage, push_to_cloudwatch  # Замените на фактическое имя модуля
from unittest.mock import AsyncMock, patch

"""
Тестовый модуль для GigaChatLLM:
- Проверка успешных запросов
- Проверка невалидных ответов
- Переполнение очереди
- Хит кэша
- Деградированный режим
- Push в CloudWatch
- Логирование при высокой нагрузке

Также поддерживается нагрузочное тестирование через отдельный скрипт load_test.py:
- Имитирует 100 одновременных пользователей
- Замеряет среднее и максимальное время отклика (кэш/прямой API)
- Поддерживает параметры CLI: количество пользователей, размеры очереди, число итераций

"""

@pytest.mark.asyncio
async def test_successful_ask(monkeypatch):
    async def handler(request: Request):
        return Response(200, json={
            "choices": [{"message": {"content": "Hello!"}}]
        })

    transport = MockTransport(handler)
    llm = GigaChatLLM()
    llm.client._transport = transport

    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hi"},
    ]
    response = await llm.cached_ask(messages)
    assert response == "Hello!"

@pytest.mark.asyncio
async def test_invalid_response(monkeypatch):
    async def handler(request: Request):
        return Response(200, json={"choices": [{}]})

    transport = MockTransport(handler)
    llm = GigaChatLLM()
    llm.client._transport = transport

    messages = [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "Hi"},
    ]
    response = await llm.cached_ask(messages)
    assert "GigaChat Error" in response or "Degraded Response" in response

@pytest.mark.asyncio
async def test_queue_overflow():
    llm = GigaChatLLM()
    llm.queue = asyncio.Queue(maxsize=1)

    messages = [
        {"role": "user", "content": "test"}
    ]
    await llm.enqueue_request(messages)

    with pytest.raises(RuntimeError):
        await llm.enqueue_request(messages)

@pytest.mark.asyncio
async def test_cache_hit():
    llm = GigaChatLLM()
    key = (("user", "Hi"),)
    llm.cache[key] = "Cached!"
    response = await llm.cached_ask([{"role": "user", "content": "Hi"}])
    assert response == "Cached!"

@pytest.mark.asyncio
async def test_degraded_mode():
    llm = GigaChatLLM()
    llm.degraded_mode = True
    response = await llm.cached_ask([{"role": "user", "content": "No data"}])
    assert "Degraded Response" in response

@patch("your_module.cloudwatch.put_metric_data")
def test_push_to_cloudwatch(mock_put):
    push_to_cloudwatch("TestMetric", 123.45)
    mock_put.assert_called_once()

@pytest.mark.asyncio
async def test_high_queue_logging(caplog):
    llm = GigaChatLLM()
    llm.queue = asyncio.Queue(maxsize=10)
    for _ in range(9):
        await llm.queue.put(([], asyncio.Future()))
    await llm.worker()  # запустит одну итерацию и логнет очередь
    assert any("High queue size" in rec.message for rec in caplog.records)
