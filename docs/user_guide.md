
---

# Product Data Scraper & Analyzer – User Guide

This guide will walk you through using the Product Data Scraper & Analyzer system via its interactive CLI. Whether you want to collect e-commerce product data, run analytics, or export clean datasets, you’ll find step-by-step instructions here.

---

## Table of Contents

* [Getting Started](#getting-started)
* [Running the CLI](#running-the-cli)
* [Main Menu Options](#main-menu-options)

  * [1. Run Full Pipeline](#1-run-full-pipeline)
  * [2. Explore/Export/Analyze Data](#2-exploreexportanalyze-data)
* [Data Exploration Features](#data-exploration-features)
* [Data Analysis & Visualization](#data-analysis--visualization)
* [Exporting Data](#exporting-data)
* [Troubleshooting](#troubleshooting)
* [Examples](#examples)

---

## Getting Started

Before you begin:

* Make sure you have Python 3+ and all dependencies installed.
* Configure your database connection in `config/database.yaml`.
* Edit `config/scrapers.yaml` to set which sites/categories you want to scrape.

---

## Running the CLI

To launch the interactive CLI, run:

```bash
python run_cli.py
```

You’ll be greeted with:

```
=== Welcome to Product Data Interactive CLI ===
--- Database Setup ---
Path to database config YAML [default: config/database.yaml]: 
Database configured successfully.
```

If you just press Enter, the default database config path will be used.

---

## Main Menu Options

After database setup, you’ll see:

```
What would you like to do?
1. Run full pipeline (scrape → process → analyze → export)
2. Explore/export/analyze data
0. Exit
```

### 1. Run Full Pipeline

Choose this to **scrape products, clean/process data, analyze, and export reports in one go.**
Just press `1` and the CLI will:

* Start all configured scrapers
* Clean and validate the scraped data
* Run analytics and export JSON/CSV reports to `data_output/`

You’ll see status updates for each step.

### 2. Explore/Export/Analyze Data

This lets you **interact with your data** after it’s been scraped. The submenu looks like:

```
=== Data Exploration ===
1. Show raw products
2. Show cleaned products
3. Filter products
4. Data quality report
5. Export products
6. Show columns
7. Show describe stats
8. Data analysis & visualization menu
0. Back to main menu
```

---

## Data Exploration Features

* **Show raw/cleaned products:** Preview data straight from your database or after cleaning.
* **Filter products:** Choose a column (e.g. `category`), operator (e.g. `==`), and value.

  * Example: To find laptops with price > 1000:

    ```
    Column to filter by (e.g. category): price
    Operator (==, !=, >, <, >=, <=, contains, not contains): >
    Value to filter for: 1000
    Use cleaned data? (Y/n): Y
    ```
* **Data quality report:** See counts of missing/duplicate fields, outliers, etc.
* **Export products:** Save selected products as CSV, JSON, or Excel.

---

## Data Analysis & Visualization

From the Data Exploration menu, choose option 8:

```
=== Data Analysis & Visualization ===
1. Statistical summary
2. Summary by category
3. Summary by source
4. Price distribution plot
5. Time-based trends (price/review)
6. Comparative analysis (across sources)
7. Generate HTML report
0. Back to previous menu
```

**Examples:**

* **Statistical summary:** View mean, median, quartiles, etc. for price/rating/review count.
* **Summary by category/source:** See grouped stats for categories or sources.
* **Plots and trends:** Generate price histograms and time-based trend reports.
* **Comparative analysis:** Compare prices/reviews for the same category across different e-commerce sources.
* **HTML Report:** Output a ready-to-share HTML dashboard of your data.

---

## Exporting Data

You can export any data subset:

* As CSV:

  * Choose “Export products” in the CLI, enter a file name and type (e.g. `export.csv`)
* As JSON or Excel:

  * Change the export type as prompted (e.g. `products.json`, `products.xlsx`)
* Full pipeline outputs:

  * After running the full pipeline, find outputs in `data_output/` (raw, cleaned, and processed files).

---

## Troubleshooting

* **Database connection errors:** Double-check `config/database.yaml` for host, port, user, password, dbname.
* **Scraper errors:** Make sure all target URLs and categories are set correctly in `config/scrapers.yaml`.
* **No products scraped:** The site’s layout may have changed; update your scraper or check logs for details.
* **Captcha or blocking:** Use proxy or `fake-useragent` for better rotation.

---

## Examples

### Example 1: Scrape and Analyze Everything

```bash
python run_cli.py
# Select option 1 (Run full pipeline)
```

* This will run the entire ETL process and save results.

### Example 2: Show Top 10 Cleaned Laptops

```
Enter choice (0-8): 2   # Show cleaned products
How many rows? (default 10): 10
```

### Example 3: Export Products with Price > 1200 to Excel

```
Enter choice (0-8): 3
Column to filter by (e.g. category): price
Operator (==, !=, >, <, >=, <=, contains, not contains): >
Value to filter for: 1200
Use cleaned data? (Y/n): y
# Review filtered products
# Then export:
Export filtered results? (Y/n): y
Output file name: some_data.csv
Type (csv/json/xlsx) [default csv]: 
Exported 140 rows to some_data.csv
```

---

## Feedback & Support

* **Check logs** in the `logs/` directory for detailed error reports.
* For bug reports or feature requests, please open an issue in the project repository.

---

**Enjoy analyzing your data!**
For advanced use (automated scripts, customizing scrapers, or integrating with your own pipeline), refer to the source code and in-line docstrings.

---
