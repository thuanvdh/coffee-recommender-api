import asyncio
import httpx
from bs4 import BeautifulSoup
import os
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image
from io import BytesIO

# Configuration
BASE_URL = "https://danang.coffee"
SITEMAPS = [
    "https://danang.coffee/location-sitemap1.xml",
    "https://danang.coffee/location-sitemap2.xml"
]
OUTPUT_DIR = Path("danang_coffee_images")
CHECKPOINT_FILE = OUTPUT_DIR / "checkpoint.json"
CONCURRENT_SHOPS = 3  # Keep it low to avoid IP ban
CONCURRENT_DOWNLOADS = 10
TIMEOUT = 30.0

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.31",
    "Referer": "https://danang.coffee/"
}

# Selectors from research
TAB_IDS = {
    "space": "364380241",
    "drinks": "364380242",
    "menu": "364380243"
}

async def fetch_shop_urls():
    urls = []
    print("Discovering shop URLs from sitemaps...")
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT) as client:
        for sitemap_url in SITEMAPS:
            try:
                resp = await client.get(sitemap_url)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    # Sitemap namespace is usually http://www.sitemaps.org/schemas/sitemap/0.9
                    for url_node in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                        urls.append(url_node.text)
            except Exception as e:
                print(f"Error fetching sitemap {sitemap_url}: {e}")
    print(f"Found {len(urls)} shops.")
    return urls

def get_slug(url):
    return url.strip("/").split("/")[-1]

async def download_image(client, url, target_path):
    # Enforce .webp extension
    target_path = target_path.with_suffix('.webp')
    
    if target_path.exists():
        return True
    
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        resp = await client.get(url)
        if resp.status_code == 200:
            img_data = BytesIO(resp.content)
            with Image.open(img_data) as img:
                img.save(target_path, format="webp", quality=80)
            return True
        else:
            print(f"Failed to download {url}: Status {resp.status_code}")
    except Exception as e:
        print(f"Error downloading/converting {url}: {e}")
    return False

async def process_shop(client, shop_url, index, total):
    slug = get_slug(shop_url)
    shop_dir = OUTPUT_DIR / slug / "images"
    print(f"[{index+1}/{total}] Processing shop: {slug}")
    
    try:
        resp = await client.get(shop_url)
        if resp.status_code != 200:
            print(f"   Failed to fetch shop page {shop_url}: Status {resp.status_code}")
            return False
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 1. Cover Image
        image_tasks = []
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            cover_url = og_image["content"]
            ext = cover_url.split(".")[-1].split("?")[0] or "jpg"
            image_tasks.append(download_image(client, cover_url, shop_dir / "cover" / f"cover.{ext}"))
            
        # 2. Robust Tab Detection
        # Find all tab titles
        tab_titles = soup.find_all("button", class_="e-n-tab-title")
        if not tab_titles:
            # Fallback for older Elementor versions if any
            tab_titles = soup.find_all("div", class_="elementor-tab-title")
            
        category_map = {
            "không gian": "space",
            "đồ uống": "drinks",
            "menu": "menu",
            "thực đơn": "menu"
        }
        
        found_tabs = {}
        for title in tab_titles:
            title_text = title.get_text(strip=True).lower()
            for key, cat in category_map.items():
                if key in title_text:
                    # Found a matching title, now find its content div
                    content_id = title.get("aria-controls") or title.get("id", "").replace("title", "content")
                    if content_id:
                        content_div = soup.find(id=content_id)
                        if content_div:
                            found_tabs[cat] = content_div
                    break
        
        # Fallback: if no titles found, look for content divs directly by ID patterns
        if not found_tabs:
            for cat, suffix in {"space": "0241", "drinks": "0242", "menu": "0243"}.items():
                content_div = soup.find("div", id=re.compile(f"e-n-tab-content-.*{suffix}"))
                if content_div:
                    found_tabs[cat] = content_div

        for category, content_div in found_tabs.items():
            # Find all gallery item links which usually point to high-res images
            links = content_div.find_all("a", class_="e-gallery-item")
            if not links:
                # Fallback to images inside
                links = content_div.find_all("img")
                
            for i, link in enumerate(links):
                img_url = link.get("href") or link.get("src") or link.get("data-src")
                if img_url and any(ext in img_url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    ext = img_url.split(".")[-1].split("?")[0]
                    if len(ext) > 4: ext = "jpg" # cleanup complex URLs
                    filename = f"{category}_{i+1}.{ext}"
                    image_tasks.append(download_image(client, img_url, shop_dir / category / filename))
        
        if image_tasks:
            results = await asyncio.gather(*image_tasks)
            print(f"   Done: {sum(results)} images downloaded for {slug}")
        else:
            print(f"   No images found for {slug}")
            
        return True
    except Exception as e:
        print(f"   Error processing shop {slug}: {e}")
        return False

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load checkpoint
    processed_urls = set()
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r") as f:
            processed_urls = set(json.load(f))
    
    shop_urls = await fetch_shop_urls()
    
    # Filter out already processed
    to_process = [url for url in shop_urls if url not in processed_urls]
    print(f"Found {len(to_process)} shops to process (Total {len(shop_urls)}, Skipped {len(processed_urls)})")
    
    async with httpx.AsyncClient(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        # Process in chunks of CONCURRENT_SHOPS
        for i in range(0, len(to_process), CONCURRENT_SHOPS):
            batch = to_process[i:i+CONCURRENT_SHOPS]
            tasks = [process_shop(client, url, i+j, len(to_process)) for j, url in enumerate(batch)]
            await asyncio.gather(*tasks)
            
            # Save checkpoint after each batch
            processed_urls.update(batch)
            with open(CHECKPOINT_FILE, "w") as f:
                json.dump(list(processed_urls), f)
            
            # Small delay to be polite
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
