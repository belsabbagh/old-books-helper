import sys
import time
from typing import List
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QFileDialog,
)

from core import parse_single_column_csv, read_text_from_image, search_books


def proceess_csv(testfile: str):
    print("--- STEP 1: CSV PARSING ---")
    print(f"Attempting to parse file: '{testfile}'")
    titles = parse_single_column_csv(testfile)
    print(f"SUCCESS: Found {len(titles)} titles.")
    print("-" * 30)

    score = {"fail": [], "total": len(titles)}

    for title in titles:
        print(f'\n[PROCESSING TITLE] -> "{title}"')
        print("  |-- A. Attempting direct ISBN extraction...")
        results = search_books(title)
        time.sleep(1)
        if not results:
            print(f"  |-- FAIL: No book was found for {title}")
            score["fail"].append(title)
            continue
        print(f"  |-- SUCCESS: Found book: {results[0]}")
        print("---------------------------------")


def process_covers(covers: List[str]):
    score = {"fail": [], "total": len(covers), "cases": {}}
    for cover in covers:
        cover_text = read_text_from_image(cover)
        results = search_books(cover_text)
        score["cases"][cover] = {"text": cover_text, "results": results}
        time.sleep(1)
        if not results:
            score["fail"].append(cover)
            continue

    # --- STEP 2: Generate Test Summary ---
    total_cases = score["total"]
    failed_cases = len(score["fail"])
    passed_cases = total_cases - failed_cases
    success_rate = (passed_cases / total_cases) * 100 if total_cases > 0 else 0

    print("\n" + "=" * 50)
    print("        📚 TEST SEARCH BY COVER SUMMARY 📚")
    print("=" * 50)
    print(f"| {'TOTAL CASES':<15} | {total_cases:>3} |")
    print(f"| {'PASSED CASES':<15} | {passed_cases:>3} |")
    print(f"| {'FAILED CASES':<15} | {failed_cases:>3} |")
    print("-" * 50)
    print(f"| {'SUCCESS RATE':<15} | {success_rate:>3.2f}% |")
    print("=" * 50)

    if failed_cases > 0:
        print("\n❌ FAILED CASES DETAILS:")
        for failed_cover in score["fail"]:
            print(f"- {failed_cover}")
            # Optionally print the extracted text that failed to yield results
            # print(f"  Extracted Text: \"{score['cases'][failed_cover]['text']}\"")
        print("-" * 50)
    else:
        print("\n✅ All cover searches passed successfully!")
    print("=" * 50)


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
        proceess_csv(filename)

    def cover_image_action(self):
        file_filter = "Images (*.png *.jpg *.jpeg *.gif);;All Files (*.*)"

        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image Files",
            "",  # Empty string for default starting directory
            file_filter,
        )
        process_covers(filenames)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
