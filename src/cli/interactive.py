import sys
import os
from src.data import database
from src.utils.config import ConfigLoader
from src.cli.commands import (
    show_raw_products, show_clean_products, show_stats, show_columns,
    filter_products, filter_price, export_products, data_quality_report, generate_html_report,
    show_statistical_summary, show_grouped_summary, plot_distribution, show_trends, show_comparative_analysis
)
from src.pipeline.entrypoints import run_scrapers, process_pipeline, analyze_and_report

# ======================================================================
# ===============<<<<<>>>>> (MUST INCLUDE) <<<<<>>>>>===================
from src.scrapers.selenium.amazon_scraper import AmazonSeleniumScraper
from src.scrapers.selenium.ebay_selenium_scraper import EbaySeleniumScraper
from src.scrapers.static_scraper import MicroCenterStaticScraper
from src.scrapers.scrapy_crawler.newegg_crawler.spriders.newegg_scrapy import NeweggScrapyScraper
# ===============<<<<<>>>>> (MUST INCLUDE) <<<<<>>>>>===================
# ======================================================================

def configure_database_interactively():
    print("\n--- Database Setup ---")
    db_config_path = input("Path to database config YAML [default: config/database.yaml]: ").strip() or "config/database.yaml"
    if not os.path.exists(db_config_path):
        print(f"Error: File '{db_config_path}' does not exist. Exiting.")
        sys.exit(1)
    db_config = ConfigLoader(db_config_path).get_config("database")
    try:
        database.configure_engine(
            db_config["host"],
            db_config["port"],
            db_config["user"],
            db_config["password"],
            db_config["dbname"]
        )
    except Exception as e:
        print(f"Failed to configure database: {e}")
        sys.exit(1)
    print("Database configured successfully.\n")

def run_full_pipeline():
    print("\n[Step 1] Running scrapers...")
    raw_path = "data_output/raw/products_raw.json"
    all_products = run_scrapers(save_path=raw_path)
    print(f"Scraping complete. Raw data saved to: {raw_path}")

    print("[Step 2] Processing and cleaning scraped data...")
    df_clean = process_pipeline(raw_json_path=raw_path)
    clean_path = "data_output/raw/last-products_clean.json"
    df_clean.to_json(clean_path, orient="records", force_ascii=False, indent=2)
    print(f"Data cleaning complete. Clean data saved to: {clean_path}")

    print("[Step 3] Analyzing and exporting reports...")
    analyze_and_report(df_clean)
    print("Analysis and export complete.\n")

def analysis_menu():
    while True:
        print("\n=== Data Analysis & Visualization ===")
        print("1. Statistical summary")
        print("2. Summary by category")
        print("3. Summary by source")
        print("4. Price distribution plot")
        print("5. Time-based trends (price/review)")
        print("6. Comparative analysis (across sources)")
        print("7. Generate HTML report")
        print("0. Back to previous menu")
        choice = input("Choose option (0-7): ").strip()
        try:
            if choice == "1":
                show_statistical_summary()
            elif choice == "2":
                show_grouped_summary(by="category")
            elif choice == "3":
                show_grouped_summary(by="source")
            elif choice == "4":
                plot_distribution("price")
            elif choice == "5":
                show_trends()
            elif choice == "6":
                show_comparative_analysis()
            elif choice == "7":
                file = input("Output HTML file (default data_output/report.html): ") or "data_output/report.html"
                clean = input("Use cleaned data? (Y/n): ").lower() != "n"
                generate_html_report(outfile=file, clean=clean)
            elif choice == "0":
                break
            else:
                print("Invalid choice.")
        except Exception as e:
            print(f"Error: {e}")

def explore_menu():
    while True:
        print("\n=== Data Exploration ===")
        print("1. Show raw products")
        print("2. Show cleaned products")
        print("3. Filter products")
        print("4. Data quality report")
        print("5. Export products")
        print("6. Show columns")
        print("7. Show describe stats")
        print("8. Data analysis & visualization menu")
        print("0. Back to main menu")
        choice = input("Enter choice (0-8): ").strip()
        try:
            if choice == "1":
                n = int(input("How many rows? (default 10): ") or 10)
                show_raw_products(n=n)
            elif choice == "2":
                n = int(input("How many rows? (default 10): ") or 10)
                show_clean_products(n=n)
            elif choice == "3":
                col = input("Column to filter by (e.g. category): ")
                op = input("Operator (==, !=, >, <, >=, <=, contains, not contains): ").strip()
                val = input("Value to filter for: ")
                clean = input("Use cleaned data? (Y/n): ").lower() != "n"
                filter_products(col, op, val, clean=clean)
            elif choice == "4":
                clean = input("Use cleaned data? (Y/n): ").lower() != "n"
                data_quality_report(clean=clean)
            elif choice == "5":
                file = input("Output file name: ")
                filetype = input("Type (csv/json/xlsx) [default csv]: ") or "csv"
                clean = input("Use cleaned data? (Y/n): ").lower() != "n"
                export_products(file, filetype=filetype, clean=clean)
            elif choice == "6":
                clean = input("Use cleaned data? (Y/n): ").lower() != "n"
                show_columns(clean=clean)
            elif choice == "7":
                clean = input("Use cleaned data? (Y/n): ").lower() != "n"
                show_stats(clean=clean)
            elif choice == "8":
                analysis_menu()
            elif choice == "0":
                break
            else:
                print("Invalid choice.")
        except Exception as e:
            print(f"Error: {e}")

def interactive_cli():
    print("\n=== Welcome to Product Data Interactive CLI ===")
    configure_database_interactively()

    while True:
        print("\nWhat would you like to do?")
        print("1. Run full pipeline (scrape → process → analyze → export)")
        print("2. Explore/export/analyze data")
        print("0. Exit")
        choice = input("Enter choice (0-2): ").strip()

        if choice == "1":
            run_full_pipeline()
        elif choice == "2":
            explore_menu()
        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    interactive_cli()
