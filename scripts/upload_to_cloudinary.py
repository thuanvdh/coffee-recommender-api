import asyncio
import os
import sys
import json
import subprocess
from pathlib import Path

# Ensure Cloudinary SDK is installed
try:
    import cloudinary
    import cloudinary.uploader
except ImportError:
    print("Cloudinary package is not installed. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cloudinary"])
    import cloudinary
    import cloudinary.uploader

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# App imports - assuming this runs from the API root
sys.path.append(str(Path(__file__).parent.parent))
from app.config import settings
from app.models import CoffeeShop, ShopImage

# Configure Cloudinary
# Cloudinary looks for CLOUDINARY_URL in environment or can be configured manually:
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if not (CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET):
    print("❌ Error: Cloudinary credentials not found in environment!")
    print("Please add CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to your .env file.")
    sys.exit(1)

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

OUTPUT_DIR = Path("danang_coffee_images")

async def upload_image_to_cloudinary(file_path: Path, public_id: str):
    """Uploads file to Cloudinary in a separate thread to prevent blocking."""
    try:
        response = await asyncio.to_thread(
            cloudinary.uploader.upload,
            str(file_path),
            public_id=public_id,
            folder="danang_coffee"
        )
        return response.get("secure_url")
    except Exception as e:
        print(f"   Failed to upload {file_path.name} to Cloudinary: {e}")
        return None

SLUG_MAP = {
    "meet%ef%bc%8b-coffee-%ef%bc%86-tea": "meet-coffee-tea",
    "a-room-for-lost-things": "a-room-for-lost-things-slow-bar-coffee",
    "di-ca-phe-bui-ky": "di-ca-phe-1",
    "caribou-food-truck": "caribou-food-truck-bien-my-an",
    "ca-cafe": "ca-cafe-find-your-flow",
    "nozza-cafe": "noz-za-cafe",
    "phe-coffee": "phe-coffee-nguyen-ba-hoc",
    "mien-space": "mie-n-space",
    "las-cafe": "la-s-cafe",
    "ca-noc-cafe": "ca-noc-cafe-nguyen-hoang",
    "sime-cafe": "si-me-cafe",
    "phe-coffee-the-garden": "phe-coffee-the-garden-tran-bach-dang",
    "1710-cafe-society": "1710-cafe-and-society",
    "the-hideout-cafe": "the-hideout-cafe-do-ba"
}

async def process_shop(session: AsyncSession, shop_dir: Path, crawled_data: list):
    folder_name = shop_dir.name
    slug = SLUG_MAP.get(folder_name, folder_name)

    # Query shop by slug
    stmt = select(CoffeeShop).where(CoffeeShop.slug == slug)
    result = await session.execute(stmt)
    shop = result.scalar_one_or_none()
    
    if not shop:
        print(f"⚠️ Shop with slug '{slug}' not found in database. Skipping...")
        return
        
    print(f"☕ Processing shop: {shop.name} ({slug})")
    
    # Find matching shop in crawled_shops.json
    matched_json_shop = None
    for js in crawled_data:
        if js.get("slug") == slug:
            matched_json_shop = js
            break

    # 1. Upload Cover Image
    cover_path = shop_dir / "images" / "cover" / "cover.webp"
    if cover_path.exists():
        # Check if already uploaded (to avoid duplicate upload calls)
        if not shop.image_url or "cloudinary.com" not in shop.image_url:
            print("   Uploading cover image...")
            secure_url = await upload_image_to_cloudinary(cover_path, f"{slug}_cover")
            if secure_url:
                shop.image_url = secure_url
                print(f"   Cover URL updated: {secure_url}")
                if matched_json_shop:
                    matched_json_shop["image_url"] = secure_url
        else:
            print("   Cover image already on Cloudinary. Skipping...")
            if matched_json_shop and "cloudinary.com" in shop.image_url:
                matched_json_shop["image_url"] = shop.image_url
            
    # 2. Upload Gallery Images (space, drinks, menu)
    categories = ["space", "drinks", "menu"]
    
    # Query existing image URLs for this shop
    img_stmt = select(ShopImage).where(ShopImage.shop_id == shop.id)
    img_result = await session.execute(img_stmt)
    existing_urls = {img.url for img in img_result.scalars().all()}
    
    gallery_images_list = []
    
    for category in categories:
        category_dir = shop_dir / "images" / category
        if category_dir.exists():
            for i, img_path in enumerate(category_dir.glob("*.webp")):
                # Generate unique public ID
                public_id = f"{slug}_{category}_{i+1}"
                
                # Check if this public ID URL already exists in DB
                already_uploaded = False
                secure_url = None
                for url in existing_urls:
                    if public_id in url:
                        already_uploaded = True
                        secure_url = url
                        break
                        
                if not already_uploaded:
                    print(f"   Uploading gallery image: {img_path.name}...")
                    secure_url = await upload_image_to_cloudinary(img_path, public_id)
                    if secure_url:
                        # Save to database
                        new_img = ShopImage(
                            shop_id=shop.id,
                            url=secure_url,
                            alt_text=f"{shop.name} - {category} {i+1}"
                        )
                        session.add(new_img)
                        print(f"   Added to DB gallery: {secure_url}")
                else:
                    print(f"   Gallery image {img_path.name} already uploaded. Skipping...")
                
                if secure_url:
                    gallery_images_list.append({
                        "url": secure_url,
                        "alt_text": f"{shop.name} - {category} {i+1}"
                    })

    if matched_json_shop and gallery_images_list:
        matched_json_shop["gallery_images"] = gallery_images_list

    # Commit progress for this shop
    await session.commit()

async def main():
    if not OUTPUT_DIR.exists():
        print(f"❌ Error: {OUTPUT_DIR} directory not found.")
        return
        
    crawled_shops_path = Path("crawled_shops.json")
    crawled_data = []
    if crawled_shops_path.exists():
        try:
            with open(crawled_shops_path, "r", encoding="utf-8") as f:
                crawled_data = json.load(f)
            print(f"Loaded {len(crawled_data)} entries from crawled_shops.json")
        except Exception as e:
            print(f"⚠️ Error loading crawled_shops.json: {e}")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    shop_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
    print(f"Found {len(shop_dirs)} shop directories to process.")
    
    sem = asyncio.Semaphore(15)
    file_lock = asyncio.Lock()
    
    async def worker(shop_dir: Path, idx: int, total: int):
        async with sem:
            async with session_factory() as session:
                try:
                    await process_shop(session, shop_dir, crawled_data)
                    async with file_lock:
                        if crawled_shops_path.exists() or len(crawled_data) > 0:
                            with open(crawled_shops_path, "w", encoding="utf-8") as f:
                                json.dump(crawled_data, f, ensure_ascii=False, indent=2)
                    print(f"✅ [{idx+1}/{total}] Finished processing {shop_dir.name}")
                except Exception as e:
                    print(f"❌ [{idx+1}/{total}] Error processing shop {shop_dir.name}: {e}")
                    await session.rollback()

    tasks = [worker(shop_dir, i, len(shop_dirs)) for i, shop_dir in enumerate(shop_dirs)]
    await asyncio.gather(*tasks)
                
    await engine.dispose()
    print("\n🏁 Done! All images processed and uploaded to Cloudinary.")

if __name__ == "__main__":
    asyncio.run(main())
