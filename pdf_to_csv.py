import os
import re
import glob
import argparse
from typing import List, Optional

import pdfplumber
import pandas as pd
import csv


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


DATE_PATTERNS = [
    r"^\d{2}/\d{2}/\d{4}",                               # 31/12/2025
    r"^\d{1,2}\s+[A-Za-z]{3}\s+\d{4}",                  # 31 Dec 2025
    r"^\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4}",    # 31st July 2025, 27th November 2025
]
AMOUNT_PATTERN = r"[+-]?\€?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})"  # matches amounts like €1,234.56 or -123.45


def extract_statement_rows(page: pdfplumber.page.Page) -> List[List[str]]:
    """Extract rows for bank statements in a fixed 5-column layout:
    [Date, Description, Debit, Credit, Balance].
    Heuristic: parse text lines, detect date at start, take the last two
    amounts as [Amount, Balance], classify Amount into Debit/Credit by sign or tokens.
    """
    text = page.extract_text() or ""
    rows: List[List[str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # Date at the start
        date_match = None
        for pat in DATE_PATTERNS:
            m = re.match(pat, line)
            if m:
                date_match = m
                break
        if not date_match:
            # Skip non-transaction lines (headers/footers)
            continue

        date_str = date_match.group(0)
        rest = line[date_match.end():].strip()

        # Find amounts (e.g., amount and running balance) at end of line
        amounts = re.findall(AMOUNT_PATTERN, rest)
        if len(amounts) < 2:
            # Not enough numeric tokens; skip
            continue

        balance_str = amounts[-1]
        amount_str = amounts[-2]

        # Description: content between date and the amount_str occurrence
        # Use last occurrence index to avoid cutting early when description contains numbers
        idx = rest.rfind(amount_str)
        description = rest[:idx].strip()

        # Determine Debit/Credit using sign or CR/DR markers
        debit, credit = "", ""
        amt_clean = amount_str.replace("€", "").replace(" ", "")
        is_debit = False
        if amt_clean.startswith("-"):
            is_debit = True
        else:
            # Look for DR/CR hints near the amount or in description
            tail = rest[idx:]
            tokens = (description + " " + tail).upper()
            if " DR" in tokens or tokens.endswith("DR"):
                is_debit = True

        if is_debit:
            debit = amt_clean.lstrip("-")
        else:
            credit = amt_clean.lstrip("+")

        balance_clean = balance_str.replace("€", "").strip()

        # Compose fixed 5 columns
        rows.append([date_str, description, debit, credit, balance_clean])

    return rows


def normalize_rows(rows: List[List[str]], target_width: Optional[int] = None) -> List[List[str]]:
    """Pad/truncate rows to a consistent width for DataFrame creation.
    If target_width is provided, enforce that width; otherwise use max row length.
    """
    if not rows:
        return []
    width = target_width if target_width is not None else max(len(r) for r in rows)
    norm = []
    for r in rows:
        padded = r + [""] * (width - len(r))
        norm.append(padded[:width])
    return norm


def pdf_to_csv(pdf_path: str, output_csv: str, include_meta: bool = True, statement_5col: bool = False) -> int:
    """Convert a single PDF to CSV. Returns number of rows written."""
    all_rows: List[List[str]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_rows = extract_statement_rows(page) if statement_5col else extract_tables_from_page(page)
            page_rows = normalize_rows(page_rows, 5 if statement_5col else None)
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
    if statement_5col:
        base_cols = ["Date", "Description", "Debit", "Credit", "Balance"]
        if include_meta:
            columns = ["SourceFile", "PageNumber"] + base_cols
        else:
            columns = base_cols
    else:
        if include_meta:
            # First two columns reserved for meta
            columns = ["SourceFile", "PageNumber"] + [f"Col{i}" for i in range(1, width - 2 + 1)]
        else:
            columns = [f"Col{i}" for i in range(1, width + 1)]

    df = pd.DataFrame(all_rows, columns=columns)
    df.to_csv(output_csv, index=False, encoding="utf-8-sig", sep=",", quoting=csv.QUOTE_MINIMAL)
    return len(df)


def batch_convert(
    input_pattern: str,
    output_dir: str,
    combine: bool = False,
    include_meta: bool = True,
    excel: bool = False,
    statement_5col: bool = False,
    auto_statement: bool = False,
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
        out_path = os.path.join(output_dir, f"{basename}.{'xlsx' if excel else 'csv'}")
        print(f"Converting: {pdf} -> {out_path}")
        try:
            with pdfplumber.open(pdf) as pdf_doc:
                file_rows: List[List[str]] = []
                any_stmt_used = False
                any_nonstmt_used = False
                for page_num, page in enumerate(pdf_doc.pages, start=1):
                    using_stmt = False
                    if statement_5col:
                        rows = extract_statement_rows(page)
                        using_stmt = True
                    elif auto_statement:
                        stmt_rows = extract_statement_rows(page)
                        # Use statement rows only if enough transactions found
                        if len(stmt_rows) >= 3:
                            rows = stmt_rows
                            using_stmt = True
                        else:
                            rows = extract_tables_from_page(page)
                    else:
                        rows = extract_tables_from_page(page)
                    rows = normalize_rows(rows, 5 if using_stmt else None)
                    if using_stmt and rows:
                        any_stmt_used = True
                    if (not using_stmt) and rows:
                        any_nonstmt_used = True
                    if include_meta and rows:
                        for r in rows:
                            file_rows.append([os.path.basename(pdf), str(page_num)] + r)
                    else:
                        file_rows.extend(rows)
                if file_rows:
                    width = max(len(r) for r in file_rows)
                    # Normalize all rows in the file to a consistent width to avoid DataFrame shape errors
                    file_rows = normalize_rows(file_rows, width)
                    if include_meta:
                        meta_width = 2
                    else:
                        meta_width = 0
                    if (statement_5col or auto_statement) and any_stmt_used and not any_nonstmt_used:
                        # Pure statement file: use named 5-column layout
                        base_cols = ["Date", "Description", "Debit", "Credit", "Balance"]
                        columns = (["SourceFile", "PageNumber"] + base_cols) if include_meta else base_cols
                    else:
                        # Mixed or generic: choose dynamic generic column names
                        data_cols = width - meta_width
                        if include_meta:
                            columns = ["SourceFile", "PageNumber"] + [f"Col{i}" for i in range(1, data_cols + 1)]
                        else:
                            columns = [f"Col{i}" for i in range(1, data_cols + 1)]
                    df = pd.DataFrame(file_rows, columns=columns)
                else:
                    if statement_5col or auto_statement:
                        empty_cols = (["SourceFile", "PageNumber"] + ["Date", "Description", "Debit", "Credit", "Balance"]) if include_meta else ["Date", "Description", "Debit", "Credit", "Balance"]
                        df = pd.DataFrame(columns=empty_cols)
                    else:
                        df = pd.DataFrame(columns=["SourceFile", "PageNumber", "Col1"] if include_meta else ["Col1"])  # empty
                if excel:
                    df.to_excel(out_path, index=False)
                else:
                    df.to_csv(out_path, index=False, encoding="utf-8-sig", sep=",", quoting=csv.QUOTE_MINIMAL)
                outputs.append(out_path)
                if combine:
                    combined_rows.extend(file_rows)
        except Exception as e:
            print(f"Skipping {pdf}: {e}")
            continue

    if combine:
        if combined_rows:
            width = max(len(r) for r in combined_rows)
            # Normalize combined rows to uniform width
            combined_rows = normalize_rows(combined_rows, width)
            if include_meta:
                columns = ["SourceFile", "PageNumber"] + [f"Col{i}" for i in range(1, width - 2 + 1)]
            else:
                columns = [f"Col{i}" for i in range(1, width + 1)]
            df_all = pd.DataFrame(combined_rows, columns=columns)
        else:
            df_all = pd.DataFrame(columns=["SourceFile", "PageNumber", "Col1"] if include_meta else ["Col1"])  # empty
        combined_path = os.path.join(output_dir, f"all_pdfs_combined.{'xlsx' if excel else 'csv'}")
        if excel:
            df_all.to_excel(combined_path, index=False)
        else:
            df_all.to_csv(combined_path, index=False, encoding="utf-8-sig", sep=",", quoting=csv.QUOTE_MINIMAL)
        outputs.append(combined_path)
        print(f"Wrote combined output: {combined_path}")

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
        help="Also write a combined output with all PDFs",
    )
    parser.add_argument(
        "--no-meta",
        action="store_true",
        help="Do not include SourceFile/PageNumber columns",
    )
    parser.add_argument(
        "--excel",
        action="store_true",
        help="Write Excel .xlsx files instead of CSV",
    )
    parser.add_argument(
        "--statement-5col",
        action="store_true",
        help="Extract in fixed 5-column layout: Date, Description, Debit, Credit, Balance",
    )
    parser.add_argument(
        "--auto-statement",
        action="store_true",
        help="Try statement layout per page; fallback to table/text if too few transactions",
    )

    args = parser.parse_args()
    outputs = batch_convert(
        input_pattern=args.input,
        output_dir=args.output_dir,
        combine=args.combine,
        include_meta=(not args.no_meta),
        excel=args.excel,
        statement_5col=args.statement_5col,
        auto_statement=args.auto_statement,
    )
    print("\nConversion complete. Outputs:")
    for p in outputs:
        print(p)


if __name__ == "__main__":
    main()
