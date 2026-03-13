import asyncio
import httpx
from bs4 import BeautifulSoup
import json
import re
from slugify import slugify
import os
import time

BASE_URL = "https://danang.coffee"
SEARCH_URL = f"{BASE_URL}/tim-kiem/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
DATA_FILE = "crawled_shops.json"
URL_FILE = "shop_urls.json"

async def get_shop_urls(client, page=1):
    url = f"{SEARCH_URL}?_paged={page}"
    print(f"🔍 Đang quét trang {page}...", flush=True)
    try:
        response = await client.get(url, timeout=30.0)
        if response.status_code != 200:
            print(f"⚠️ Trang {page} trả về status {response.status_code}", flush=True)
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.select(".jet-listing-dynamic-image__link")
        return list(set([link['href'] for link in links if link.has_attr('href')]))
    except Exception as e:
        print(f"❌ Lỗi khi quét trang {page}: {e}", flush=True)
        return []

def parse_district(address):
    if not address:
        return None
    districts = ["Hải Châu", "Thanh Khê", "Sơn Trà", "Ngũ Hành Sơn", "Liên Chiểu", "Cẩm Lệ", "Hòa Vang"]
    for d in districts:
        if d.lower() in address.lower():
            return d
    return None

async def crawl_shop_detail(client, url):
    print(f"☕ Đang lấy chi tiết: {url}", flush=True)
    try:
        response = await client.get(url, timeout=30.0)
        if response.status_code != 200:
            print(f"⚠️ {url} trả về status {response.status_code}", flush=True)
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        name_el = soup.select_one("h1.elementor-heading-title")
        name = name_el.get_text(strip=True) if name_el else ""
        
        if not name:
            print(f"⚠️ {url}: Không tìm thấy tên quán.", flush=True)
            return None

        # Address
        address_el = soup.select_one('a.jet-listing-dynamic-link__link[href*="maps.app.goo.gl"] span')
        address = address_el.get_text(strip=True) if address_el else ""
        
        # Phone
        phone_el = soup.select_one('a[href^="tel:"] span')
        phone = phone_el.get_text(strip=True) if phone_el else ""
        
        # Image
        thumb_el = soup.select_one('meta[property="og:image"]')
        image_url = thumb_el['content'] if thumb_el and thumb_el.has_attr('content') else ""

        # Tags
        tags = soup.select("a.jet-listing-dynamic-terms__link")
        purposes = []
        spaces = []
        amenities = []
        
        for tag in tags:
            href = tag.get('href', '')
            text = tag.get_text(strip=True)
            if '/muc-dich/' in href:
                purposes.append(text)
            elif '/khong-gian/' in href:
                spaces.append(text)
            elif '/tien-ich/' in href:
                amenities.append(text)

        return {
            "name": name,
            "slug": slugify(name),
            "address": address,
            "district": parse_district(address),
            "phone": phone,
            "image_url": image_url,
            "purposes": list(set(purposes)),
            "spaces": list(set(spaces)),
            "amenities": list(set(amenities)),
            "source_url": url
        }
    except Exception as e:
        print(f"❌ Lỗi khi crawl {url}: {e}", flush=True)
        return None

async def main():
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
        # Load or Find URLs
        if os.path.exists(URL_FILE):
            with open(URL_FILE, "r") as f:
                all_shop_urls = json.load(f)
            print(f"📂 Đã nạp {len(all_shop_urls)} URL từ cache.", flush=True)
        else:
            all_shop_urls = []
            page = 1
            seen_urls = set()
            while True:
                urls = await get_shop_urls(client, page)
                if not urls: break
                new_urls = [u for u in urls if u not in seen_urls]
                if not new_urls: break
                all_shop_urls.extend(new_urls)
                seen_urls.update(new_urls)
                page += 1
                await asyncio.sleep(0.5)
            with open(URL_FILE, "w") as f:
                json.dump(all_shop_urls, f)
            print(f"✅ Đã tìm thấy {len(all_shop_urls)} URL và lưu vào cache.", flush=True)

        # Load existing results
        results = []
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                results = json.load(f)
        
        crawled_urls = {r['source_url'] for r in results}
        urls_to_crawl = [u for u in all_shop_urls if u not in crawled_urls]
        
        print(f"🚀 Còn {len(urls_to_crawl)} quán cần lấy dữ liệu. Bắt đầu...", flush=True)
        
        for i, url in enumerate(urls_to_crawl):
            res = await crawl_shop_detail(client, url)
            if res:
                results.append(res)
                # Save checkpoint every 10 shops
                if len(results) % 10 == 0:
                    with open(DATA_FILE, "w", encoding="utf-8") as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                    print(f"💾 Checkpoint: {len(results)}/{len(all_shop_urls)}", flush=True)
            
            await asyncio.sleep(2) # VERY Polite delay
            
        # Final save
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"🏁 Hoàn tất! Đã lưu tổng cộng {len(results)} quán.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
