import re
import time
import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

INCLUDED_EDUCATION = [
    r"\bcse\b", r"\bcs\b", r"computer science", r"information technology",
    r"\bit\b", r"any degree", r"any graduate", r"b\.?e\.?", r"b\.?tech",
    r"engineering", r"software", r"programmer", r"technical officer",
    r"graduate", r"officer", r"assistant"
]

EXCLUDED_CUTOFFS = [
    r"70\s*%", r"75\s*%", r"80\s*%", r"7\.0\s*cgpa", r"7\.5\s*cgpa",
    r"first class with distinction", r"minimum 70%"
]

def get_headers() -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        response = requests.get(url, headers=get_headers(), timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

def is_profile_eligible(qualification_text: str, full_text: str = "") -> bool:
    content = f"{qualification_text} {full_text}".lower()
    has_education = any(re.search(pat, content) for pat in INCLUDED_EDUCATION)
    if not has_education:
        return False
    has_strict_cutoff = any(re.search(pat, content) for pat in EXCLUDED_CUTOFFS)
    if has_strict_cutoff:
        return False
    return True

def scrape_freejobalert_central() -> list[dict]:
    url = "https://www.freejobalert.com/government-jobs/"
    soup = fetch_page(url)
    jobs = []
    if not soup:
        return jobs

    for table in soup.find_all("table"):
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue

            post_date = cols[0].get_text(strip=True)
            org_name = cols[1].get_text(strip=True)
            role_name = cols[2].get_text(strip=True)
            qualification = cols[3].get_text(strip=True)
            last_date = cols[4].get_text(strip=True)
            link_tag = row.find("a", href=True)
            app_link = link_tag["href"] if link_tag else url

            if is_profile_eligible(qualification, f"{org_name} {role_name}"):
                jobs.append({
                    "org_name": org_name or "Central Govt Organization",
                    "role_name": role_name or "Technical / General Post",
                    "branches": qualification or "B.Tech CSE / IT / Any Graduate",
                    "app_start": post_date or "Check Notification",
                    "last_date": last_date or "Refer Notification",
                    "selection_procedure": "CBT / Written Test / Interview",
                    "app_fee": "As per official notification",
                    "app_link": app_link
                })
    return jobs

def scrape_telangana_jobs() -> list[dict]:
    url = "https://www.freejobalert.com/telangana-government-jobs/"
    soup = fetch_page(url)
    jobs = []
    if not soup:
        return jobs

    for table in soup.find_all("table"):
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            post_date = cols[0].get_text(strip=True)
            org_name = cols[1].get_text(strip=True)
            role_name = cols[2].get_text(strip=True) if len(cols) > 2 else ""
            qualification = cols[3].get_text(strip=True) if len(cols) > 3 else ""
            last_date = cols[4].get_text(strip=True) if len(cols) > 4 else "Refer Notification"
            link_tag = row.find("a", href=True)
            app_link = link_tag["href"] if link_tag else url

            if is_profile_eligible(qualification, f"{org_name} {role_name}"):
                jobs.append({
                    "org_name": f"Telangana: {org_name}",
                    "role_name": role_name or "Technical / State Cadre Post",
                    "branches": qualification or "B.Tech CSE / Any Graduate",
                    "app_start": post_date or "Active",
                    "last_date": last_date,
                    "selection_procedure": "TSPSC / State Board Written Exam + Verification",
                    "app_fee": "Refer TS Notification",
                    "app_link": app_link
                })
    return jobs

def scrape_indgovtjobs_all_india() -> list[dict]:
    url = "https://www.indgovtjobs.in/2015/10/Government-Jobs.html"
    soup = fetch_page(url)
    jobs = []
    if not soup:
        return jobs

    for table in soup.find_all("table"):
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            org_name = cols[0].get_text(strip=True)
            role_name = cols[1].get_text(strip=True)
            qualification = cols[2].get_text(strip=True) if len(cols) > 2 else ""
            last_date = cols[3].get_text(strip=True) if len(cols) > 3 else "Refer Notice"
            link_tag = row.find("a", href=True)
            app_link = link_tag["href"] if link_tag else url

            if is_profile_eligible(qualification, f"{org_name} {role_name}"):
                jobs.append({
                    "org_name": org_name or "PSU / Central Dept",
                    "role_name": role_name,
                    "branches": qualification or "B.Tech CSE / IT / Graduate",
                    "app_start": "Active",
                    "last_date": last_date,
                    "selection_procedure": "Online Examination + Interview",
                    "app_fee": "As per category guidelines",
                    "app_link": app_link
                })
    return jobs

def run_all_scrapers() -> list[dict]:
    all_jobs = []
    scrapers = [
        scrape_freejobalert_central,
        scrape_telangana_jobs,
        scrape_indgovtjobs_all_india
    ]

    for scraper in scrapers:
        try:
            logger.info(f"Running {scraper.__name__}...")
            results = scraper()
            all_jobs.extend(results)
            time.sleep(1.5)
        except Exception as e:
            logger.error(f"Error during {scraper.__name__}: {e}", exc_info=True)

    return all_jobs