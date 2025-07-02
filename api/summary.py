# 📂 api/summary.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Literal
from core.summary_generator import UniversalSummaryGenerator, SummaryConfig
import logging
from datetime import datetime

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

router = APIRouter(
    prefix="/api/v1",
    tags=["summary"],
    responses={404: {"description": "Not found"}}
)

generator = UniversalSummaryGenerator()

# Модели запросов/ответов
class SummaryRequest(BaseModel):
    text: str = Field(..., min_length=50, max_length=100000, example="Полный текст для анализа...")
    language: str = Field("ru", regex="^[a-z]{2}$", example="ru")
    custom_role: Optional[str] = Field(
        None, 
        min_length=3, 
        example="Game Designer",
        description="Кастомная роль для генерации (если не указана - будет автоопределение)"
    )
    length: Literal['short', 'medium', 'long'] = Field("medium", example="medium")
    style: Literal['academic', 'professional', 'casual'] = Field("professional", example="professional")

class SummaryResponse(BaseModel):
    content_type: str
    language: str
    suggested_roles: list[str]
    summaries: dict[str, str]
    processing_time_ms: int

@router.post(
    "/summary",
    response_model=SummaryResponse,
    summary="Генерация мультиперспективного summary",
    description="""Анализирует текст и возвращает summaries для разных профессиональных ролей.
    Поддерживает 48 языков и автоматическое определение тематики.""",
    response_description="Словарь с summary для каждой роли"
)
async def generate_summary(
    request: SummaryRequest,
    http_request: Request
):
    """
    Генерирует адаптивные summaries с возможностью:
    - Автовыбора ролей по содержанию
    - Ручного указания профессии
    - Настройки длины и стиля
    """
    start_time = datetime.now()
    client_ip = http_request.client.host
    
    try:
        logger.info(f"Request from {client_ip} | Language: {request.language} | Chars: {len(request.text)}")
        
        config = SummaryConfig(
            length=request.length,
            style=request.style
        )
        
        result = generator.generate_summary(
            text=request.text,
            language=request.language,
            config=config,
            custom_role=request.custom_role
        )
        
        # Добавляем метрики производительности
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        response = {
            **result,
            "processing_time_ms": int(processing_time)
        }
        
        logger.info(f"Success | Roles: {len(result['summaries'])} | Time: {processing_time:.0f}ms")
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.critical(f"Processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Contact support."
        )

# Примеры для Swagger
@router.get("/examples", include_in_schema=False)
async def get_examples():
    return {
        "legal": {
            "text": "Статья 128 УК РФ предусматривает...",
            "language": "ru",
            "length": "medium"
        },
        "tech": {
            "text": "Python 3.12 introduces new typing features...",
            "custom_role": "Software Engineer",
            "style": "academic"
        }
    }