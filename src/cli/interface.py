import argparse

from src.pipeline.entrypoints import run_scrapers, process_pipeline, analyze_and_report


def main():
    parser = argparse.ArgumentParser(description="Product Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Scrape
    sp_scrape = subparsers.add_parser("scrape", help="Run all scrapers and save raw data")
    sp_scrape.add_argument("--scrapers-config", default="config/scrapers.yaml")
    sp_scrape.add_argument("--out", default="data_output/raw/products_raw.json")
    sp_scrape.add_argument("--max-workers", type=int, default=4)

    # Process
    sp_process = subparsers.add_parser("process", help="Process raw scraped data and save clean results")
    sp_process.add_argument("--in", dest="input", required=True, help="Input raw JSON file from scrapers")
    sp_process.add_argument("--db-config", default="config/database.yaml")

    # Analyze
    sp_analyze = subparsers.add_parser("analyze", help="Analyze cleaned data and export reports")
    sp_analyze.add_argument("--in", dest="input", required=True, help="Input clean JSON file for analysis")
    sp_analyze.add_argument("--out-dir", default="data_output")

    # All (run the full pipeline)
    sp_all = subparsers.add_parser("all", help="Run scrapers, process, and analyze all in one go")

    args = parser.parse_args()

    if args.command == "scrape":
        run_scrapers(scrapers_config=args.scrapers_config, max_workers=args.max_workers, save_path=args.out)
    elif args.command == "process":
        process_pipeline(raw_json_path=args.input, db_config=args.db_config)
    elif args.command == "analyze":
        import pandas as pd
        df_clean = pd.read_json(args.input)
        analyze_and_report(df_clean, output_dir=args.out_dir)
    elif args.command == "all":
        all_products = run_scrapers()
        df_clean = process_pipeline(products=all_products)
        analyze_and_report(df_clean)
    else:
        parser.print_help()
