import subprocess
import requests
import argparse
import logging
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO or ERROR in production
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger()

# Configuration for each environment
CONFIG = {
    "prod": {
        "autosys_jobs": ["prod_job1", "prod_job2", "prod_job3"],
        "urls": ["https://prod.example1.com", "https://prod.example2.com"],
        "webscrape_url": "https://prod.example-webscrape.com"
    },
    "qa": {
        "autosys_jobs": ["qa_job1", "qa_job2"],
        "urls": ["https://qa.example1.com", "https://qa.example2.com"],
        "webscrape_url": "https://qa.example-webscrape.com"
    },
    "uat": {
        "autosys_jobs": ["uat_job1", "uat_job2"],
        "urls": ["https://uat.example1.com", "https://uat.example2.com"],
        "webscrape_url": "https://uat.example-webscrape.com"
    },
}

# Initialize Prometheus Gauges
registry = CollectorRegistry()
auto_status_gauge = Gauge(
    "auto_status", "Status of Autosys jobs", labelnames=["job_name"], registry=registry
)
url_status_gauge = Gauge(
    "url_status", "Status of monitored URLs", labelnames=["url"], registry=registry
)
webscrape_gauge = Gauge(
    "webscrape_data", "Web scraping results with content", labelnames=["scrape_field"], registry=registry
)

# Check Autosys Job Status
def check_autosys_jobs(autosys_jobs):
    for job in autosys_jobs:
        try:
            logger.info(f"Checking Autosys job status for {job}...")
            result = subprocess.run(
                ["autostatus", "-J", job],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Simulate job status: Success (0) or Failure (1)
            job_status = 1 if "FAILURE" in result.stdout.upper() else 0
            auto_status_gauge.labels(job_name=job).set(job_status)
            logger.info(f"Job {job} status: {'FAILURE' if job_status == 1 else 'SUCCESS'}")
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout occurred while checking job {job}")
            auto_status_gauge.labels(job_name=job).set(0)
        except Exception as e:
            logger.error(f"Error checking job {job}: {e}")
            auto_status_gauge.labels(job_name=job).set(0)

# Check URL Status
def check_urls(urls):
    for url in urls:
        try:
            logger.info(f"Checking URL status for {url}...")
            response = requests.get(url, timeout=10)
            url_status_gauge.labels(url=url).set(response.status_code == 200)
            logger.info(f"URL {url} status: {'UP' if response.status_code == 200 else 'DOWN'}")
        except Exception as e:
            logger.error(f"Error checking URL {url}: {e}")
            url_status_gauge.labels(url=url).set(0)

# Web Scraping with Content
def web_scrape_site(webscrape_url):
    try:
        logger.info(f"Scraping web content from {webscrape_url}...")
        response = requests.get(webscrape_url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Example: Scraping specific content
        title = soup.title.string if soup.title else "No title"
        meta_description = soup.find("meta", attrs={"name": "description"})
        meta_description_content = meta_description["content"] if meta_description else "No description"
        div_count = len(soup.find_all("div"))

        # Sending content as metrics with meaningful labels
        webscrape_gauge.labels(scrape_field="title").set(len(title))
        webscrape_gauge.labels(scrape_field="meta_description_length").set(len(meta_description_content))
        webscrape_gauge.labels(scrape_field="div_count").set(div_count)
        logger.info(f"Scraped data: Title length: {len(title)}, Meta description length: {len(meta_description_content)}, Div count: {div_count}")
    except Exception as e:
        logger.error(f"Error scraping site: {e}")
        webscrape_gauge.labels(scrape_field="error").set(1)

# Main Function
def main(env, job_name, pushgateway_url):
    if env not in CONFIG:
        logger.error(f"Invalid environment '{env}'. Valid options are: {list(CONFIG.keys())}")
        return

    config = CONFIG[env]
    autosys_jobs = config["autosys_jobs"]
    urls = config["urls"]
    webscrape_url = config["webscrape_url"]

    # Perform checks
    check_autosys_jobs(autosys_jobs)
    check_urls(urls)
    web_scrape_site(webscrape_url)

    # Push data to Push Gateway
    try:
        logger.info(f"Pushing data to Prometheus Push Gateway at {pushgateway_url} with job name '{job_name}'...")
        push_to_gateway(pushgateway_url, job=job_name, registry=registry)
        logger.info(f"Data successfully pushed to Prometheus Push Gateway for environment '{env}' and job '{job_name}'.")
    except Exception as e:
        logger.error(f"Error pushing data to Push Gateway: {e}")

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="Monitor jobs, URLs, and web-scraping results.")
    parser.add_argument("--env", required=True, help="Environment (prod, qa, uat)")
    parser.add_argument("--job_name", required=True, help="Custom job name for Prometheus push")
    parser.add_argument("--pushgateway_url", required=True, help="Push Gateway URL")

    args = parser.parse_args()
    main(args.env, args.job_name, args.pushgateway_url)
