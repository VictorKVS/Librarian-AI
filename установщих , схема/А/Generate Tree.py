import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox
)


def generate_tree(path, prefix='', output_file=None):
    entries = sorted(os.listdir(path), key=lambda s: s.lower())
    total_count = len(entries)
    line = f"{prefix}├── {os.path.basename(path)} ({total_count})"
    output_file.write(line + "\n")

    child_prefix = prefix + "│   "

    for entry in entries:
        full_path = os.path.join(path, entry)
        if os.path.isdir(full_path):
            generate_tree(full_path, child_prefix, output_file)
        else:
            output_file.write(f"{child_prefix}├── {entry}\n")


class TreeGeneratorGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Directory Tree Generator')
        layout = QVBoxLayout()

        # Input directory
        in_layout = QHBoxLayout()
        in_label = QLabel('Input Directory:')
        self.in_edit = QLineEdit()
        in_browse = QPushButton('Browse')
        in_browse.clicked.connect(self.browse_input)
        in_layout.addWidget(in_label)
        in_layout.addWidget(self.in_edit)
        in_layout.addWidget(in_browse)
        layout.addLayout(in_layout)

        # Output file
        out_layout = QHBoxLayout()
        out_label = QLabel('Output File:')
        self.out_edit = QLineEdit()
        out_browse = QPushButton('Browse')
        out_browse.clicked.connect(self.browse_output)
        out_layout.addWidget(out_label)
        out_layout.addWidget(self.out_edit)
        out_layout.addWidget(out_browse)
        layout.addLayout(out_layout)

        # Generate button
        generate_btn = QPushButton('Generate Tree')
        generate_btn.clicked.connect(self.generate)
        layout.addWidget(generate_btn)

        self.setLayout(layout)
        self.resize(600, 150)

    def browse_input(self):
        directory = QFileDialog.getExistingDirectory(self, 'Select Input Directory')
        if directory:
            self.in_edit.setText(directory)

    def browse_output(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Select Output File', filter='Markdown Files (*.md);;All Files (*)')
        if file_path:
            self.out_edit.setText(file_path)

    def generate(self):
        input_dir = self.in_edit.text().strip()
        output_file = self.out_edit.text().strip()

        if not os.path.isdir(input_dir):
            QMessageBox.critical(self, 'Error', 'Invalid input directory.')
            return
        if not output_file:
            QMessageBox.critical(self, 'Error', 'Please select an output file path.')
            return

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Directory Tree for {os.path.basename(input_dir)}\n\n")
                generate_tree(input_dir, '', f)
            QMessageBox.information(self, 'Success', f'Directory tree saved to:\n{output_file}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to write file:\n{e}')


def main():
    app = QApplication(sys.argv)
    window = TreeGeneratorGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
