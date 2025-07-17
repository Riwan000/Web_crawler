# crawler.py

import os
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser
from concurrent.futures import ThreadPoolExecutor

# Settings
USER_AGENT = "ScraperBot"
DOWNLOAD_DIR = "downloads"
MAX_WORKERS = 4  # Safe thread count per domain
CRAWL_DELAY = 1.5  # seconds between page loads

visited = set()
robots_cache = {}
download_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})

# Allowed file extensions
ALLOWED_EXTS = [".pdf", ".epub", ".html"]


def is_valid_file_link(link):
    return any(link.lower().endswith(ext) for ext in ALLOWED_EXTS)


def get_domain_folder(url):
    domain = urlparse(url).netloc.replace("www.", "")
    return os.path.join(DOWNLOAD_DIR, domain)


def is_allowed_by_robots(url):
    domain = urlparse(url).netloc
    base_url = f"{urlparse(url).scheme}://{domain}"

    if domain not in robots_cache:
        robots_url = urljoin(base_url, "/robots.txt")
        rp = robotparser.RobotFileParser()
        try:
            rp.set_url(robots_url)
            rp.read()
            robots_cache[domain] = rp
            print(f"[✓] robots.txt loaded for {domain}")
        except Exception as e:
            print(f"[!] Could not load robots.txt for {domain}: {e}")
            return False  # Fail safe: deny crawl

    return robots_cache[domain].can_fetch(USER_AGENT, url)


def download_file(url, folder):
    try:
        file_name = url.split("/")[-1].split("?")[0]
        file_path = os.path.join(folder, file_name)

        # Skip if already downloaded
        if os.path.exists(file_path):
            print(f"[↪] Already exists: {file_name}")
            return

        r = session.get(url, stream=True, timeout=20)
        r.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                f.write(chunk)

        print(f"[✓] Downloaded: {file_name}")
    except Exception as e:
        print(f"[X] Failed: {url} – {e}")


def queue_download(url, folder):
    if is_allowed_by_robots(url):
        download_executor.submit(download_file, url, folder)
    else:
        print(f"[🚫] Blocked by robots.txt: {url}")


def crawl(url, depth=2):
    if url in visited or depth <= 0:
        return

    if not is_allowed_by_robots(url):
        print(f"[🚫] Skipping page (robots.txt): {url}")
        return

    print(f"[*] Crawling: {url}")
    visited.add(url)

    try:
        res = session.get(url, timeout=20)
        res.raise_for_status()
        time.sleep(CRAWL_DELAY)

        soup = BeautifulSoup(res.text, "html.parser")
        base_folder = get_domain_folder(url)
        os.makedirs(base_folder, exist_ok=True)

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()

            # Ignore invalid links
            if href.startswith("mailto:") or href.startswith("javascript:") or not href:
                continue

            full_link = urljoin(url, href)

            # Skip external domains
            if urlparse(full_link).netloc != urlparse(url).netloc:
                continue

            # Download file if it's a valid doc
            if is_valid_file_link(full_link):
                queue_download(full_link, base_folder)
            else:
                # Continue crawling subpages within same domain
                crawl(full_link, depth=depth - 1)

    except Exception as e:
        print(f"[X] Error crawling {url}: {e}")
