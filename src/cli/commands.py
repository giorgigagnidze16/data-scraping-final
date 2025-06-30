import pandas as pd
import os
from src.data.database import load_products, load_products_raw
from src.data.processors import ProductDataProcessor
from src.analysis.analysis_engine import AnalysisEngine

def show_table(df, n=10, tail=False):
    """
    Print the first or last n rows of a DataFrame.
    """
    if df.empty:
        print("No data found.")
        return
    if tail:
        print(df.tail(n).to_string(index=False))
    else:
        print(df.head(n).to_string(index=False))

def show_raw_products(n=10, tail=False):
    """Show raw products (head/tail)."""
    df = load_products_raw()
    show_table(df, n=n, tail=tail)

def show_clean_products(n=10, tail=False):
    """Show cleaned products (head/tail)."""
    df = load_products()
    show_table(df, n=n, tail=tail)

def show_stats(clean=True):
    """Show DataFrame.describe() for raw or cleaned data."""
    df = load_products() if clean else load_products_raw()
    print(df.describe(include='all').transpose())

def show_columns(clean=True):
    """Show column names for raw or cleaned data."""
    df = load_products() if clean else load_products_raw()
    print("Columns:", ", ".join(df.columns))

def filter_products(column, value, contains=False, clean=True):
    """Show products filtered by column (exact or substring match)."""
    df = load_products() if clean else load_products_raw()
    if column not in df.columns:
        print(f"Column '{column}' not found.")
        return
    if contains:
        df = df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
    else:
        df = df[df[column] == value]
    show_table(df, n=min(20, len(df)))

def filter_price(min_price=None, max_price=None, clean=True):
    """Show products within a price range."""
    df = load_products() if clean else load_products_raw()
    if min_price is not None:
        df = df[df['price'] >= float(min_price)]
    if max_price is not None:
        df = df[df['price'] <= float(max_price)]
    show_table(df, n=min(20, len(df)))

def export_products(file, filetype="csv", clean=True, **filters):
    """
    Export products (clean/raw) as csv/json/xlsx, optionally filtered.
    """
    df = load_products() if clean else load_products_raw()
    for col, val in filters.items():
        if col in df.columns and val:
            df = df[df[col] == val]
    if filetype == "csv":
        df.to_csv(file, index=False)
    elif filetype == "json":
        df.to_json(file, orient='records', force_ascii=False, indent=2)
    elif filetype in ("xlsx", "excel"):
        df.to_excel(file, index=False)
    else:
        print("Unsupported export type.")
        return
    print(f"Exported {len(df)} rows to {file}")

def data_quality_report(clean=True):
    """Print data quality report."""
    df = load_products() if clean else load_products_raw()
    processor = ProductDataProcessor(df)
    processor.clean_and_validate()  # optional for clean=True
    report = processor.get_data_quality_report()
    print("=== Data Quality Report ===")
    for k, v in report.items():
        print(f"{k:20}: {v}")

def generate_html_report(outfile="data_output/report.html", clean=True):
    """Generate a simple HTML report with summary stats and sample data."""
    df = load_products() if clean else load_products_raw()
    analysis = AnalysisEngine(df)
    stats = analysis.summary_statistics()
    nulls = analysis.nulls()
    uniques = analysis.uniques()
    html = "<html><head><title>Product Data Report</title></head><body>"
    html += "<h1>Product Data Report</h1>"
    html += "<h2>Summary Statistics</h2>"
    html += pd.DataFrame(stats).to_html()
    html += "<h2>Missing Values</h2><pre>" + str(nulls) + "</pre>"
    html += "<h2>Unique Values</h2><pre>" + str(uniques) + "</pre>"
    html += "<h2>Sample Data</h2>" + df.head(20).to_html()
    html += "</body></html>"
    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report written to {outfile}")

# You could add more, e.g. matplotlib/seaborn chart generation here!
