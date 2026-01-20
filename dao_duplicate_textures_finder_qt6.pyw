import sys
import os
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QLineEdit,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QStandardPaths
from PyQt6.QtGui import QColor, QPalette, QPixmap, QImage
from PIL import Image

try:
    from send2trash import send2trash

    TRASH_SUPPORT = True
except ImportError:
    TRASH_SUPPORT = False


def pil_to_qpixmap(pil_image):
    if pil_image.mode == "RGBA":
        data = pil_image.tobytes("raw", "RGBA")
        qimage = QImage(
            data, pil_image.width, pil_image.height, QImage.Format.Format_RGBA8888
        )
    elif pil_image.mode == "RGB":
        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(
            data, pil_image.width, pil_image.height, QImage.Format.Format_RGB888
        )
    else:
        pil_image = pil_image.convert("RGB")
        data = pil_image.tobytes("raw", "RGB")
        qimage = QImage(
            data, pil_image.width, pil_image.height, QImage.Format.Format_RGB888
        )
    return QPixmap.fromImage(qimage)


class DuplicateFinder(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, folder_path):
        super().__init__()
        self.folder_path = folder_path
        self.supported_formats = (".dds", ".tga", ".png", ".jpg", ".jpeg")

    def run(self):
        try:
            image_files = []
            for root, _, files in os.walk(self.folder_path):
                for file in files:
                    if file.lower().endswith(self.supported_formats):
                        full_path = os.path.join(root, file)
                        key = file.lower()
                        image_files.append((full_path, key))

            if not image_files:
                self.error.emit(
                    "No supported image files found in the selected folder."
                )
                return

            name_dict = {}
            for file_path, key in image_files:
                name_dict.setdefault(key, []).append(file_path)

            duplicates = {
                name: paths for name, paths in name_dict.items() if len(paths) > 1
            }
            self.finished.emit(duplicates)

        except Exception as e:
            self.error.emit(f"Error during scanning: {str(e)}")


