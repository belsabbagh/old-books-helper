import os
from core import (
    parse_single_column_csv,
    read_text_from_image,
    search_books,
    search_books_by_cover_image,
)
import time


def test_search_by_title():
    testfile = "test.csv"

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


def test_search_by_cover():
    testdir = r"data/test_covers"

    covers = os.listdir(testdir)
    score = {"fail": [], "total": len(covers), "cases": {}}
    for cover in covers:
        cover_text = read_text_from_image(os.path.join(testdir, cover))
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


if __name__ == "__main__":
    test_search_by_cover()
    test_search_by_title()
