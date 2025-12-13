# pyright:strict
import sys
import time
from typing import List, Tuple

import openpyxl
from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core import (
    BookDetails,
    parse_single_column_csv,
    read_text_from_image,
    search_books,
)


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    * finished: No data
    * error: tuple (exception type, value, traceback.format_exc())
    * progress: (int current, int total, str item_data)
    """

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    progress = pyqtSignal(int, int, str)
    result = pyqtSignal(BookDetails)


class IsbnWorker(QRunnable):
    """
    Worker runnable for the long-running ISBN processing task.
    Inherits from QRunnable to handle worker thread setup, signals
    and wrap your user functions.
    """

    def __init__(self, items: List[str]):
        super().__init__()
        self.items = items
        self.signals = WorkerSignals()
        # Ensure it can be killed/stopped gracefully if needed (optional)
        self.setAutoDelete(True)

    def run(self):
        """
        Initialise function to run the process in the thread.
        """
        try:
            for i, item in enumerate(self.items):
                # 1. Report progress before the work starts
                self.signals.progress.emit(i + 1, len(self.items), item)

                foundList = search_books(item)

                if not foundList:
                    # Handle the case where the book is not found or error occurred
                    print(f"ISBN: {item} not found or search failed.")
                    continue

                # 2. Report a successful result back to the main thread
                self.signals.result.emit(foundList[0])

                time.sleep(0.05)  # Small wait to simulate more work/rate limiting

        except Exception as e:
            # Report any exceptions back to the main thread
            import traceback

            self.signals.error.emit((type(e), e, traceback.format_exc()))
        finally:
            # Report completion
            self.signals.finished.emit()


class CoverWorker(QRunnable):
    """
    Worker runnable for the long-running ISBN processing task.
    Inherits from QRunnable to handle worker thread setup, signals
    and wrap your user functions.
    """

    def __init__(self, items: List[str]):
        super().__init__()
        self.items = items
        self.signals = WorkerSignals()
        # Ensure it can be killed/stopped gracefully if needed (optional)
        self.setAutoDelete(True)

    def run(self):
        """
        Initialise function to run the process in the thread.
        """
        try:
            for i, item in enumerate(self.items):
                # 1. Report progress before the work starts
                self.signals.progress.emit(i + 1, len(self.items), item)

                cover_text = read_text_from_image(item)
                foundList = search_books(cover_text)

                if not foundList:
                    # Handle the case where the book is not found or error occurred
                    print(f"ISBN: {item} not found or search failed.")
                    continue

                # 2. Report a successful result back to the main thread
                self.signals.result.emit(foundList[0])

                time.sleep(0.05)  # Small wait to simulate more work/rate limiting

        except Exception as e:
            # Report any exceptions back to the main thread
            import traceback

            self.signals.error.emit((type(e), e, traceback.format_exc()))
        finally:
            # Report completion
            self.signals.finished.emit()


class MainWindow(QMainWindow):
    isbn_button: QPushButton
    cover_button: QPushButton
    status_label: QLabel
    progress_bar: QProgressBar
    results: List[BookDetails] = []

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Book Data Input (PyQt6)")
        self.setGeometry(100, 100, 500, 250)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_vbox = QVBoxLayout(central_widget)

        # 1. Action Group Box
        action_group = QGroupBox("Select Data Source")
        hbox_layout = QHBoxLayout()

        self.isbn_button = QPushButton("I have ISBN codes (CSV)")
        self.cover_button = QPushButton("I have book cover images (Files)")

        self.isbn_button.clicked.connect(self.isbn_file_selection)
        self.cover_button.clicked.connect(self.cover_image_file_selection)

        hbox_layout.addWidget(self.isbn_button)
        hbox_layout.addWidget(self.cover_button)
        action_group.setLayout(hbox_layout)

        main_vbox.addWidget(action_group)

        # 2. Status Label (Verbose feedback)
        self.status_label = QLabel("Ready. Select an input method to begin.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_vbox.addWidget(self.status_label)

        # 3. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)  # Start invisible/indeterminate
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_vbox.addWidget(self.progress_bar)

        main_vbox.addStretch()
        self.threadpool = QThreadPool()

    def _enable_ui(self, enabled: bool = True):
        """Helper to enable/disable buttons during processing."""
        self.isbn_button.setEnabled(enabled)
        self.cover_button.setEnabled(enabled)

    def _reset_status(self):
        """Resets the status label to a neutral state."""
        self.status_label.setText("Ready. Select an input method to begin.")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self._enable_ui(True)

    def worker_progress(self, current: int, total: int, item: str):
        """Update the UI with the worker's progress."""
        if self.progress_bar:
            if total > 0:
                self.progress_bar.setRange(0, total)
                self.progress_bar.setValue(current)
        if self.status_label:
            self.status_label.setText(f"Processing ISBNs: {current}/{total}: {item}")

    def worker_result(self, book_details: BookDetails):
        """Handle a successful result from the worker."""
        # This slot runs in the main GUI thread, so it's safe to modify self.results
        self.results.append(book_details)
        print("Found book and added to results.")

    def worker_error(self, t: Tuple[type, str, str]):
        """Handle an error reported by the worker."""
        exctype, value, tb_str = t
        print(f"Worker Error: {exctype.__name__}: {value}\n{tb_str}")
        QMessageBox.critical(
            self, "Error", f"An error occurred in the processing thread:\n{value}"
        )
        self._reset_status()

    def worker_finished(self):
        """Handle the worker completing its task."""
        print("All ISBN processing finished.")
        print("\n".join(f"{i + 1}. {item}" for i, item in enumerate(self.results)))
        self.save_results_to_excel()
        self._reset_status()
        self._enable_ui(True)

    def save_results_to_excel(self):
        """
        Opens a QFileDialog for the user to select the save location,
        then writes the collected book data to an Excel file.
        """
        if not self.results:
            QMessageBox.warning(
                self,
                "No Data",
                "There are no results to save. Please fetch book data first.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Book Results to Excel File",  # Dialog Title
            "book_results.xlsx",  # Default File Name
            "Excel Files (*.xlsx);;All Files (*)",  # File Filter
        )

        # Check if the user cancelled the dialog
        if not file_path:
            print("Save operation cancelled by user.")
            return

        # Ensure the file has the correct extension
        if not file_path.lower().endswith(".xlsx"):
            file_path += ".xlsx"

        print(f"Attempting to save {len(self.results)} books to: {file_path}")

        try:
            # 2. Write Data using openpyxl
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            if sheet is None:
                raise ValueError("active sheet failed")
            sheet.title = "Book Details"

            # Write header row
            header = ["ISBN", "Title", "Authors"]
            sheet.append(header)

            # Write data rows
            for book in self.results:
                # Format authors list into a comma-separated string
                authors_str = ", ".join(book.authors)
                row_data = [book.identifiers[0]["identifier"], book.title, authors_str]
                sheet.append(row_data)

            # Save the workbook to the selected path
            workbook.save(file_path)

            print(
                f"✅ Successfully saved {len(self.results)} book records to Excel at: {file_path}"
            )
            QMessageBox.information(
                self,
                "Save Complete",
                f"Successfully saved {len(self.results)} book records to\n**{file_path}**",
            )

        except Exception as e:
            error_msg = f"Error saving to Excel file: {e}"
            print(f"❌ {error_msg}")
            QMessageBox.critical(self, "Save Error", error_msg)

    def isbn_file_selection(self):
        self._enable_ui(False)
        self.status_label.setText("Waiting for CSV file selection...")
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        csv_filter = "CSV Files (*.csv);;All Files (*.*)"
        filename, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File with ISBNs", "", csv_filter
        )

        if not filename:
            self._reset_status()
            return
        # 1. Load the items from the file
        items = parse_single_column_csv(filename)
        # Clear previous results
        self.results: List[BookDetails] = []

        worker: IsbnWorker = IsbnWorker(items)

        # 3. Connect the worker's signals to the main thread's slots
        worker.signals.progress.connect(self.worker_progress)
        worker.signals.result.connect(self.worker_result)
        worker.signals.error.connect(self.worker_error)
        worker.signals.finished.connect(self.worker_finished)

        # 4. Start the worker using the QThreadPool
        self.threadpool.start(worker)

    def cover_image_file_selection(self):
        self._enable_ui(False)
        self.status_label.setText("Waiting for image file selection...")
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        file_filter = "Images (*.png *.jpg *.jpeg *.gif);;All Files (*.*)"
        filenames, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Book Cover Images",
            "",
            file_filter,
        )

        if not filenames:
            self._reset_status()
        items = filenames
        self.results: List[BookDetails] = []

        worker: CoverWorker = CoverWorker(items)

        # 3. Connect the worker's signals to the main thread's slots
        worker.signals.progress.connect(self.worker_progress)
        worker.signals.result.connect(self.worker_result)
        worker.signals.error.connect(self.worker_error)
        worker.signals.finished.connect(self.worker_finished)

        # 4. Start the worker using the QThreadPool
        self.threadpool.start(worker)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
