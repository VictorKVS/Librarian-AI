# 📄 test_gigachat.py
# 📍 Назначение: Юнит-тесты для клиента GigaChatLLM, включая кэш, очередь, degraded mode, CloudWatch и уведомленияъ
# Фоновая задача для отправки метрик в CloudWatch добавлена в виде теста test_background_push_to_cloudwatch. Она проверяет, 
# что функция push_all_metrics_to_cloudwatch корректно вызывает CloudWatch API. 
# 📦 Расположение: tests/
# 🧪 Зависимости: pytest, pytest-asyncio, httpx, unittest.mock, cloudwatch sdk

import pytest
import asyncio
from httpx import AsyncClient, Response, Request
from httpx._transports.mock import MockTransport
from your_module import GigaChatLLM, ChatMessage, push_to_cloudwatch, RateLimiter, NotificationService  # Замените на фактическое имя модуля
from unittest.mock import AsyncMock, patch, MagicMock
import time

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
    push_to_cloudwatch("TestMetric", 123.45, dimensions=[{"Name": "Environment", "Value": "test"}])
    mock_put.assert_called_once()
    args = mock_put.call_args[1]
    assert any(dim["Name"] == "Environment" and dim["Value"] == "test" for dim in args['MetricData'][0]['Dimensions'])

@pytest.mark.asyncio
async def test_high_queue_logging(caplog):
    llm = GigaChatLLM()
    llm.queue = asyncio.Queue(maxsize=10)
    for _ in range(9):
        await llm.queue.put(([], asyncio.Future()))
    await llm.worker()  # запустит одну итерацию и логнет очередь
    assert any("High queue size" in rec.message for rec in caplog.records)

@pytest.mark.asyncio
async def test_uptime_metric(monkeypatch):
    from your_module import push_to_cloudwatch
    mock_time = time.time() - 500
    with patch("your_module.start_time", mock_time):
        with patch("your_module.cloudwatch.put_metric_data") as mock_push:
            push_to_cloudwatch("Uptime", time.time() - mock_time, dimensions=[{"Name": "Stage", "Value": "test"}])
            mock_push.assert_called_once()

@pytest.mark.asyncio
async def test_empty_response_count(monkeypatch):
    from your_module import EMPTY_RESPONSE_COUNT, push_to_cloudwatch
    EMPTY_RESPONSE_COUNT.inc()
    with patch("your_module.cloudwatch.put_metric_data") as mock_push:
        push_to_cloudwatch("EmptyResponseCount", EMPTY_RESPONSE_COUNT._value.get(), dimensions=[{"Name": "Stage", "Value": "test"}])
        mock_push.assert_called_once()

@pytest.mark.asyncio
async def test_retry_count_metric(monkeypatch):
    from your_module import RETRY_COUNT, push_to_cloudwatch
    RETRY_COUNT.inc(2)
    with patch("your_module.cloudwatch.put_metric_data") as mock_push:
        push_to_cloudwatch("RetryCount", RETRY_COUNT._value.get(), dimensions=[{"Name": "Stage", "Value": "test"}])
        mock_push.assert_called_once()

@pytest.mark.asyncio
async def test_rate_limiter_wait():
    limiter = RateLimiter(10)
    before = time.time()
    await limiter.wait()
    after = time.time()
    assert after >= before

@pytest.mark.asyncio
async def test_shutdown_cleanup():
    llm = GigaChatLLM()
    await llm.shutdown()
    for task in llm.workers:
        assert task.cancelled() or task.done()

@patch("smtplib.SMTP")
def test_notification_service_email(mock_smtp):
    settings.admin_email = "test@example.com"
    settings.smtp_server = "smtp.example.com"
    settings.smtp_username = "user"
    settings.smtp_password = "pass"

    NotificationService.send_email("Test Subject", "Body")
    mock_smtp.assert_called_once()

@patch("requests.post")
def test_notification_service_slack(mock_post):
    settings.slack_webhook_url = "https://hooks.slack.com/services/test"

    NotificationService.send_slack("Test message")
    mock_post.assert_called_once()

# Фоновая задача CloudWatch push
@pytest.mark.asyncio
async def test_background_push_to_cloudwatch(monkeypatch):
    from your_module import push_all_metrics_to_cloudwatch
    with patch("your_module.cloudwatch.put_metric_data") as mock_push:
        task = asyncio.create_task(push_all_metrics_to_cloudwatch())
        await asyncio.sleep(0.1)
        task.cancel()
        mock_push.assert_called()
