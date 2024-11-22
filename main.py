import requests
import re
import time
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
# from fake_useragent import UserAgent
# ua = UserAgent(browsers=['edge', 'chrome'])

response = requests.get('https://api64.ipify.org?format=json')
ip_address = response.json().get('ip')
print(f"Public IP Address: {ip_address}")

Project_ID = "1" #  change this

TELEGRAM_BOT_TOKENS = [
    "7306877915:AAHR-EDl87kj1eiLVWUxyiHnaQoiJUTW8Fc",
    "2117608874:AAHVEvOk16DF3CCS2bbHbVSXY8uJlB2eryo",
    "2112540740:AAHzSUURQwWW4yxEYtNHVsUTnnfwJstrb6A",
    "1630903119:AAG0brqW871aXKMKTQHVkvy4JXTbdj-Z2xI",
    "707274898:AAGT9BjrdHnq2t28qQJmG-3pYal6jAa1PZ0",
]
TELEGRAM_USER_ID = "567639577"
MAX_RETRIES = 5
NUM_WORKERS = 10

header = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) EdgiOS/120.0.2210.126 Version/17.0 Mobile/15E148 Safari/604.1'}

def active_game():
    while True:
        try:
            # sample
            # response = requests.get("https://my.abdee.ir/sample_active_treasure.json", headers=header)
            response = requests.get("https://api.digikala.com/v1/treasure-hunt/", headers=header)
            # بررسی وضعیت پاسخ
            if response.status_code == 200:
                data = response.json()
                try:
                    uri = data["data"]["active_treasure"]["treasure_map"]["products_url"]["uri"]
                except (KeyError, TypeError):
                    uri = None
                    
                if uri != "" and uri is not None:
                    match = re.search(r"category-([\w-]+)/", uri)
                    return match.group(1)
                else:
                    print("🔴 🔴 Active Game [Treasure] NOT FOUND!  🔴 🔴 ")
                    print("Retrying...") 
            else:
                print("🔴 🔴 Active Game [Treasure] NOT FOUND!  🔴 🔴 ")
                print("Retrying...")
        except requests.RequestException as e:
            print("🔴 🔴 Active Game [Treasure] NOT FOUND!  🔴 🔴 ")
            print("Retrying...")
        time.sleep(2)
Active_Game = active_game()
print(f"🟢🟢🟢 Active Treasure: {Active_Game} 🟢🟢🟢")
BASE_URL   = f"https://api.digikala.com/v1/categories/{Active_Game}/search/?page="
PRODUCT_URL_TEMPLATE = "https://api.digikala.com/v2/product/{}/"
Project_Range = requests.get(f"https://my.abdee.ir/?action=get_range&for={Project_ID}") #10-20
Project_Range = Project_Range.text.split("-")



if Project_Range == "" or not Project_Range[0].isnumeric():
    print(Project_Range)
    print("🔴 🔴 Project Range NOT FOUND!  🔴 🔴")
    sys.exit(1)


FROM = int(Project_Range[0])
TO   = int(Project_Range[1])

print(f"Form Page: {FROM}")
print(f"To Page:   {TO}")

start_time = time.time()

OCR_API_KEY = requests.get('https://my.abdee.ir/ocr_api_key.txt').text #"K85729529988957"

if OCR_API_KEY == "":
    print(OCR_API_KEY)
    print("🔴 🔴 OCR API KEY NOT FOUND!  🔴 🔴")
    sys.exit(1)
    
print(f"🟢🟢🟢 OCR_API_KEY: {OCR_API_KEY} 🟢🟢🟢")
OCR_API_URL = "https://api.ocr.space/parse/image"
OCR_header = {'apikey': OCR_API_KEY}


def extract_timestamp(url):
    match = re.search(r"_([0-9]+)\.jpg", url)
    if match:
        return int(match.group(1))
    return 0

def ocr(image_url):
    payload = {'language': 'ara','isOverlayRequired': 'false','url': image_url,'iscreatesearchablepdf': 'false','issearchablepdfhidetextlayer': 'false'}
    response = requests.request("POST", OCR_API_URL, headers=OCR_header, data=payload)
    while True:
        if response.status_code == 200:   
            try:
                data = response.json()['ParsedResults'][0]['ParsedText']
                return data
            except Exception as e:
                print(f"🔴 🔴 OCR FAILED for {image_url}  🔴 🔴")
                print(f"🔴 Retrying ... 🔴")
        else:
            print(f"🔴 🔴 OCR FAILED for {image_url}  🔴 🔴")
            print(f"🔴 Retrying ... 🔴")
        time.sleep(2)
            
