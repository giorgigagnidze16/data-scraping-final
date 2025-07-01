
---

# Product Data Scraper & Analyzer

**A flexible, scalable pipeline for scraping, cleaning, analyzing, and reporting on product data from multiple e-commerce sources.**

---

## Features

* Multi-source scraping: Amazon, eBay, Newegg, MicroCenter (easily extensible)
* Modular, production-ready ETL pipeline (scraping → cleaning → analysis → export)
* PostgreSQL database support for full traceability & auditability
* Automated analytics, data quality checks, and comparative reporting
* Interactive command-line interface (CLI) for non-technical users
* Flexible data exports: CSV, Excel, JSON, HTML report
* Fully tested, maintainable codebase

---

## Table of Contents

* [Project Structure](#project-structure)
* [Requirements](#requirements)
* [Quickstart](#quickstart)
* [Configuration](#conf)
  * [Database Setup](#conf)
  * [Scraper Configuration](#conf)
* [Running the CLI](#running-the-cli)
* [Usage Examples](#usage-examples)
* [Advanced Usage](#advanced-usage)
* [Development & Contribution](#development--contribution)
* [Troubleshooting](#troubleshooting)

---

## Project Structure

```
src/
 ├── analysis/        # Analysis engines, statistics, reporting
 ├── cli/             # Interactive command-line interface
 ├── data/            # Database models and adapters
 ├── pipeline/        # Orchestration: ETL, orchestrators, entrypoints
 ├── scrapers/        # All web scrapers (Selenium, Scrapy, static)
 └── utils/           # Config, logger, helpers
config/
 ├── database.yaml    # Database connection config
 └── scrapers.yaml    # Per-site scraper configs/categories
data_output/          # Exports, reports, raw/cleaned data
tests/                # Full test suite (unit & integration)
run_cli.py       # CLI entrypoint
main.py          # (optional) Entrypoint
requirements.txt
README.md
```

---

## Requirements

* **Python 3+**
* **PostgreSQL+** (or compatible, for persistence)
* Chrome browser (for Selenium-based scrapers)
* [ChromeDriver](https://chromedriver.chromium.org/downloads) (make sure it matches your Chrome version)
* All dependencies in `requirements.txt`

---

## Quickstart

1. **Clone this repository:**

   ```bash
   git clone https://github.com/giorgigagnidze16/data-scraping-final
   cd data-scraping-final
   ```

2. **Install Python dependencies:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. **Set up your PostgreSQL database:**

   * Create a new database (e.g. `product_data`).
   * Create a user and grant privileges.

   Example:

   ```sql
   CREATE DATABASE product_data;
   CREATE USER scraper_user WITH ENCRYPTED PASSWORD 'password123';
   GRANT ALL PRIVILEGES ON DATABASE product_data TO scraper_user;
   ```
#### conf

4. **Configure database connection:**

   * Edit `config/database.yaml` with your DB credentials:

     ```yaml
     database:
       host: localhost
       port: 5432
       user: scraper_user
       password: password123
       dbname: product_data
     ```
5. **Configure scraping sources:**

   * Edit `config/scrapers.yaml` to specify which e-commerce sites and categories you want to scrape.
   * Example:

     ```yaml
     amazon:
       base_url: "https://www.amazon.com"
       categories:
         laptops: "/s?k=laptops"
         phones: "/s?k=phones"
       max_pages: 3
       delay: 2
     ```

6. **Download ChromeDriver** and make sure it’s in your PATH or provide its path explicitly.

---

## Running the CLI

Simply run:

```bash
python run_cli.py
```

You’ll be guided through database setup and presented with menu options:

* Run full pipeline (scrape → process → analyze → export)
* Explore/export/analyze data interactively

**Everything is menu-driven and beginner-friendly.**

---

## Usage Examples

### Run Full End-to-End Pipeline

Scrape, clean, analyze, and export reports with one click:

```
=== Welcome to Product Data Interactive CLI ===
--- Database Setup ---
Path to database config YAML [default: config/database.yaml]: 
Database configured successfully.

What would you like to do?
1. Run full pipeline (scrape → process → analyze → export)
2. Explore/export/analyze data
0. Exit

Enter choice (0-2): 1
```

### Explore Cleaned Data and Export

* Show raw or cleaned product tables
* Filter products (by category, price, etc.)
* Generate data quality reports (missing values, outliers, duplicates)
* Export results as CSV, Excel, or JSON

### Run Data Analysis & Visualization

* Generate statistical summaries by source/category
* Plot price distributions
* Show time-based price/review trends
* Generate a beautiful HTML dashboard/report

---

## Advanced Usage

* **Add new scrapers:**
  Implement a new scraper class and register with `ScraperFactory`.
* **Automate workflows:**
  Use modules from `src/pipeline` and `src/analysis` for custom automation or batch jobs.
* **Change DB or storage:**
  Swap out the DB adapter in `src/data/database.py` for other storage backends.

---

## Development & Contribution

* Full codebase is **fully unit and integration tested** (see `tests/`).

* Follow [PEP8](https://pep8.org/) and docstring conventions.

* To run all tests:

  ```bash
  pytest
  ```

* **Pull requests and suggestions are welcome!**

---

## Troubleshooting

* **Database connection errors:**
  Double-check credentials and that PostgreSQL is running.
* **Webdriver not found:**
  Ensure `chromedriver` is installed and in your system PATH.
* **Blocked by captchas:**
  Update your user-agent strings, try proxy rotation, or integrate [`fake-useragent`](https://github.com/hellysmile/fake-useragent). (Tried, didn't really help, only paid proxies worked)
* **No products scraped:**
  E-commerce site layout may have changed; check logs and update scrapers as needed.
* **Logs:**
  Check the `logs/` directory for error/debug information.

---

**Questions or feedback?**
Open an issue or contact the maintainers!

---

