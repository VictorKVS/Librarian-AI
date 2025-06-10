# 📄 Файл: api/metrics.py
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter(
    prefix="/api/v1",
    tags=["Monitoring"]
)

@router.get("/metrics", summary="Prometheus metrics endpoint")
def metrics():
    """
    Возвращает метрики в формате Prometheus (для Grafana/Prometheus scrape).
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
