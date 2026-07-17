from scraper import job_scraper, SEARCH_TERMS


def daily_scraper():
    for job in SEARCH_TERMS:
        job_scraper(
            job_title=job,
            target_location="Kuala Lumpur",
            date_range="daily",
            run_type="scheduled"
        )


if __name__ == "__main__":
    daily_scraper()