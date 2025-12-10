from PyQt6.QtCore import Qt
import subprocess
import json
from PyQt6.QtWidgets import (
    QWidget, QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QFileDialog, QTextEdit, QListWidget, QListWidgetItem, QFrame,
    QSizePolicy, QMessageBox, QScrollArea, QSpacerItem
)
from PyQt6.QtCore import (
    QSize, QCoreApplication, QEvent, QTimer, QPoint, QThread, pyqtSignal
)
from PyQt6.QtGui import (
    QFont, QIcon
)


import sys
import os

# =============================================================== #
#           Constants and Configurations                          #
# =============================================================== #
basedir = os.path.dirname(__file__)

MAX_RECENT_FOLDERS = 10
CONFIG_FILE = "config.json"

# =============================================================== #
#           Main Application Class                                #
# =============================================================== #
class YtDlpWrapper(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube to MP3 Downloader")
        self.setGeometry(100, 100, 600, 650)

        self.config = self.load_config()
        # =============================================================== #
        #           Widgets                                               #
        # =============================================================== #
        self.url_label = QLabel("YouTube Link:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube link here...")

        self.folder_label = QLabel("Download Folder:")
        self.folder_input = QLineEdit(self.config.get("last_folder", ""))
        self.folder_input.setPlaceholderText("Select download folder...")
        # =============================================================== #
        #    Create dropdown list floating panel for recent folders       #
        # =============================================================== #
        self.recent_panel = QFrame(self)
        self.recent_panel.setFrameShape(QFrame.Shape.Box)
        self.recent_panel.setStyleSheet(
            "background: #2e2e2e; border-radius: 6px;")
        self.recent_panel.hide()

        self.recent_list = QListWidget(self.recent_panel)
        self.recent_list.itemClicked.connect(self.select_recent_folder)

        self.folder_input.installEventFilter(self)
        self.folder_input.textChanged.connect(self.on_folder_edit)
        # =============================================================== #
        #                       Buttons                                   #                     
        # =============================================================== #
        self.folder_btn = QPushButton("Browse")
        self.folder_btn.clicked.connect(self.select_folder)

        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.download_video)

        # add a check box "only audio" next to download button
        self.only_audio_checkbox = QPushButton("Only Audio")
        self.only_audio_checkbox.setCheckable(True)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setPlaceholderText("Output log...")
        self.output_box.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.output_box.setStyleSheet("background: #1e1e1e; color: #ffffff;")
        self.output_box.setFont(QFont("Consolas", 10))
        # =============================================================== #
        # Layout setup                                                  #
        # =============================================================== #
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.folder_label)
        layout.addLayout(folder_layout)
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.only_audio_checkbox)
        layout.addWidget(self.download_btn)
        layout.addWidget(self.output_box)

        self.setLayout(layout)
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def eventFilter(self, obj, event):

        match event.type():
            case QEvent.Type.Enter:
                if obj == self.folder_input or self.recent_panel.underMouse():
                    self.show_recent_panel()
            case QEvent.Type.Leave:
                if obj == self.folder_input and not self.recent_panel.underMouse():
                    QTimer.singleShot(200, self.hide_recent_panel)
    
        return super().eventFilter(obj, event)
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def show_recent_panel(self):
        self.populate_recent_list()
        if self.recent_list.count() == 0:
            self.recent_list.hide()

            # Position panel right under the folder input box
        input_pos = self.folder_input.mapTo(
            self, QPoint(0, self.folder_input.height()))
        width = self.folder_input.width()

        self.recent_panel.setGeometry(input_pos.x(), input_pos.y(), width, 120)
        self.recent_list.setGeometry(0, 0, width, 120)

        self.recent_panel.raise_()
        self.recent_panel.show()
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def hide_recent_panel(self):
        if not self.folder_input.underMouse() and not self.recent_panel.underMouse():
            self.recent_panel.hide()
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def on_folder_edit(self, text):
        self.populate_recent_list(filter_text=text)
        if self.recent_list.count() > 0:
            self.show_recent_panel()
        else:
            self.recent_panel.hide()
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def populate_recent_list(self, filter_text=""):
        self.recent_list.clear()
        for path in self.config.get("recent_folders", []):
            if filter_text.lower() in path.lower():
                self.recent_list.addItem(QListWidgetItem(path))
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def select_recent_folder(self, item):
        self.folder_input.setText(item.text())
        self.recent_list.hide()
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Download Folder")
        if folder:
            self.add_recent_folder(folder)
            self.save_config()
            self.folder_input.setText(folder)
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def download_video(self):
        url = self.url_input.text().strip()
        folder = self.folder_input.text().strip()

        if not url:
            self.log_output("❌ Please enter a YouTube link.")
            return
        if not folder:
            self.log_output("❌ Please select a download folder.")
            return

        # Add recent folder and save immediately so it's remembered
        self.add_recent_folder(folder)
        self.save_config()

        # Build the yt-dlp command
        if self.only_audio_checkbox.isChecked():
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
        else:
            command = [
                "yt-dlp",
                "-f", "bestvideo+bestaudio/best",
                "--embed-thumbnail",
                "--add-metadata",
                "--metadata-from-title", "%(title)s",
                "--parse-metadata", "title:%(title)s",
                "--parse-metadata", "uploader:%(artist)s",
                "-o", os.path.join(folder, "%(title)s.%(ext)s"),
                url
            ]

        # Disable controls while downloading
        self.download_btn.setEnabled(False)
        self.folder_btn.setEnabled(False)
        self.url_input.setEnabled(False)
        self.folder_input.setEnabled(False)
        self.only_audio_checkbox.setEnabled(False)

        self.log_output(f"▶ Starting download: {url}\n")

        # Start worker thread to run yt-dlp and stream output
        self.worker = DownloadWorker(command)
        self.worker.line.connect(self.log_output)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.start()
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def add_recent_folder(self, folder):
        recent = self.config.get("recent_folders", [])
        if folder in recent:
            recent.remove(folder)
        recent.insert(0, folder)
        self.config["recent_folders"] = recent[:MAX_RECENT_FOLDERS]
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.log_output(f"Error saving config: {e}")
    # =============================================================== #
    #           Recent folders panel methods                         #
    # =============================================================== #
    def log_output(self, text):
        self.output_box.append(text)
        self.output_box.ensureCursorVisible()

    def on_download_finished(self, returncode: int):
        if returncode == 0:
            self.log_output("\n✅ Done!")
        else:
            self.log_output("\n❌ Error during download.")

        # Re-enable controls
        self.download_btn.setEnabled(True)
        self.folder_btn.setEnabled(True)
        self.url_input.setEnabled(True)
        self.folder_input.setEnabled(True)
        self.only_audio_checkbox.setEnabled(True)

        # Optionally clean up worker reference
        try:
            self.worker.deleteLater()
        except Exception:
            pass
        self.worker = None


# =============================================================== #
#           Download Worker Class                                 #
# =============================================================== #
class DownloadWorker(QThread):
    line = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, command, parent=None):
        super().__init__(parent)
        self.command = command

    def run(self):
        try:
            proc = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,      # Python 3.7+: use text=True instead of universal_newlines
                bufsize=1
            )
        except Exception as e:
            self.line.emit(f"❌ Failed to start process: {e}")
            self.finished.emit(1)
            return

        # Stream lines and emit them to the GUI thread
        for line in proc.stdout:
            self.line.emit(line.rstrip())

        proc.wait()
        self.finished.emit(proc.returncode if proc is not None else 1)

# =============================================================== #
#           Application entry point                               #
# =============================================================== #

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # print(os.path.join(basedir, 'src\\img\\logo.ico'))
    app.setWindowIcon(QIcon(os.path.join(basedir, 'src/img/logo.ico')))

    window = YtDlpWrapper()
    window.show()
    sys.exit(app.exec())
