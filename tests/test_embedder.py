# Тестирование модуля Embedder
# tests/test_embedder.py
import pytest
import asyncio
from core.tools.embedder import Embedder, EmbeddingType, CacheInfo


@pytest.fixture
def embedder():
    """
    Инициализация экземпляра класса Embedder с минимальными параметрами для тестирования.
    
    Создаем объект Embedder с моделью минимальной размерности и устройством 'cpu'.
    Для упрощения тестового окружения заменяется реальный механизм кодирования векторов
    на простой метод, возвращающий длину входящего текста.
    """
    # Настройка Embedder с небольшой моделью и малым объемом кэша
    e = Embedder(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        device="cpu",
        cache_size=10,
        embedding_type=EmbeddingType.NONE,
        model_kwargs={},
        max_seq_length=32
    )
    
    # Замещаем синхронный метод кодирования на простую реализацию для тестов
    def dummy_encode(text: str):
        # Генерируем вектор длиной равной количеству символов в тексте
        return [float(len(text))]
    
    # Устанавливаем новую реализацию метода кодирования и сбрасываем кэш
    e._encode_sync_uncached = dummy_encode
    e._setup_caching(cache_size=10)
    return e


@pytest.mark.asyncio
async def test_generate_single(embedder):
    """
    Тест одиночного запроса на генерацию вектора с проверкой попадания/промаха в кэш.
    
    Проверяет, что для нового запроса происходит промах в кэше и возвращается правильный вектор.
    """
    # Очистка кэша перед началом теста
    embedder.clear_cache()
    
    # Генерация вектора для строки "abc"
    result = await embedder.generate("abc")
    
    # Убеждаемся, что результат — список и соответствует ожидаемому значению длины строки
    assert isinstance(result, list)
    assert result == [3.0]
    
    # Получение статистики кэша
    info: CacheInfo = embedder.get_cache_info()
    
    # Должен произойти один промах и ни одного попадания
    assert info.misses == 1
    assert info.hits == 0


@pytest.mark.asyncio
async def test_cache_hit_miss(embedder):
    """
    Тест проверки механизма кэширования при повторных запросах одинаковых строк.
    
    Сначала делается первый запрос ("hello"), потом второй такой же запрос.
    Второй запрос должен попасть в кэш.
    """
    # Очистка кэша перед началом теста
    embedder.clear_cache()
    
    # Первый запрос: ожидается промах в кэше
    await embedder.generate("hello")
    
    # Повторный запрос той же строки: ожидание попадания в кэш
    await embedder.generate("hello")
    
    # Статистика кэша должна показать одно попадание и один промах
    info: CacheInfo = embedder.get_cache_info()
    assert info.misses == 1
    assert info.hits == 1


@pytest.mark.asyncio
async def test_generate_batch(embedder):
    """
    Тест обработки пакета запросов одновременно.
    
    Проверяет обработку нескольких текстов одним вызовом с контролем результатов.
    """
    # Очистка кэша перед началом теста
    embedder.clear_cache()
    
    # Набор текстов разной длины
    texts = ["a", "bb", "ccc"]
    
    # Запуск пакетной генерации с заданием размера батча
    results = await embedder.generate(texts, batch_size=2)
    
    # Проверка правильности результата: каждый элемент списка должен соответствовать длине своего текста
    assert results == [[1.0], [2.0], [3.0]]
    
    # Статистика кэша показывает три промаха, поскольку тексты уникальны
    info: CacheInfo = embedder.get_cache_info()
    assert info.misses == 3
    assert info.hits == 0


def test_model_info(embedder):
    """
    Тест получение информации о модели.
    
    Проверяет правильность формата и содержания сведений о модели, устройстве и параметрах Embedder.
    """
    # Получение информации о конфигурации модели
    info = embedder.get_model_info()
    
    # Проверка типа информации
    assert isinstance(info, dict)
    
    # Тип модели должен быть SentenceTransformer или AutoModel
    assert info.get("model_type") in {"SentenceTransformer", "AutoModel"}
    
    # Устройство должно быть cpu
    assert info.get("device") == "cpu"
    
    # Тип встраивания NONE
    assert info.get("embedding_type") == EmbeddingType.NONE.value
    
    # Длина последовательности должна быть указана
    assert "max_seq_length" in info