class ImagePreviewWidget(QWidget):
    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setup_ui()
        self.load_image_info()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(384, 384)
        self.image_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.image_label.setStyleSheet(
            "border: 1px solid #555; background-color: #2a2a2a;"
        )
        layout.addWidget(self.image_label)

        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(self.info_label)

        button_layout = QHBoxLayout()
        self.open_button = QPushButton("Open")
        self.delete_button = QPushButton("Delete")
        self.open_button.clicked.connect(self.open_file)
        self.delete_button.clicked.connect(self.delete_file)

        if not TRASH_SUPPORT:
            self.delete_button.setEnabled(False)
            self.delete_button.setToolTip("send2trash not available")

        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        button_style = """
            QPushButton {
                background-color: #444;
                color: #eee;
                border: 1px solid #666;
                padding: 4px 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #555;
                border: 1px solid #888;
            }
            QPushButton:pressed {
                background-color: #333;
            }
            QPushButton:disabled {
                color: #777;
                border: 1px solid #555;
            }
        """
        self.open_button.setStyleSheet(button_style)
        self.delete_button.setStyleSheet(button_style)

        self.setToolTip(self.file_path)

    def load_image_info(self):
        try:
            size_bytes = os.path.getsize(self.file_path)
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

            with Image.open(self.file_path) as img:
                width, height = img.size
                mode = img.mode

            filename = os.path.basename(self.file_path)
            self.info_label.setText(
                f"{filename}\n{width}×{height} px | {mode}\n{size_str}"
            )
            self.load_pixmap_from_pil()
        except Exception:
            self.info_label.setText(
                f"Error loading:\n{os.path.basename(self.file_path)}"
            )
            self.image_label.setText("Error")

    def load_pixmap_from_pil(self):
        try:
            with Image.open(self.file_path) as img:
                if img.mode in ("RGBA", "LA", "P"):
                    if img.mode == "P":
                        img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")
                img.thumbnail((384, 384), Image.Resampling.LANCZOS)
                pixmap = pil_to_qpixmap(img)
                self.image_label.setPixmap(pixmap)
        except Exception:
            self.image_label.setText("Preview\nUnavailable")

    def open_file(self):
        try:
            if sys.platform == "win32":
                os.startfile(self.file_path)
            elif sys.platform == "darwin":
                os.system(f"open '{self.file_path}'")
            else:
                os.system(f"xdg-open '{self.file_path}'")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file:\n{str(e)}")

    def delete_file(self):
        if not TRASH_SUPPORT:
            QMessageBox.warning(
                self,
                "Not Supported",
                "send2trash is not installed.\n\nPlease run:\npip install send2trash",
            )
            return

        try:
            normalized_path = os.path.normpath(self.file_path)
            send2trash(normalized_path)
            self.setEnabled(False)
            self.setStyleSheet("background-color: #2a2a2a; color: #777;")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not move to Trash:\n{str(e)}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Dragon Age: Origins - Duplicate Textures Finder - 1.0 - © Henry & Lukas 2025-2026"
        )
        self.setGeometry(100, 100, 1200, 600)

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Highlight, QColor(70, 70, 100))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.setPalette(palette)

        docs = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
        self.default_folder = os.path.join(
            docs, r"BioWare\Dragon Age\packages\core\override"
        )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = QWidget()
        top_bar.setFixedHeight(40)
        top_bar.setStyleSheet("background-color: #222;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 5, 10, 5)

        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedWidth(100)
        self.browse_btn.setMinimumHeight(32)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: #eee;
                border: 1px solid #666;
                padding: 6px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #555;
                border: 1px solid #888;
            }
        """)
        self.browse_btn.clicked.connect(self.select_folder)
        top_bar_layout.addWidget(self.browse_btn)

        self.folder_entry = QLineEdit()
        self.folder_entry.setReadOnly(True)
        self.folder_entry.setMinimumHeight(32)
        self.folder_entry.setStyleSheet(
            "background-color: #333; color: #ccc; border: 1px solid #555; padding: 6px 8px; border-radius: 4px;"
        )
        top_bar_layout.addWidget(self.folder_entry)

        main_layout.addWidget(top_bar)

        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.content_splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)

        self.groups_tree = QTreeWidget()
        self.groups_tree.setHeaderHidden(True)
        self.groups_tree.itemClicked.connect(self.on_group_selected)
        self.groups_tree.setAlternatingRowColors(True)
        self.groups_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252525;
                color: #e0e0e0;
                border: 1px solid #555;
                alternate-background-color: #2d2d2d;
            }
            QTreeWidget::item {
                padding: 6px 0px;
            }
        """)
        left_layout.addWidget(self.groups_tree)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)

        self.compare_title = QLabel("Select a group to compare")
        self.compare_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.compare_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; margin: 10px; color: #e0e0e0;"
        )
        right_layout.addWidget(self.compare_title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #222;")
        self.scroll_layout = QHBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.scroll_layout.setSpacing(15)
        self.scroll_area.setWidget(self.scroll_content)
        right_layout.addWidget(self.scroll_area)

        self.content_splitter.addWidget(left_widget)
        self.content_splitter.addWidget(right_widget)
        self.content_splitter.setSizes([280, self.width() - 280])

        self.duplicate_groups = {}
        self.current_group = None

        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet(
            "background-color: #222; color: #aaa; border-top: 1px solid #444;"
        )

        if os.path.exists(self.default_folder):
            self.selected_folder = self.default_folder
            self.folder_entry.setText(self.selected_folder)
            self.start_scan()
        else:
            self.selected_folder = None
            self.folder_entry.setText("(not found)")

    def select_folder(self):
        start_dir = self.selected_folder or self.default_folder
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", start_dir)
        if folder:
            self.selected_folder = folder
            self.folder_entry.setText(folder)
            self.groups_tree.clear()
            self.clear_comparison_view()
            self.start_scan()

    def start_scan(self):
        if not self.selected_folder or not os.path.exists(self.selected_folder):
            return
        self.statusBar().showMessage("Scanning...")
        self.duplicate_groups = {}
        self.groups_tree.clear()
        self.clear_comparison_view()
        self.finder = DuplicateFinder(self.selected_folder)
        self.finder.finished.connect(self.show_results)
        self.finder.error.connect(self.show_error)
        self.finder.start()

    def show_results(self, duplicates):
        self.duplicate_groups = duplicates
        self.groups_tree.clear()
        if not duplicates:
            self.statusBar().showMessage("Scan complete – No duplicates found")
            self.clear_comparison_view()
            return
        for full_name, paths in duplicates.items():
            item = QTreeWidgetItem([f"{full_name} ({len(paths)} files)"])
            item.setData(0, Qt.ItemDataRole.UserRole, full_name)
            self.groups_tree.addTopLevelItem(item)
        self.groups_tree.resizeColumnToContents(0)
        total_files = sum(len(v) for v in duplicates.values())
        self.statusBar().showMessage(
            f"Scan complete! Found {total_files} duplicate files in {len(duplicates)} groups"
        )

    def on_group_selected(self, item, column):
        group_name = item.data(0, Qt.ItemDataRole.UserRole)
        if group_name in self.duplicate_groups:
            self.show_comparison(group_name, self.duplicate_groups[group_name])

    def show_comparison(self, group_name, file_paths):
        self.current_group = group_name
        self.compare_title.setText(f"Comparing: {group_name}")
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        for file_path in file_paths:
            preview = ImagePreviewWidget(file_path)
            self.scroll_layout.addWidget(preview)
        self.scroll_content.setLayout(self.scroll_layout)

    def clear_comparison_view(self):
        self.compare_title.setText("Select a group to compare")
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_error(self, error_msg):
        self.statusBar().showMessage("Error occurred")
        QMessageBox.critical(self, "Error", error_msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
