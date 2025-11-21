import sys
import json
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt

CONFIG_FILE = "config.json"


class YtDlpWrapper(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube to MP3 Downloader")
        self.setGeometry(100, 100, 500, 250)

        self.config = self.load_config()

        # Widgets
        self.url_label = QLabel("YouTube Link:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube link here...")

        self.folder_label = QLabel("Download Folder:")
        self.folder_input = QLineEdit(self.config.get("last_folder", ""))
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
        layout.addWidget(self.download_btn)
        layout.addWidget(self.output_box)

        self.setLayout(layout)

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YtDlpWrapper()
    window.show()
    sys.exit(app.exec())
