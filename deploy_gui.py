from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QCheckBox, QTextEdit, QMessageBox
)
from PyQt5.QtGui import QIcon
import subprocess
import os
import sys

class DeployTool(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Librarian AI — Deploy Tool")
        self.setGeometry(100, 100, 540, 420)
        self.setWindowIcon(QIcon("logo.png"))
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.repo_path = QLineEdit()
        self.repo_path.setPlaceholderText("📁 Путь к локальному проекту")

        self.remote_url = QLineEdit()
        self.remote_url.setPlaceholderText("🌐 URL GitHub-репозитория (например, git@...)")

        browse_btn = QPushButton("🔍 Выбрать папку")
        browse_btn.clicked.connect(self.select_folder)

        self.git_check = QCheckBox("✅ Отправить в GitHub")
        self.git_check.setChecked(True)
        self.yadisk_check = QCheckBox("📤 Отправить в Яндекс.Диск (заглушка)")

        deploy_btn = QPushButton("🚀 Запустить деплой")
        deploy_btn.clicked.connect(self.deploy_project)

        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout.addWidget(QLabel("📁 Путь к проекту:"))
        layout.addWidget(self.repo_path)
        layout.addWidget(browse_btn)

        layout.addWidget(QLabel("🌐 URL репозитория (если новый):"))
        layout.addWidget(self.remote_url)

        layout.addWidget(self.git_check)
        layout.addWidget(self.yadisk_check)
        layout.addWidget(deploy_btn)
        layout.addWidget(QLabel("🪵 Вывод:"))
        layout.addWidget(self.output)

        self.setLayout(layout)

    def log(self, msg):
        self.output.append(msg)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выбрать папку")
        if folder:
            self.repo_path.setText(folder)

    def run_git(self, cmd_list, cwd):
        return subprocess.run(cmd_list, cwd=cwd, capture_output=True, text=True)

    def deploy_project(self):
        path = self.repo_path.text().strip()
        remote_url = self.remote_url.text().strip()

        if not os.path.isdir(path):
            QMessageBox.critical(self, "❌ Ошибка", "Указанная папка не существует.")
            return

        os.chdir(path)

        if self.git_check.isChecked():
            self.log("🧩 Git инициализация...")

            # Инициализация git
            if not os.path.isdir(os.path.join(path, ".git")):
                self.run_git(["git", "init"], path)
                self.log("✅ Git инициализирован")

            # Добавление remote origin
            if remote_url:
                self.run_git(["git", "remote", "remove", "origin"], path)
                self.run_git(["git", "remote", "add", "origin", remote_url], path)
                self.log(f"🔗 Добавлен origin: {remote_url}")

            # Git push
            self.run_git(["git", "add", "."], path)
            self.run_git(["git", "commit", "-m", "🚀 Auto-deploy from Librarian AI GUI"], path)
            push_result = self.run_git(["git", "push", "-u", "origin", "main"], path)

            if push_result.returncode == 0:
                self.log("✅ Проект успешно отправлен в GitHub")
            else:
                self.log("❌ Ошибка push:\n" + push_result.stderr)

        if self.yadisk_check.isChecked():
            self.log("📡 Загрузка в Яндекс.Диск (заглушка)")

        self.log("🎉 Готово.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DeployTool()
    window.show()
    sys.exit(app.exec_())