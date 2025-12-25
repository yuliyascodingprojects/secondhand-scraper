import requests
from bs4 import BeautifulSoup
import time
import json
import re
import unicodedata

BASE_URL = "https://clothesmentor.com"
COLLECTION = "/collections/all"
SORT = "&sort_by=created-descending"
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# pull brands from external file
def load_brands(path="brands.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# strip text down to lowercase letters 
def normalize(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower()

# safely checks for match in brand names
def brand_matches(brand, text):
    brand_norm = normalize(brand)
    text_norm = normalize(text)

    pattern = re.escape(brand_norm)
    return re.search(pattern, text_norm) is not None
   
# scrape each page of website in order
def scrape_collection():
    page = 1
    products = []

    # while True:
    while page < 10:
        url = f"{BASE_URL}{COLLECTION}?page={page}{SORT}"
        print(f"Scraping page {page} → {url}")

        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print("Page returned non-200, stopping.")
            break

        soup = BeautifulSoup(response.text, "lxml")

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

            products.append({
                "title": title,
                "url": product_url
            })

        page += 1
        time.sleep(1)

    return products


# --------- RUN SCRAPER ----------
all_products = scrape_collection()
print(f"\nTotal products scraped: {len(all_products)}")


# get brands
brands = load_brands()

matches = []

# check scraped products for brand matches
for product in all_products:
    product_title = f"{product.get('title', '')}"

    for brand_obj in brands:
        brand_name = brand_obj["brand"]

        if brand_matches(brand_name, product_title):
            matches.append({
                **product,
                "matched_brand": brand_name
            })
            break

# write matches to local file
with open("scraper-results.json", "w") as json_file:
    json.dump(matches, json_file, indent=4)