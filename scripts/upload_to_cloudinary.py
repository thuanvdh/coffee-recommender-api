import asyncio
import os
import sys
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

async def process_shop(session: AsyncSession, shop_dir: Path):
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
        else:
            print("   Cover image already on Cloudinary. Skipping...")
            
    # 2. Upload Gallery Images (space, drinks, menu)
    categories = ["space", "drinks", "menu"]
    
    # Clear existing gallery images first if desired, or skip duplicates.
    # To keep it safe, let's query existing image URLs for this shop.
    img_stmt = select(ShopImage).where(ShopImage.shop_id == shop.id)
    img_result = await session.execute(img_stmt)
    existing_urls = {img.url for img in img_result.scalars().all()}
    
    for category in categories:
        category_dir = shop_dir / "images" / category
        if category_dir.exists():
            for i, img_path in enumerate(category_dir.glob("*.webp")):
                # Generate unique public ID
                public_id = f"{slug}_{category}_{i+1}"
                
                # Check if this public ID URL already exists in DB
                # Simple heuristical check
                already_uploaded = False
                for url in existing_urls:
                    if public_id in url:
                        already_uploaded = True
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

    # Commit progress for this shop
    await session.commit()

async def main():
    if not OUTPUT_DIR.exists():
        print(f"❌ Error: {OUTPUT_DIR} directory not found.")
        return
        
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with session_factory() as session:
        shop_dirs = [d for d in OUTPUT_DIR.iterdir() if d.is_dir()]
        print(f"Found {len(shop_dirs)} shop directories to process.")
        
        for i, shop_dir in enumerate(shop_dirs):
            print(f"\n[{i+1}/{len(shop_dirs)}] ----------------------------------------")
            try:
                await process_shop(session, shop_dir)
            except Exception as e:
                print(f"❌ Error processing shop {shop_dir.name}: {e}")
                await session.rollback()
                
    await engine.dispose()
    print("\n🏁 Done! All images processed and uploaded to Cloudinary.")

if __name__ == "__main__":
    asyncio.run(main())
