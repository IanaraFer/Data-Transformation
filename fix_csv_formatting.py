#!/usr/bin/env python3
"""
Script to fix formatting issues in the CSV file.
Removes euro symbols (€) from Debit and Credit columns.
"""

import pandas as pd
import sys


def fix_csv_formatting(input_file: str, output_file: str = None):
    """
    Fix formatting issues in CSV file:
    - Remove euro symbols (€) from Debit and Credit columns
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (defaults to overwriting input)
    """
    if output_file is None:
        output_file = input_file
    
    # Read the CSV file
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    print(f"Processing file: {input_file}")
    print(f"Total rows: {len(df)}")
    
    # Count rows with euro symbols before cleaning
    debit_with_euro = df['Debit'].astype(str).str.contains('€', na=False).sum()
    credit_with_euro = df['Credit'].astype(str).str.contains('€', na=False).sum()
    
    print(f"Rows with € in Debit column: {debit_with_euro}")
    print(f"Rows with € in Credit column: {credit_with_euro}")
    
    # Remove euro symbols from Debit and Credit columns
    df['Debit'] = df['Debit'].astype(str).str.replace('€', '', regex=False).str.strip()
    df['Credit'] = df['Credit'].astype(str).str.replace('€', '', regex=False).str.strip()
    
    # Replace 'nan' strings back to empty strings
    df['Debit'] = df['Debit'].replace('nan', '')
    df['Credit'] = df['Credit'].replace('nan', '')
    
    # Write the cleaned CSV file
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\nCleaned CSV written to: {output_file}")
    print("✓ Removed euro symbols from monetary values")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_csv_formatting.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    fix_csv_formatting(input_file, output_file)
