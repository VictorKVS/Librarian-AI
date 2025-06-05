# utils/metrics.py
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter("librarian_requests_total", "Количество HTTP-запросов", ["endpoint"])
REQUEST_LATENCY = Histogram("librarian_request_latency_seconds", "Время обработки запроса", ["endpoint"])

def track_request(endpoint: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            REQUEST_COUNT.labels(endpoint=endpoint).inc()
            with REQUEST_LATENCY.labels(endpoint=endpoint).time():
                return func(*args, **kwargs)
        return wrapper
    return decorator