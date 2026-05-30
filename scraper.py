import re
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://hybel.no"
SEARCH_URL = "https://hybel.no/bolig-til-leie/Trondheim--Norge/"
DEFAULT_PARAMS = [
    ("housing_in", "4"),
    ("housing_in", "5"),
    ("housing_in", "3"),
    ("order_by", "-created_at"),
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nb-NO,nb;q=0.9,en;q=0.8",
}


def fetch_page(page: int = 1) -> str:
    params = DEFAULT_PARAMS.copy()
    if page > 1:
        params.append(("page", str(page)))
    resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.text


def parse_total_pages(html: str) -> int:
    m = re.search(r"<strong>(\d+)</strong>\s*treff", html)
    if m:
        total = int(m.group(1))
        return max(1, (total + 11) // 12)
    return 1


def parse_listings(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    listings = []

    for a in soup.find_all("a", href=re.compile(r"^/bolig/\d+")):
        listing_id = a.get("id")
        if not listing_id:
            m = re.match(r"/bolig/(\d+)/", a["href"])
            listing_id = m.group(1) if m else None
        if not listing_id:
            continue

        title_el = a.find("h2", class_="card-title")
        title = title_el.get_text(" ", strip=True) if title_el else ""
        housing_type, size_sqm = _parse_title(title)

        body = a.find("div", class_="card-body")
        address = ""
        if body:
            p = body.find("p")
            if p:
                address = p.get_text(strip=True)

        price_el = a.find("span", class_="listing-price")
        rent = _parse_price(price_el.get_text(strip=True)) if price_el else None

        listings.append({
            "id": listing_id,
            "address": address,
            "rent": rent,
            "size_sqm": size_sqm,
            "housing_type": housing_type,
            "url": BASE_URL + a["href"],
            "title": title,
        })

    return listings


def _parse_title(title: str) -> tuple[str | None, int | None]:
    # "Rom i bofellesskap - 9m²" or "2 rom i bofellesskap - 11m²" or "Hybel - 35m²"
    m = re.match(r"^(.*?)\s*[-–]\s*(\d+)\s*m", title, re.IGNORECASE)
    if m:
        return m.group(1).strip(), int(m.group(2))
    return title or None, None


def _parse_price(text: str) -> int | None:
    # "5 500,-" or "5\xa0500,-"
    m = re.search(r"([\d\s\xa0]+),", text)
    if m:
        return int(re.sub(r"\s|\xa0", "", m.group(1)))
    return None


def scrape_all(max_pages: int | None = None) -> list[dict]:
    print("Fetching page 1...")
    html = fetch_page(1)
    total_pages = parse_total_pages(html)
    if max_pages:
        total_pages = min(total_pages, max_pages)
    print(f"Total pages: {total_pages}")

    all_listings = parse_listings(html)
    print(f"  Page 1: {len(all_listings)} listings")

    for page in range(2, total_pages + 1):
        time.sleep(0.75)
        print(f"  Page {page}/{total_pages}...")
        try:
            html = fetch_page(page)
            page_listings = parse_listings(html)
            all_listings.extend(page_listings)
        except Exception as e:
            print(f"  Error on page {page}: {e}")

    print(f"Total scraped: {len(all_listings)}")
    return all_listings
