# pyright:strict
import csv
import json
import os
from dataclasses import dataclass
import re
from typing import Any, Dict, List

import pytesseract
import requests
from dotenv import load_dotenv
from PIL import Image

load_dotenv()
api_key: str | None = os.environ.get("GOOGLE_BOOKS_API_KEY")


def parse_single_column_csv(file_path: str) -> List[str]:
    """
    Reads a single-column CSV file and returns the column data as a list of strings.
    Uses the csv module for robust parsing.
    """
    data_list: List[str] = []
    try:
        # 'r' mode for reading, newline='' is recommended for CSV files on all OS
        with open(file_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)

            for row in reader:
                if row:  # Ensure the row is not empty (e.g., blank lines)
                    # For a single column, the data is the first (and only) element
                    data_list.append(row[0])

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except IndexError:
        print("Error: The CSV file appears to have multiple columns or is malformed.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return data_list


@dataclass
class BookDetails:
    """A data class to hold extracted book information."""

    identifiers: List[Dict[str, str]]
    title: str
    authors: List[str]

    def __repr__(self):
        """
        Creates a compact and readable representation of the BookDetails instance.
        Example: <BookDetails 'The Hitchhiker's Guide...' by Adams (ISBN-13: 9780345391803)>
        """
        # Truncate the title if it's too long for a single line representation
        max_title_len = 30
        title_display = (
            (self.title[:max_title_len] + "...")
            if len(self.title) > max_title_len
            else self.title
        )

        # Format authors: either 'Author Name' or 'Author 1 & Author 2, et al.'
        if not self.authors:
            authors_display = "Unknown Author"
        elif len(self.authors) == 1:
            authors_display = self.authors[0]
        elif len(self.authors) == 2:
            authors_display = f"{self.authors[0]} & {self.authors[1]}"
        else:
            authors_display = f"{self.authors[0]}, et al."

        # Extract a displayable ISBN (e.g., ISBN_13)
        isbn_display = ""
        isbn_type = ""
        # The structure is List[Dict[str, str]], e.g., [{'type': 'ISBN_13', 'identifier': '978...'}, ...]
        for isbn_entry in self.identifiers:
            if isbn_entry.get("type") == "ISBN_13":
                isbn_display = isbn_entry.get("identifier", "N/A")
                isbn_type = "ISBN-13"
                break  # Found the preferred ISBN
            elif isbn_entry.get("type") == "ISBN_10" and not isbn_display:
                # Use ISBN_10 as a fallback if ISBN_13 is not found yet
                isbn_display = isbn_entry.get("identifier", "N/A")
                isbn_type = "ISBN-10"

        # Fallback if no specific ISBN was found
        if not isbn_display and self.identifiers:
            # Try to grab the first identifier if we couldn't find a type match
            isbn_display = self.identifiers[0].get("identifier", "N/A")
            isbn_type = self.identifiers[0].get("type", "ISBN")
        elif not isbn_display:
            # If the list is empty
            isbn_display = "N/A"
            isbn_type = "ISBN"

        # The final, formatted string
        # Note the change to include the ISBN type and the extracted identifier
        return f"<BookDetails '{title_display}' by {authors_display} ({isbn_type}: {isbn_display})>"


def search_books(q: str) -> List[BookDetails]:
    if not api_key:
        print("Error: GOOGLE_BOOKS_API_KEY environment variable not set.")
        return []

    # 2. Define the API endpoint and parameters
    api_url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": q,
        "key": api_key,  # Pass the API key as a query parameter
    }

    try:
        # 3. Make the Request using 'requests'
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # 4. Process the JSON Response
        obj = response.json()

        if obj.get("totalItems", 0) == 0 or not obj.get("items"):
            print(f"No book found for query: {q}")
            return []

        volumes = obj["items"]

        def mk_book(volume: dict[str, Any]):
            volume_info = volume.get("volumeInfo", {})
            authors = volume_info.get("authors", ["N/A (Author Unknown)"])
            return BookDetails(
                identifiers=volume_info.get("industryIdentifiers") or [],
                title=volume_info.get("title", "N/A"),
                authors=authors,
            )

        return [mk_book(i) for i in volumes]

    except requests.exceptions.RequestException as e:
        # Catches network errors, DNS failure, and HTTP errors (4xx/5xx)
        print(f"An error occurred during the API request: {e.response.json()}")
        return []
    except json.JSONDecodeError:
        print("Error decoding JSON response.")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


def search_by_isbn(isbn: str) -> List[BookDetails]:
    return search_books(f"isbn:{isbn}")


def search_books_by_cover_image(img_path: str) -> List[BookDetails]:
    # Correct path to tesseract.exe on your computer
    # pytesseract.pytesseract.tesseract_cmd = (
    #     r"C:\Users\gfg0753\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
    # )
    img = Image.open(img_path).convert("L")
    text = pytesseract.image_to_string(img)
    if isinstance(text, str):
        print(text.replace("\x0c", "").strip())
        return search_books(text)
    return []


def read_text_from_image(img_path: str) -> str:
    img = Image.open(img_path).convert("L")
    text = pytesseract.image_to_string(img)
    if isinstance(text, str):
        text = "".join(re.findall(r"[a-zA-Z0-9\ \n]+", text)).replace("\n", " ")
        print(text)
        return text
    return ""
