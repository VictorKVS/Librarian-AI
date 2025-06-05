import os
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QLabel, QLineEdit, QTextEdit, QFileDialog, QMessageBox
)

class RepoManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Repo Manager (Lite)")
        self.setGeometry(300, 300, 500, 400)
        
        # Основные настройки
        self.repo_path = ""
        self.yandex_token = "f940f84e7b44493db295cb4d2beb720b"  # Ваш токен
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # Поля ввода
        self.repo_url = QLineEdit("https://github.com/bigcode-project/starcoder.git")
        self.local_path = QLineEdit("G:\\Librarian AI\\.1RepoManager")
        
        # Кнопки
        self.btn_clone = QPushButton("Клонировать репозиторий")
        self.btn_backup = QPushButton("Резервная копия на Яндекс.Диск")
        
        # Лог
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        
        # Добавляем элементы
        layout.addWidget(QLabel("URL репозитория Git:"))
        layout.addWidget(self.repo_url)
        
        layout.addWidget(QLabel("Локальная папка:"))
        layout.addWidget(self.local_path)
        
        layout.addWidget(self.btn_clone)
        layout.addWidget(self.btn_backup)
        layout.addWidget(QLabel("Лог:"))
        layout.addWidget(self.log)
        
        central_widget.setLayout(layout)
        
        # Обработчики событий
        self.btn_clone.clicked.connect(self.clone_repo)
        self.btn_backup.clicked.connect(self.backup_to_yandex)
    
    def log_message(self, message):
        self.log.append(message)
    
    def clone_repo(self):
        url = self.repo_url.text()
        path = self.local_path.text()
        
        if not url or not path:
            QMessageBox.warning(self, "Ошибка", "Заполните URL и путь!")
            return
        
        try:
            subprocess.run(["git", "clone", url, path], check=True)
            self.log_message(f"Репозиторий склонирован в {path}")
        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}")
    
    def backup_to_yandex(self):
        if not self.yandex_token:
            self.log_message("Токен Яндекс.Диска не указан!")
            return
        
        # Здесь можно добавить загрузку через API Яндекс.Диска
        self.log_message("Резервная копия создана (реализуйте этот метод)")

if __name__ == "__main__":
    app = QApplication([])
    window = RepoManager()
    window.show()
    app.exec_()