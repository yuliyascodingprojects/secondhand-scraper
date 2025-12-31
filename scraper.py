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
RECENTS = 30

# pull brands from external file
def load_brands(path="brands.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# pull in recently scraped urls 
def load_products(path="recent_products.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# load recently scraped urls into set 
def load_scraped_urls(path="recent_products.json"):
    try: 
        with open(path, "r", encoding="utf-8") as f:
            items = json.load(f)
            return {item["url"] for item in items}
    except FileNotFoundError:
        return set()

# strip text down to lowercase letters 
def normalize(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text.lower()

# safely checks for match in brand names
def brand_matches(brand, text):
    return normalize(brand) == normalize(text)

# strip out brand name from the title
def get_brand_from_title(title):
    case1 = re.search(r"By(.*?)In", title)
    case2 = re.search(r"By(.*?), Size", title)
    case3 = re.search(r"(?<=By\s).*", title)

    if case1:
        extracted_match = case1.group(1).strip()
        return extracted_match
    elif case2:
        extracted_match = case2.group(1).strip()
        return extracted_match
    elif case3:
        extracted_match = case3.group(0)
        return extracted_match
    else:
        return None

# load in already scraped urls
scraped_urls = load_scraped_urls()
   
# scrape each page of website in order
def scrape_collection():
    page = 1
    products = []

    # while True:
    while page < 4:
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

            if product_url in scraped_urls:
                print("stopping early")
                return products

            title = link.get("title") or link.text.strip()

            products.append({
                "title": title,
                "url": product_url,
                "brand": get_brand_from_title(title)
            })

        page += 1
        time.sleep(1)

    return products


# --------- RUN SCRAPER ----------
all_products = scrape_collection()
print(f"\nTotal products scraped: {len(all_products)}")

# write newly scraped products to recent products file 
# if < 30 recent products, make up difference with previous recent products
if len(all_products) >= RECENTS:
    first_20_products = all_products[:RECENTS]
    with open("recent_products.json", "w") as json_file:
        json.dump(first_20_products, json_file, indent=4)
else:
    recent_products = load_products()
    first_20_products = all_products
    i = 0
    difference = RECENTS - len(first_20_products)

    while i < difference:
        first_20_products.append(recent_products[i])
        i+=1
    with open("recent_products.json", "w") as json_file:
        json.dump(first_20_products, json_file, indent=4)        

# get brands
brands = load_brands()

matches = []

# check scraped products for brand matches
for product in all_products:
    product_brand = f"{product.get('brand', '')}"

    for brand_obj in brands:
        brand_name = brand_obj["brand"]

        if brand_matches(brand_name, product_brand):
            matches.append({
                **product,
                "matched_brand": brand_name
            })
            break

# write matches to local file
with open("scraper-results.json", "w") as json_file:
    json.dump(matches, json_file, indent=4)