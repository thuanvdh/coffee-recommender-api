import os
import sys
import subprocess
from pathlib import Path

# Ensure Pillow is installed
try:
    from PIL import Image
except ImportError:
    print("Pillow is not installed. Installing Pillow...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

def convert_images_to_webp(target_dir):
    path = Path(target_dir)
    if not path.exists():
        print(f"Error: Target directory {target_dir} does not exist.")
        return

    print(f"Scanning directory: {path.resolve()}")
    
    # Supported image extensions for conversion
    extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    success_count = 0
    fail_count = 0
    skipped_count = 0

    for file_path in path.glob('**/*'):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            webp_path = file_path.with_suffix('.webp')
            
            # If the webp file already exists, we skip conversion unless we want to overwrite
            if webp_path.exists():
                # Just delete the original file since webp is already present
                try:
                    file_path.unlink()
                    skipped_count += 1
                except Exception as e:
                    print(f"Failed to delete duplicate original {file_path}: {e}")
                continue
                
            try:
                # Open image and convert
                with Image.open(file_path) as img:
                    # Convert palette images or RGBA to RGB/RGBA as appropriate
                    # WebP supports transparency, so RGBA can be kept.
                    img.save(webp_path, format='webp', quality=80)
                
                # Delete original file
                file_path.unlink()
                success_count += 1
                if success_count % 100 == 0:
                    print(f"Converted {success_count} images...")
            except Exception as e:
                print(f"Failed to convert {file_path}: {e}")
                fail_count += 1

    print("\nConversion Completed!")
    print(f"Successfully converted: {success_count} images")
    print(f"Skipped/Cleaned duplicate originals: {skipped_count} images")
    print(f"Failed to convert: {fail_count} images")

if __name__ == "__main__":
    target_directory = "danang_coffee_images"
    convert_images_to_webp(target_directory)
