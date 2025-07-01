
---

# Technical Architecture Document

## Overview

This document describes the architecture of the Product Scraping and Analytics System, designed to collect, process, analyze, and report on product data from multiple e-commerce platforms (e.g., Amazon, eBay, Newegg, MicroCenter). The system is modular, extensible, and built with scalability and maintainability in mind, utilizing modern Python practices and established software design patterns.

## System Goals

* **Multi-source scraping:** Support multiple e-commerce sites with different extraction methods (Selenium, Scrapy, static requests).
* **Clean and normalize data:** Standardize, validate, and deduplicate data from diverse sources.
* **Analytics and reporting:** Produce business-relevant statistics, trend analyses, and exportable reports.
* **Traceability:** Persist both raw and cleaned data, plus analysis results, in a relational database for auditability.
* **Extensibility:** Easily support new data sources and analytics without major rewrites.
* **Usability:** Provide both CLI and programmatic interfaces for various user needs.

---

## High-Level Architecture

The system is divided into the following major layers and modules:

1. **Scrapers:**
   Specialized classes for fetching and parsing product data from each site (e.g., AmazonSeleniumScraper, EbaySeleniumScraper, NeweggScrapyScraper, MicroCenterStaticScraper).

2. **Scraper Orchestrator:**
   Manages configuration and parallel execution of all registered scrapers, aggregating results into a unified dataset.

3. **Data Pipeline:**
   Coordinates the flow from raw data ingestion, through cleaning, to analysis and reporting. Handles database storage, file exports, and error management.

4. **Product Data Processor:**
   Responsible for data normalization: cleaning, deduplication, field conversions, and data quality reporting.

5. **Analysis & Reporting Engine:**
   Performs descriptive statistics, group-by summaries, trend analysis, and generates both human-readable and machine-consumable reports.

6. **Database Layer:**
   Uses SQLAlchemy ORM for PostgreSQL, persisting all raw/cleaned data and analytics results for reproducibility.

7. **CLI (Command Line Interface):**
   Provides interactive and scriptable entrypoints for running the pipeline, exploring data, and generating reports.

---

## Key Data Flow

1. **Scraping Phase:**
   The `ScraperOrchestrator` loads scraper configurations from YAML, creates scraper instances via `ScraperFactory`, and runs each scraper (in parallel subprocesses when possible). Each scraper fetches product data for its configured categories, parses HTML pages, and emits a list of normalized product dicts. Scrapers support both Selenium and Scrapy engines depending on the target website.

2. **Raw Data Storage:**
   All raw product dictionaries are saved to the database for traceability, using a normalized schema that allows for auditing and recovery.

3. **Cleaning & Processing:**
   The `ProductDataProcessor` loads raw records, standardizes fields, converts types, fills missing values, lowercases categories/sources, and deduplicates on product URL. A data quality report is generated at this stage to surface any major issues.

4. **Clean Data Storage:**
   Cleaned, validated product records are written back to the database and exported as CSV/JSON/Excel files for further inspection.

5. **Analysis:**
   The `AnalysisEngine` computes a wide range of statistics: per-source, per-category, and overall summaries; outlier detection; time-based and categorical trend analysis; comparative analytics across data sources. All results are persisted for future reporting.

6. **Reporting & Export:**
   Reports are generated as JSON (for programmatic use), CSV (for data science/BI), and via console output for fast inspection. Custom HTML and visualizations can be added if required.

7. **CLI/UX Layer:**
   Users interact with the system via a CLI, enabling them to run the full pipeline, generate reports, filter or export data, and trigger analyses on demand.

---

## Design Patterns & Principles

The architecture employs several industry-standard patterns:

* **Factory Pattern:**
  The `ScraperFactory` registers all scraper classes and is used to instantiate the appropriate scraper at runtime based on config.

* **Strategy Pattern:**
  Each scraper implements the same interface (via `BaseScraper`), but uses different fetching/parsing logic depending on site and technology.

* **Template Method Pattern:**
  The abstract `BaseScraper` provides the workflow (`scrape` = fetch + parse), letting subclasses override just what’s needed.

* **Facade Pattern:**
  Both the `DataPipeline` and `AnalysisEngine` act as facades, providing a high-level, simplified API over a set of complex operations.

* **Decorator Pattern:**
  Scraper registration is handled via a class decorator (`@ScraperFactory.register('name')`), making extension simple.

* **Singleton/Global Resource:**
  The database engine/session is a shared global resource, initialized once per run.

* **Adapter Pattern:**
  Data processing logic (cleaning, normalization) makes all data from different sources look the same.

* **Command Pattern:**
  The CLI commands are mapped to discrete functions for each user action, making it easy to add new features.

---

## Scalability & Extensibility

* **Adding a New Scraper:**
  Simply implement a new scraper class (inheriting from `BaseScraper`), decorate it with `@ScraperFactory.register('site_name')`, and add its config. No core changes needed.

* **Supporting New Analytics:**
  Add new methods to `AnalysisEngine` or plug in new engines. All analytics are orchestrated in a single place.

* **Deployment:**
  The system is designed to be run locally or on a server, with Python’s process/thread pools providing horizontal scaling during scraping.

---

## Fault Tolerance & Logging

* **Resilient Scraping:**
  Scrapers include retry logic, user-agent rotation, and can handle CAPTCHA or proxy failures gracefully.

* **Error Handling:**
  All major phases (scraping, cleaning, DB, analysis) use structured logging and try/except blocks to ensure that errors in one source/category do not crash the entire pipeline.

* **Auditing:**
  Every record is timestamped and saved both raw and clean, supporting audit trails and reproducibility.

---

## Technology Stack

* **Python 3.10+**
* **Selenium** and **Scrapy** for web automation and scraping.
* **BeautifulSoup** for HTML parsing.
* **SQLAlchemy** ORM with **PostgreSQL** for data storage.
* **Pandas** for all data cleaning, aggregation, and analytics.
* **Pytest** for unit/integration testing.
* **YAML** for configuration.
* **Logging** for monitoring and troubleshooting.

---

## Summary

This architecture provides a robust, maintainable, and scalable platform for data extraction, cleaning, and analytics from multiple web sources. The use of classic design patterns, modular structure, and extensible configuration ensures that the system can grow with new requirements and data sources over time, while keeping code maintainable and onboarding for new developers straightforward.

---

**For questions or contributions, see the README or contact the maintainers.**
