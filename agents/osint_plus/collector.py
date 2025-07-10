#scraper.py

import requests
from bs4 import BeautifulSoup
import csv
import os
from typing import List, Optional, Dict
import asyncio
import aiohttp
import logging
from logging.handlers import RotatingFileHandler
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import sqlite3
import random
from datetime import datetime
from python_anticaptcha import AnticaptchaClient, NoCaptchaTaskProxyless
from celery import Celery
from prometheus_client import start_http_server, Counter
from config import (
    OUTPUT_DIR,
    HEADERS_LIST,
    PROXIES,
    TARGET_URLS,
    MAX_PAGES,
    ARTICLE_TAG,
    TITLE_TAG,
    CONTENT_SELECTOR,
    DYNAMIC_LOADING,
    USE_PROXY,
    REQUEST_DELAY,
    MAX_RETRIES,
    ANTICAPTCHA_KEY
)

# Prometheus metrics
SCRAPED_PAGES = Counter('scraped_pages', 'Total scraped pages')
SCRAPE_ERRORS = Counter('scrape_errors', 'Total scraping errors')

app = Celery('osint_tasks', broker='redis://localhost:6379/0')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_handler = RotatingFileHandler(
    'osint_scraper.log', maxBytes=5*1024*1024, backupCount=3
)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)

