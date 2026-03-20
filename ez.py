import logging
import pandas as pd
import sys

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(levelname)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def main():
    if len(sys.argv) < 3:
        logger.error("Usage: python script.py <index_file> <filter_file>")
        return

    _, index_file, filter_file = sys.argv[:3]

    try:
        # 1. Load data forcing the index/ID column to be treated as string
        # dtype=str ensures Excel doesn't automatically turn "00123" into 123
        index_df = pd.read_excel(
            index_file, sheet_name=0, index_col=0, dtype=str
        ).dropna(how="all")
        index_df = index_df[index_df.index.notna()]

        filter_df = pd.read_excel(
            filter_file, sheet_name=0, index_col=0, dtype=str
        ).dropna(how="all")
        filter_df = filter_df[filter_df.index.notna()]

        # 2. Clean string indexes (remove leading/trailing spaces)
        index_df.index = index_df.index.astype(str).str.strip()
        filter_ids = filter_df.index.astype(str).str.strip().unique().tolist()

        logger.info(f"Searching for {len(filter_ids)} values")
        filtered_rows = []
        not_found = 0

        # Manual Loop through unique filter IDs
        for book_id in filter_ids:
            if book_id in index_df.index:
                # Use .loc with the string ID
                matches = index_df.loc[[book_id]]

                # Check for duplicates in the Index File
                if len(matches) > 1:
                    print(f"\nDuplicate entries found for ID: {book_id}")
                    print(matches)

                    # Manual selection prompt
                    while True:
                        try:
                            choice = int(
                                input(
                                    f"Select row index to keep (0 to {len(matches) - 1}): "
                                )
                            )
                            selected_row = matches.iloc[[choice]]
                            break
                        except (ValueError, IndexError):
                            print("Invalid selection. Please enter a valid row number.")

                    filtered_rows.append(selected_row)
                else:
                    filtered_rows.append(matches)
            else:
                # Log the string ID that was missing
                logger.warning(f"ID '{book_id}' not found in {index_file}. Skipping.")
                not_found += 1
        # Combine selected rows into final DataFrame

        logger.info(f"Not found: {not_found}")
        if filtered_rows:
            final_df = pd.concat(filtered_rows)
            output_name = "filtered_books.xlsx"
            final_df.to_excel(output_name)
            logger.info(f"Successfully saved to {output_name}")
        else:
            logger.error("No matches found. No file created.")

    except Exception as e:
        logger.critical(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
