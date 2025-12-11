from core import parse_single_column_csv, search_books
import time


def main():
    testfile = "test.csv"

    print("--- STEP 1: CSV PARSING ---")
    print(f"Attempting to parse file: '{testfile}'")
    titles = parse_single_column_csv(testfile)
    print(f"SUCCESS: Found {len(titles)} titles.")
    print("-" * 30)

    for title in titles:
        print(f'\n[PROCESSING TITLE] -> "{title}"')
        print("  |-- A. Attempting direct ISBN extraction...")
        results = search_books(title)
        time.sleep(3)
        if not results:
            print(f"  |-- FAIL: No book was found for {title}")
            continue
        print(f"  |-- SUCCESS: Found book: {results[0]}")
        print("---------------------------------")


if __name__ == "__main__":
    main()
