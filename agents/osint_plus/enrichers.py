import csv
import os
import sqlite3
import logging

def export_to_csv(articles: list, filepath: str):
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=articles[0].keys())
        writer.writeheader()
        writer.writerows(articles)
    logging.info(f"Экспортировано в CSV: {filepath}")

def export_to_db(articles: list, db_path: str = 'osint_articles.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY,
            title TEXT,
            content TEXT,
            source TEXT,
            timestamp TEXT
        )
    ''')
    for article in articles:
        cursor.execute('''
            INSERT INTO articles (title, content, source, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (article['title'], article['content'], article['source'], article['timestamp']))
    conn.commit()
    conn.close()
    logging.info(f"Экспортировано в БД: {db_path}")