class OSINTScraper:
    def __init__(self):
        """Инициализация сессии, базы данных и выходного каталога."""
        self.session = requests.Session()
        self.output_dir = OUTPUT_DIR
        self.create_output_dir()
        self.db_conn = self.init_db()

    def create_output_dir(self):
        """Создаёт выходной каталог, если он не существует."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            logger.info(f"Создана директория {self.output_dir}")

    def init_db(self):
        """Инициализирует SQLite базу данных для хранения статей."""
        conn = sqlite3.connect('osint_articles.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY,
                url TEXT,
                title TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                source TEXT
            )
        ''')
        conn.commit()
        return conn

    def get_random_headers(self):
        """Выбирает случайный User-Agent из списка."""
        return {'User-Agent': random.choice(HEADERS_LIST)}

    def get_random_proxy(self):
        """Возвращает настройки прокси, если включено."""
        return PROXIES if USE_PROXY else None

    async def fetch_async(self, url: str) -> Optional[str]:
        """Асинхронно загружает страницу.
        Args:
            url (str): Ссылка для загрузки
        Returns:
            str | None: HTML содержимое страницы
        """
        try:
            async with aiohttp.ClientSession(headers=self.get_random_headers()) as session:
                async with session.get(url, proxy=self.get_random_proxy().get('http') if self.get_random_proxy() else None) as response:
                    response.raise_for_status()
                    SCRAPED_PAGES.inc()
                    return await response.text()
        except Exception as e:
            SCRAPE_ERRORS.inc()
            logger.error(f"Ошибка при асинхронном запросе {url}: {e}")
            return None

    def fetch_sync(self, url: str, retry: int = MAX_RETRIES) -> Optional[str]:
        """Синхронно загружает страницу с повторными попытками."""
        for attempt in range(retry):
            try:
                response = self.session.get(
                    url,
                    headers=self.get_random_headers(),
                    proxies=self.get_random_proxy(),
                    timeout=10
                )
                response.raise_for_status()
                SCRAPED_PAGES.inc()
                return response.text
            except requests.RequestException as e:
                SCRAPE_ERRORS.inc()
                logger.warning(f"Попытка {attempt + 1} для {url} не удалась: {e}")
                if attempt < retry - 1:
                    import time
                    time.sleep(REQUEST_DELAY * (attempt + 1))
                continue
        return None

    def parse_article(self, article) -> Dict[str, str]:
        """Извлекает данные из статьи.
        Returns:
            dict: Заголовок, контент и временная метка
        """
        title = article.find(TITLE_TAG).get_text(strip=True) if article.find(TITLE_TAG) else "No Title"
        content = ' '.join([p.get_text(strip=True) for p in article.select(CONTENT_SELECTOR)]) if CONTENT_SELECTOR else article.get_text(separator='\n', strip=True)
        return {
            'title': title,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }

    def scrape_page(self, html: str, source: str) -> List[Dict]:
        """Парсит HTML страницу и извлекает статьи.
        Args:
            html (str): HTML содержимое
            source (str): URL источника
        Returns:
            list: Список словарей статей
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        for article in soup.find_all(ARTICLE_TAG):
            try:
                article_data = self.parse_article(article)
                article_data['source'] = source
                articles.append(article_data)
            except Exception as e:
                logger.error(f"Ошибка парсинга статьи: {e}")
        return articles

    def handle_captcha(self, driver):
        """Решает CAPTCHA с использованием AntiCaptcha."""
        try:
            site_key = driver.find_element(By.CLASS_NAME, 'g-recaptcha').get_attribute('data-sitekey')
            url = driver.current_url
            client = AnticaptchaClient(ANTICAPTCHA_KEY)
            task = NoCaptchaTaskProxyless(website_url=url, website_key=site_key)
            job = client.createTask(task)
            job.join()
            token = job.get_solution_response()
            driver.execute_script(f"document.getElementById('g-recaptcha-response').innerHTML = '{token}';")
            logger.info("CAPTCHA решена")
        except Exception as e:
            logger.error(f"Ошибка при решении CAPTCHA: {e}")

    def scrape_dynamic(self, url: str):
        """Скрапинг страниц с динамическим контентом через Selenium."""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')

        driver = webdriver.Chrome(options=options)
        try:
            driver.get(url)
            if 'g-recaptcha' in driver.page_source:
                self.handle_captcha(driver)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, ARTICLE_TAG))
            )
            html = driver.page_source
            return self.scrape_page(html, url)
        except Exception as e:
            logger.error(f"Ошибка Selenium для {url}: {e}")
            return []
        finally:
            driver.quit()

    def save_article_to_db(self, article: Dict):
        """Сохраняет статью в базу данных."""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
                INSERT INTO articles (url, title, content, source)
                VALUES (?, ?, ?, ?)
            ''', (article.get('url'), article['title'], article['content'], article['source']))
            self.db_conn.commit()
        except Exception as e:
            logger.error(f"Ошибка сохранения в БД: {e}")

    def save_to_csv(self, data: List[Dict], filename: str = 'osint_articles.csv'):
        """Сохраняет статьи в CSV файл."""
        try:
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['title', 'content', 'source', 'timestamp'])
                writer.writeheader()
                writer.writerows(data)
            logger.info(f"Данные сохранены в {filepath}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении CSV: {e}")

    async def run_async(self):
        """Асинхронный запуск парсера."""
        tasks = []
        for url in TARGET_URLS:
            if DYNAMIC_LOADING:
                articles = self.scrape_dynamic(url)
                for article in articles:
                    self.save_article_to_db(article)
            else:
                tasks.append(self.scrape_async(url))

        results = await asyncio.gather(*tasks)
        all_articles = [article for sublist in results for article in sublist]
        self.save_to_csv(all_articles)

    def run_sync(self):
        """Синхронный запуск парсера."""
        all_articles = []
        for url in TARGET_URLS:
            if DYNAMIC_LOADING:
                articles = self.scrape_dynamic(url)
            else:
                articles = self.scrape_sync(url)

            for article in articles:
                self.save_article_to_db(article)
            all_articles.extend(articles)

        self.save_to_csv(all_articles)

    def close(self):
        """Закрытие сессии и БД соединения."""
        self.session.close()
        self.db_conn.close()
        logger.info("Ресурсы освобождены")

@app.task(bind=True, max_retries=3)
def scrape_task(self, url):
    """Celery задача для парсинга URL."""
    scraper = OSINTScraper()
    try:
        articles = scraper.scrape_sync(url)
        for article in articles:
            scraper.save_article_to_db(article)
        return articles
    except Exception as e:
        self.retry(exc=e)
    finally:
        scraper.close()

if __name__ == "__main__":
    import time
    start_http_server(8000)  # Запуск Prometheus метрик
    scraper = OSINTScraper()
    try:
        start_time = time.time()
        if DYNAMIC_LOADING:
            scraper.run_sync()
        else:
            asyncio.run(scraper.run_async())
        logger.info(f"Парсинг завершен за {time.time() - start_time:.2f} секунд")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
    finally:
        scraper.close()

#На следующем этапе стоит реализовать:

#Обработку CAPTCHA — с помощью сервисов 2Captcha/AntiCaptcha.

#Распределённую обработку — используя Celery + Redis.

#Универсальные тесты — с использованием unittest и mock.

#Документацию функций — через docstrings.

#Мониторинг Prometheus — для отслеживания активности.

#Контейнеризацию — через Dockerfile.

#Интеграцию .env и dotenv — для переменных окружения."