import requests
from bs4 import BeautifulSoup
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

# Initialize a push gateway registry
registry = CollectorRegistry()
gauge_failed = Gauge('site_failed', 'Number of failed sites', labelnames=['site'], registry=registry)
gauge_success = Gauge('site_success', 'Number of successful sites', labelnames=['site'], registry=registry)

# List of URLs to scrape
sites = [
    'https://example.com',
    'https://another-site.com'
]

# Web scraping function
def check_site_status(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Assuming status is marked in the HTML by a class or id
        status = soup.find('div', {'class': 'status'}).text.strip()  # adjust based on the HTML structure
        
        if "Failed" in status:
            print(f"{url} - \033[91mFAILED\033[0m")  # Red for failed
            gauge_failed.labels(site=url).set(1)
        elif "Success" in status:
            print(f"{url} - \033[92mSUCCESS\033[0m")  # Green for success
            gauge_success.labels(site=url).set(1)
        else:
            print(f"{url} - UNKNOWN")
        
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        gauge_failed.labels(site=url).set(1)  # Mark as failed in case of error

# Check the status of all sites
for site in sites:
    check_site_status(site)

# Push data to Push Gateway
push_to_gateway('localhost:9091', job='web_scraper_status', registry=registry)
