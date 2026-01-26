import os
import re
import glob
import argparse
from typing import List, Optional

import pdfplumber
import pandas as pd


def split_line_to_cells(line: str) -> List[str]:
    """Split a text line into columns by runs of 2+ spaces or tabs.
    Keeps numbers/words together and avoids breaking on single spaces.
    """
    cells = [c.strip() for c in re.split(r"\s{2,}|\t+", line.strip()) if c.strip()]
    return cells if cells else [line.strip()]


def extract_tables_from_page(page: pdfplumber.page.Page) -> List[List[str]]:
    """Try to extract tables using pdfplumber; fallback to text heuristics if none found."""
    rows: List[List[str]] = []

    # First, attempt table extraction
    try:
        tables = page.extract_tables()
        for tbl in tables:
            for row in tbl:
                if row is None:
                    continue
                # Clean cell values
                cleaned = [(
                    cell.strip() if isinstance(cell, str) else str(cell) if cell is not None else ""
                ) for cell in row]
                # Skip fully empty rows
                if any(cell for cell in cleaned):
                    rows.append(cleaned)
    except Exception:
        # Silently fallback below
        pass

    # Fallback: use text lines if no table rows
    if not rows:
        text = page.extract_text() or ""
        for line in text.splitlines():
            cells = split_line_to_cells(line)
            if any(cells):
                rows.append(cells)

    return rows


def normalize_rows(rows: List[List[str]]) -> List[List[str]]:
    """Pad/truncate rows to a consistent width for DataFrame creation."""
    if not rows:
        return []
    width = max(len(r) for r in rows)
    norm = []
    for r in rows:
        padded = r + [""] * (width - len(r))
        norm.append(padded[:width])
    return norm


def pdf_to_csv(pdf_path: str, output_csv: str, include_meta: bool = True) -> int:
    """Convert a single PDF to CSV. Returns number of rows written."""
    all_rows: List[List[str]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_rows = extract_tables_from_page(page)
            page_rows = normalize_rows(page_rows)
            if include_meta and page_rows:
                # Prepend meta columns (SourceFile, PageNumber)
                for r in page_rows:
                    all_rows.append([os.path.basename(pdf_path), str(page_num)] + r)
            else:
                all_rows.extend(page_rows)

    if not all_rows:
        # Create an empty file with a header for consistency
        if include_meta:
            df = pd.DataFrame(columns=["SourceFile", "PageNumber", "Col1"])
        else:
            df = pd.DataFrame(columns=["Col1"])
        df.to_csv(output_csv, index=False, encoding="utf-8-sig")
        return 0

    # Build DataFrame with dynamic columns
    width = max(len(r) for r in all_rows)
    if include_meta:
        # First two columns reserved for meta
        columns = ["SourceFile", "PageNumber"] + [f"Col{i}" for i in range(1, width - 2 + 1)]
    else:
        columns = [f"Col{i}" for i in range(1, width + 1)]

    df = pd.DataFrame(all_rows, columns=columns)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    return len(df)


def batch_convert(
    input_pattern: str,
    output_dir: str,
    combine: bool = False,
    include_meta: bool = True,
    ) -> List[str]:
    """Convert all PDFs matching pattern. Returns list of output CSV paths.
    If combine=True, also writes a combined CSV named `all_pdfs_combined.csv`.
    """
    os.makedirs(output_dir, exist_ok=True)
    pdf_files = sorted(glob.glob(input_pattern))
    outputs: List[str] = []

    combined_rows: List[List[str]] = []

    for pdf in pdf_files:
        basename = os.path.splitext(os.path.basename(pdf))[0]
        out_csv = os.path.join(output_dir, f"{basename}.csv")
        print(f"Converting: {pdf} -> {out_csv}")
        try:
            with pdfplumber.open(pdf) as pdf_doc:
                file_rows: List[List[str]] = []
                for page_num, page in enumerate(pdf_doc.pages, start=1):
                    rows = extract_tables_from_page(page)
                    rows = normalize_rows(rows)
                    if include_meta and rows:
                        for r in rows:
                            file_rows.append([os.path.basename(pdf), str(page_num)] + r)
                    else:
                        file_rows.extend(rows)
                if file_rows:
                    width = max(len(r) for r in file_rows)
                    if include_meta:
                        columns = ["SourceFile", "PageNumber"] + [f"Col{i}" for i in range(1, width - 2 + 1)]
                    else:
                        columns = [f"Col{i}" for i in range(1, width + 1)]
                    df = pd.DataFrame(file_rows, columns=columns)
                else:
                    df = pd.DataFrame(columns=["SourceFile", "PageNumber", "Col1"] if include_meta else ["Col1"])  # empty
                df.to_csv(out_csv, index=False, encoding="utf-8-sig")
                outputs.append(out_csv)
                if combine:
                    combined_rows.extend(file_rows)
        except Exception as e:
            print(f"Skipping {pdf}: {e}")
            continue

    if combine:
        if combined_rows:
            width = max(len(r) for r in combined_rows)
            if include_meta:
                columns = ["SourceFile", "PageNumber"] + [f"Col{i}" for i in range(1, width - 2 + 1)]
            else:
                columns = [f"Col{i}" for i in range(1, width + 1)]
            df_all = pd.DataFrame(combined_rows, columns=columns)
        else:
            df_all = pd.DataFrame(columns=["SourceFile", "PageNumber", "Col1"] if include_meta else ["Col1"])  # empty
        combined_path = os.path.join(output_dir, "all_pdfs_combined.csv")
        df_all.to_csv(combined_path, index=False, encoding="utf-8-sig")
        outputs.append(combined_path)
        print(f"Wrote combined CSV: {combined_path}")

    return outputs


def main():
    parser = argparse.ArgumentParser(description="Convert PDF files to CSV using pdfplumber")
    parser.add_argument(
        "--input",
        default=os.path.join(os.path.expanduser("~"), "Downloads", "*.pdf"),
        help="Glob pattern for input PDFs (e.g., 'C:\\Users\\Me\\Downloads\\*.pdf')",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.getcwd(), "output"),
        help="Directory to write CSV files",
    )
    parser.add_argument(
        "--combine",
        action="store_true",
        help="Also write a combined CSV with all PDFs",
    )
    parser.add_argument(
        "--no-meta",
        action="store_true",
        help="Do not include SourceFile/PageNumber columns",
    )

    args = parser.parse_args()
    outputs = batch_convert(
        input_pattern=args.input,
        output_dir=args.output_dir,
        combine=args.combine,
        include_meta=(not args.no_meta),
    )
    print("\nConversion complete. Outputs:")
    for p in outputs:
        print(p)


if __name__ == "__main__":
    main()
