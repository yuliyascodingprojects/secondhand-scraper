import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://clothesmentor.com"
COLLECTION = "/collections/all"
SORT = "&sort_by=created-descending"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def scrape_collection():
    page = 1
    products = []

    # while True:
    while page < 3:
        url = f"{BASE_URL}{COLLECTION}?page={page}{SORT}"
        print(f"Scraping page {page} → {url}")

        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print("Page returned non-200, stopping.")
            break

        soup = BeautifulSoup(response.text, "lxml")

        # print(soup)

        items = soup.select("div.grid-product, div.product-card, a.grid-product__link, a.product-card, li.grid__item")
        if not items:
            print("No products found on this page. Scraping finished.")
            break

        for item in items:
            link = item.find("a")
            if not link:
                continue

            product_url = link.get("href")
            if product_url.startswith("/"):
                product_url = BASE_URL + product_url

            title = link.get("title") or link.text.strip()

            # vendor_tag = item.find(class_="grid-product__vendor") or item.find(class_="product-card__vendor")
            # vendor = vendor_tag.text.strip() if vendor_tag else None

            products.append({
                "title": title,
                "url": product_url,
                # "vendor": vendor
            })

        page += 1
        time.sleep(1)

    return products


# --------- RUN SCRAPER ----------
all_products = scrape_collection()
print(f"\nTotal products scraped: {len(all_products)}")
# print (all_products[1])

target_brands = {"Ugg", "Imogene", "Sezane", "Bibi"}

matches = [
    p for p in all_products
    if any(b.lower() in (p["vendor"] or "").lower() or b.lower() in p["title"].lower()
           for b in target_brands)
]

print("Matches:")
for m in matches:
    print(m)