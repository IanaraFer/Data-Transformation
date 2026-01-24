# 📊 PDF to Excel & CSV Data Transformation Project

Welcome! This project helps you extract data from PDF files, clean it up, and export it to Excel and CSV formats - perfect for financial reporting and data analysis.

## 🎯 What Does This Project Do?

Have you ever received financial reports, invoices, or data tables locked inside a PDF file? This project solves that problem! It:

1. **Extracts tables from PDFs** - Automatically pulls out all the data tables from your PDF documents
2. **Cleans the data** - Removes duplicates, fixes formatting issues, handles missing values
3. **Organizes everything** - Sorts and structures your data properly
4. **Exports to usable formats** - Saves as Excel (.xlsx) with professional formatting AND CSV for universal compatibility
5. **Handles big files** - Can split large datasets into manageable chunks

## 💡 Who Is This For?

- **Finance professionals** who need to analyze data from PDF reports
- **Data analysts** working with data trapped in PDFs
- **Business users** who receive invoices or statements as PDFs
- **Anyone** who wants to convert PDF tables into spreadsheets quickly

## 🚀 Getting Started

### What You Need
- Python 3.7 or higher
- Jupyter Notebook or VS Code
- Basic understanding of running Python code (we'll guide you!)

### Quick Start Guide

1. **Open the notebook** - Start with `part_01/pdf-cvs-part01.ipynb`
2. **Run the first cell** - This installs all required libraries automatically
3. **Follow the examples** - Each section is explained step-by-step
4. **Use your own PDFs** - Replace the example with your actual PDF file path

## 📁 What's Inside?

### Part 01 - Complete Workflow
- **Setup & Libraries** - Automatic installation of everything you need
- **PDF Extraction** - Functions to read tables from PDFs
- **Data Cleaning** - Remove junk, fix formatting, standardize data
- **Type Conversion** - Auto-detect dates, numbers, and text
- **Data Organization** - Sort and structure your data
- **Excel Export** - Create beautiful, formatted Excel files
- **CSV Export** - Generate lightweight, universal CSV files
- **Visualizations** - Charts showing file formats and data quality
- **Chunking Tools** - Split large files into smaller parts

### Example Workflow Included
The notebook includes a complete working example with sample data, so you can see how everything works before using your own files.

## 🛠️ Key Features

### ✅ Smart Data Extraction
- Reads multi-page PDFs
- Extracts all tables automatically
- Tracks which page each table came from

### ✅ Professional Data Cleaning
- Removes duplicate entries
- Trims extra whitespace
- Handles missing values intelligently
- Standardizes column names
- Reports data quality issues

### ✅ Beautiful Excel Output
- Formatted headers with colors
- Auto-adjusted column widths
- Frozen header rows for scrolling
- Currency formatting for financial data
- Summary sheet with metadata

### ✅ Universal CSV Export
- Lightweight and fast
- Works with any tool (Excel, Google Sheets, databases)
- UTF-8 encoding for international characters

### ✅ Big Data Ready
- Split large datasets into 25 MB chunks
- Merge chunks back together when needed
- Memory-efficient processing

## 📊 Visual Guides Included

The notebook includes helpful visualizations:
- **File Format Comparison** - Understand PDF vs CSV vs Excel
- **Data Pipeline Flowchart** - See the transformation process
- **Quality Metrics** - Track data improvements at each step

## 🎓 Learning Path

**Beginner?** Start here:
1. Run cells 1-3 to set up your environment
2. Look at the sample data example (cells 19-22)
3. See the cleaning process in action
4. Check out the exported files in `output_example/`

**Intermediate?** Focus on:
1. Understanding the extraction function (cell 5)
2. Customizing the cleaning rules (cell 7)
3. Modifying Excel formatting (cell 13)

**Advanced?** Explore:
1. The complete pipeline function (cell 17)
2. Chunk splitting for large files (cells 30-36)
3. Custom visualization code (cells 24-28)

## 💻 Common Use Cases

### Example 1: Monthly Financial Reports
```python
# Extract data from monthly PDF report
df_list = extract_tables_from_pdf('monthly_report.pdf')
df_clean = clean_data(df_list[0])
df_converted = convert_data_types(df_clean)
export_to_excel(df_converted, 'monthly_report.xlsx')
```

### Example 2: Complete Pipeline
```python
# Process everything in one go
complete_pdf_processing_pipeline(
    pdf_path='invoice.pdf',
    output_dir='output',
    excel_name='invoice_data.xlsx',
    csv_name='invoice_data.csv'
)
```

### Example 3: Large Dataset Handling
```python
# Split large dataset into manageable chunks
split_dataframe_by_size(
    df_large, 
    chunk_size_mb=25, 
    output_dir='output_chunks'
)
```

## 📝 Parts Structure

### Part 01 (Current)
- **File:** `part_01/pdf-cvs-part01.ipynb`
- **Size:** 0.50 MB
- **Contains:** All functions, examples, and visualizations

*Note: Additional parts will appear here automatically if the notebook grows beyond 25 MB*

## 🔧 Customization Tips

1. **Change chunk size:** Modify `chunk_size_mb=25` to your preferred size
2. **Excel formatting:** Edit the `export_to_excel()` function for custom colors/styles
3. **Data cleaning rules:** Adjust the `clean_data()` function for your specific needs
4. **Column detection:** Customize the type conversion logic in `convert_data_types()`

## 📞 Need Help?

Each section in the notebook includes:
- **Detailed explanations** of what the code does
- **Example usage** showing how to call functions
- **Sample data** to test without a real PDF
- **Error handling** that explains what went wrong

## 🎉 Success Stories

This workflow helps you:
- ✅ Save hours of manual data entry
- ✅ Reduce errors from copy-paste mistakes
- ✅ Create professional reports quickly
- ✅ Standardize data across multiple PDFs
- ✅ Automate repetitive data extraction tasks

## 📚 What You'll Learn

By working through this notebook, you'll learn:
- How to work with PDFs programmatically
- Data cleaning best practices
- Pandas DataFrame manipulation
- Excel automation with Python
- Data quality validation techniques
- Big data handling strategies

## 🚦 Quick Reference

| Need to... | Go to Cell | Function Name |
|-----------|-----------|---------------|
| Extract from PDF | 5 | `extract_tables_from_pdf()` |
| Clean data | 7 | `clean_data()` |
| Convert types | 9 | `convert_data_types()` |
| Export to Excel | 13 | `export_to_excel()` |
| Export to CSV | 15 | `export_to_csv()` |
| Complete workflow | 17 | `complete_pdf_processing_pipeline()` |
| Split large files | 30 | `split_dataframe_by_size()` |

---

**Ready to get started?** Open `part_01/pdf-cvs-part01.ipynb` and begin your data transformation journey! 🚀

*Last updated: January 2026*
