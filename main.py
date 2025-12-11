import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
)

from core import parse_single_column_csv


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Book Data Input (PyQt5)")
        self.setGeometry(100, 100, 400, 150)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        hbox_layout = QHBoxLayout()

        isbn_button = QPushButton("I have ISBN codes")
        cover_button = QPushButton("I have book cover images")

        isbn_button.clicked.connect(self.isbn_action)
        cover_button.clicked.connect(self.cover_image_action)

        hbox_layout.addWidget(isbn_button)
        hbox_layout.addWidget(cover_button)

        main_vbox = QVBoxLayout(central_widget)
        main_vbox.addLayout(hbox_layout)

        main_vbox.addStretch()

    def isbn_action(self):
        csv_filter = "CSV Files (*.csv);;All Files (*.*)"
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", csv_filter
        )
        isbns = parse_single_column_csv(filename)
        print(isbns)

    def cover_image_action(self):
        file_filter = "Images (*.png *.jpg *.jpeg *.gif);;All Files (*.*)"

        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",  # Empty string for default starting directory
            file_filter,
        )
        print(filenames)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
