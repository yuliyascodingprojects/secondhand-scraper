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

# pull in recently scraped urls 
def load_products(path="recent_products.json"):
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
        
recent_products = load_products()
   
# scrape each page of website in order
def scrape_collection():
    page = 1
    products = []

    # while True:
    while page < 5:
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

            #if any(prod.url == product_url for prod in recent_products):
            # if product_url in recent_products.values():
            #     break
            # for prod in recent_products:
            #     if prod["url"] == product_url:
            #         print("Recent match found")
            #         break

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

# write 20 most recent products to file
first_20_products = all_products[:20]
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