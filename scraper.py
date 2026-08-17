import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Education match keywords
INCLUDED_EDUCATION = [
    r"\bcse\b", r"\bcs\b", r"computer science", r"information technology",
    r"\bit\b", r"any degree", r"any graduate", r"b\.?e\.?", r"b\.?tech",
    r"engineering", r"software", r"programmer", r"technical officer"
]

# Strict cutoffs higher than 6.64 CGPA (~66.4%)
EXCLUDED_CUTOFFS = [
    r"70\s*%", r"75\s*%", r"80\s*%", r"7\.0\s*cgpa", r"7\.5\s*cgpa",
    r"first class with distinction", r"minimum 70%"
]

def get_headers() -> dict:
    ua = UserAgent()
    return {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive"
    }

def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None

def is_profile_eligible(qualification_text: str, full_text: str = "") -> bool:
    content = f"{qualification_text} {full_text}".lower()
    
    # Check educational match
    has_matching_education = any(re.search(pattern, content) for pattern in INCLUDED_EDUCATION)
    if not has_matching_education:
        return False

    # Check for strict >66.4% score barriers
    has_ineligible_cutoff = any(re.search(pattern, content) for pattern in EXCLUDED_CUTOFFS)
    if has_ineligible_cutoff:
        return False

    return True

def scrape_freejobalert_central() -> list[dict]:
    url = "https://www.freejobalert.com/government-jobs/"
    soup = fetch_page(url)
    jobs = []
    if not soup:
        return jobs

    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue

            post_date = cols[0].get_text(strip=True)
            org_name = cols[1].get_text(strip=True)
            role_name = cols[2].get_text(strip=True)
            qualification = cols[3].get_text(strip=True)
            last_date = cols[4].get_text(strip=True)
            
            link_tag = cols[-1].find("a", href=True) if len(cols) >= 6 else row.find("a", href=True)
            app_link = link_tag["href"] if link_tag else url

            if is_profile_eligible(qualification, f"{org_name} {role_name}"):
                jobs.append({
                    "org_name": org_name or "Central Govt Organization",
                    "role_name": role_name or "Technical / General Post",
                    "branches": qualification or "B.Tech CSE / IT / Any Graduate",
                    "app_start": post_date or "Check Notification",
                    "last_date": last_date or "Refer Notification",
                    "selection_procedure": "CBT / Technical Exam / Interview (Check Notification)",
                    "app_fee": "As per official notification",
                    "app_link": app_link
                })
    return jobs

def scrape_indgovtjobs_telangana() -> list[dict]:
    url = "https://telangana.indgovtjobs.net/jobs/"
    soup = fetch_page(url)
    jobs = []
    if not soup:
        return jobs

    for article in soup.find_all(["article", "div"], class_=re.compile(r"post|job|item")):
        title_tag = article.find(["h2", "h3", "a"])
        if not title_tag:
            continue
            
        title_text = title_tag.get_text(strip=True)
        link_tag = article.find("a", href=True)
        app_link = link_tag["href"] if link_tag else url
        snippet = article.get_text(separator=" ", strip=True)

        if is_profile_eligible(snippet, title_text):
            jobs.append({
                "org_name": "Telangana State Recruitment",
                "role_name": title_text,
                "branches": "B.Tech CSE / IT / Any Graduate (Telangana Region)",
                "app_start": "Announced",
                "last_date": "Check Official Portal",
                "selection_procedure": "Written Test / Interview",
                "app_fee": "Refer TSPSC / Official Portal",
                "app_link": app_link
            })
    return jobs

def scrape_indgovtjobs_all_india() -> list[dict]:
    url = "https://www.indgovtjobs.in/2015/10/Government-Jobs.html"
    soup = fetch_page(url)
    jobs = []
    if not soup:
        return jobs

    tables = soup.find_all("table")
    for table in tables:
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
        scrape_indgovtjobs_telangana,
        scrape_indgovtjobs_all_india
    ]

    for scraper in scrapers:
        try:
            logger.info(f"Running {scraper.__name__}...")
            results = scraper()
            all_jobs.extend(results)
            time.sleep(2)  # Rate limiting between domains
        except Exception as e:
            logger.error(f"Error during {scraper.__name__}: {e}", exc_info=True)

    return all_jobs