def is_correct(string):
    return any(word in string for word in ['درست', 'همينه', 'حـالا', 'حالا', 'وارد', 'كن'])

def send_to_telegram(image_url, product_id, text):
    for TELEGRAM_BOT_TOKEN in TELEGRAM_BOT_TOKENS:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        data = {
            "chat_id": TELEGRAM_USER_ID,
            "photo": image_url,
            "caption": f"Product ID: {product_id}\n\n{text}",
            # "parse_mode": "MarkdownV2" 
        }
        try:
            response = requests.post(url, data=data)
            if response.status_code != 200:
                print(f"🔴 Error sending image to Telegram with token {TELEGRAM_BOT_TOKEN}: {response.text} 🔴")
            else:
                # print(f"✅ Image sent successfully with token {TELEGRAM_BOT_TOKEN}")
                break
        except Exception as e:
            print(f"🔴 Error sending image to Telegram with token {TELEGRAM_BOT_TOKEN}: {e} 🔴")

def process_images(product_data):
    if product_data.get("status") == 200:
        images = product_data.get("data", {}).get("product", {}).get("images", {}).get("list", [])
        image_urls = [img["url"][0] for img in images if "url" in img and img["url"]]
        return sorted(image_urls, key=extract_timestamp, reverse=True)
    return []

def fetch_product(product_id):
    url = PRODUCT_URL_TEMPLATE.format(product_id)
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            response = requests.get(url, headers=header)
            response.raise_for_status()
            product_data = response.json()
            sorted_images = process_images(product_data)
            if sorted_images:
                ocr_text = ocr(sorted_images[0])
                # ocr_text = ocr("https://dkstatics-public.digikala.com/digikala-products/319f22d08c9494efbc88a4756de3de3ded4d6f65_1731925489.jpg")
                # ocr_text = ocr("https://abdee.ir/right.jpg")
                if ocr_text != "" and is_correct(ocr_text):
                    send_to_telegram(sorted_images[0], product_id, ocr_text)
            return product_id, sorted_images
        except requests.RequestException as e:
            print(f"❌ Failed to get product {product_id}: {e}")
            time.sleep(1)
        attempt += 1
    return product_id, []

def fetch_page(page_num):
    url = f"{BASE_URL}{page_num}"
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            response = requests.get(url, headers=header)
            response.raise_for_status()
            page_data = response.json()
            if page_data.get("status") == 200:
                return page_data.get("data", {}).get("products", [])
        except requests.exceptions.HTTPError as e:
            print(f"⭕️ Failed Getting Page {page_num}: {e}")
            time.sleep(1)
        attempt += 1
    return []

# ذخیره محصولات یا صفحات ناموفق
failed_products = []
failed_pages = []

# پردازش صفحات و محصولات
all_product_ids = []
with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    future_to_page = {executor.submit(fetch_page, page_num): page_num for page_num in range(FROM, TO)}
    for future in as_completed(future_to_page):
        products = future.result()
        if products:
            all_product_ids.extend([product.get("id") for product in products if product.get("id")])
        else:
            page_num = future_to_page[future]
            failed_pages.append(page_num)

    future_to_product = {executor.submit(fetch_product, product_id): product_id for product_id in all_product_ids}
    for future in as_completed(future_to_product):
        product_id, images = future.result()
        if images:
            print(f"🟡 Product {product_id}: {len(images)} Images Done!")
        else:
            failed_products.append(product_id)

# دوباره بررسی صفحات و محصولات ناموفق
print(f"🟠 Retrying failed pages: {len(failed_pages)} items")
with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    for page_num in failed_pages:
        time.sleep(2)  # فاصله 2 ثانیه برای جلوگیری از سرریز شدن درخواست‌ها
        future = executor.submit(fetch_page, page_num)
        products = future.result()
        if products:
            all_product_ids.extend([product.get("id") for product in products if product.get("id")])

print(f"🟠 Retrying failed products: {len(failed_products)} items")
with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
    for product_id in failed_products:
        time.sleep(2)  # فاصله 2 ثانیه برای جلوگیری از سرریز شدن درخواست‌ها
        future = executor.submit(fetch_product, product_id)
        future.result()

print(f"🟢🟢🟢 ALL DONE: {len(all_product_ids)} 🟢🟢🟢")
end_time = time.time()

# Calculate time taken
time_taken = end_time - start_time

print("Time taken:", time_taken, "seconds")
