
from PyQt6.QtCore import Qt
import subprocess
import json
from PyQt6.QtWidgets import (
    QWidget, QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QFileDialog, QTextEdit, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import (
    QSize, QCoreApplication, QEvent, QTimer
)
from PyQt6.QtGui import (
    QFont, QIcon
)

import sys
import os

basedir = os.path.dirname(__file__)

MAX_RECENT_FOLDERS = 10
CONFIG_FILE = "config.json"


class YtDlpWrapper(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube to MP3 Downloader")
        self.setGeometry(100, 100, 600, 650)

        self.config = self.load_config()

        # Widgets
        self.url_label = QLabel("YouTube Link:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube link here...")

        self.folder_label = QLabel("Download Folder:")
        self.folder_input = QLineEdit(self.config.get("last_folder", ""))

        self.recent_list = QListWidget()
        self.recent_list.hide()  # Hide for now; can be shown later if needed
        self.recent_list.itemClicked.connect(self.select_recent_folder)

        self.folder_input.installEventFilter(self)
        self.folder_input.textChanged.connect(self.on_folder_edit)

        self.folder_btn = QPushButton("Browse")
        self.folder_btn.clicked.connect(self.select_folder)

        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.download_video)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)

        # Layout
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.folder_label)
        layout.addLayout(folder_layout)
        layout.addWidget(self.recent_list)
        layout.addWidget(self.download_btn)
        layout.addWidget(self.output_box)

        self.setLayout(layout)

    def eventFilter(self, obj, event):
        if obj == self.folder_input:
            if event.type() == QEvent.Type.Enter:
                QTimer.singleShot(300, self.show_recent_panel)
            elif event.type() == QEvent.Type.Leave:
                QTimer.singleShot(300, self.hide_recent_panel)
        return super().eventFilter(obj, event)

    def show_recent_panel(self):
        self.populate_recent_list()
        if self.recent_list.count() > 0:
            self.recent_list.show()

    def hide_recent_panel(self):
        if not self.folder_input.underMouse() and not self.recent_list.underMouse():
            self.recent_list.hide()

    def on_folder_edit(self, text):
        self.populate_recent_list(filter_text=text)
        if self.recent_list.count() > 0:
            self.recent_list.show()
        else:
            self.recent_list.hide()

    def populate_recent_list(self, filter_text=""):
        self.recent_list.clear()
        for path in self.config.get("recent_folders", []):
            if filter_text.lower() in path.lower():
                self.recent_list.addItem(QListWidgetItem(path))

    def select_recent_folder(self, item):
        self.folder_input.setText(item.text())
        self.recent_list.hide()

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Download Folder")
        if folder:
            self.add_recent_folder(folder)
            self.save_config()
            self.folder_input.setText(folder)

    def download_video(self):
        folder = self.folder_input.text().strip()
        if folder:
            self.add_recent_folder(folder)
            self.save_config()
        # ... rest of your download code ...

    def add_recent_folder(self, folder):
        recent = self.config.get("recent_folders", [])
        if folder in recent:
            recent.remove(folder)
        recent.insert(0, folder)
        self.config["recent_folders"] = recent[:MAX_RECENT_FOLDERS]

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.log_output(f"Error saving config: {e}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Download Folder")
        if folder:
            self.folder_input.setText(folder)
            self.config["last_folder"] = folder
            self.save_config()

    def log_output(self, text):
        self.output_box.append(text)
        self.output_box.ensureCursorVisible()

    def download_video(self):
        url = self.url_input.text().strip()
        folder = self.folder_input.text().strip()

        if not url:
            self.log_output("❌ Please enter a YouTube link.")
            return
        if not folder:
            self.log_output("❌ Please select a download folder.")
            return

        command = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            "--embed-thumbnail",
            "--add-metadata",
            "--metadata-from-title", "%(title)s",
            "--parse-metadata", "title:%(title)s",
            "--parse-metadata", "uploader:%(artist)s",
            "-o", os.path.join(folder, "%(title)s.%(ext)s"),
            url
        ]

        self.log_output(f"▶ Starting download: {url}\n")

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        for line in process.stdout:
            self.log_output(line.strip())

        process.wait()
        self.log_output("\n✅ Done!" if process.returncode ==
                        0 else "\n❌ Error during download.")




if __name__ == '__main__':
    app = QApplication(sys.argv)

    # print(os.path.join(basedir, 'src\\img\\logo.ico'))
    app.setWindowIcon(QIcon(os.path.join(basedir, 'src/img/logo.ico')))

    window = YtDlpWrapper()
    window.show()
    sys.exit(app.exec())
