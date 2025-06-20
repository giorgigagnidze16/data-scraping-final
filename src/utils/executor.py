from concurrent.futures import ThreadPoolExecutor, as_completed


def threaded_scrape_executor(
        scraper_cls,
        base_config,
        jobs: dict,  # e.g. {'laptops': '/s?k=laptops', ...}
        max_workers=None,  # number of parallel threads
        url_prefix: str = "",
):
    """
    threaded scrape executor for any scraper class.

    Args:
        scraper_cls: the scraper class to instantiate (with .scrape(url) and .close())
        base_config: base config dict for this scraper
        jobs: mapping of job name -> path or url (ex: {'laptops': '/s?k=laptops'})
        max_workers: max parallel threads (default: len(jobs))
        url_prefix: (optional) prefix for all jobs

    Returns:
        usually list of products
    """
    results = {}

    def worker(job_name, job_path):
        scraper = scraper_cls(base_config)
        url = f"{url_prefix}{job_path}"
        try:
            print(f"[{job_name}] Scraping {url}")
            items = scraper.scrape(url)
            print(f"[{job_name}] Done ({len(items)} items)")
            return job_name, items
        except Exception as e:
            print(f"[{job_name}] ERROR: {e}")
            return job_name, []
        finally:
            scraper.close()

    max_workers = max_workers or len(jobs)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(worker, job_name, job_path)
            for job_name, job_path in jobs.items()
        ]
        for future in as_completed(futures):
            job_name, items = future.result()
            results[job_name] = items
    return results
