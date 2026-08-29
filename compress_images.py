"""
Batch-compresses every image in the images/ folder and writes the results
to images-compressed/ (your originals are never touched).

USAGE:
    1. pip install pillow
    2. Put this script in the same folder as your "images" folder
       (i.e. your PegasusWebsite project root).
    3. Run:  python compress_images.py
    4. Check images-compressed/ — if it looks good, rename your old
       "images" folder to "images-original" (keep as backup) and rename
       "images-compressed" to "images".

WHAT IT DOES:
    - Resizes any image wider than MAX_WIDTH down to MAX_WIDTH (keeps aspect ratio).
      Most of your images are shown well under 1600px on the page, so shrinking
      the source file has zero visible quality impact.
    - Re-compresses JPEGs at JPEG_QUALITY (85 = visually near-identical, much smaller).
    - Re-compresses PNGs with optimize=True (lossless, just strips redundant data).
    - Keeps transparency on PNGs that have it (e.g. your logo).
    - Keeps the exact same filenames and extensions, so you don't need to
      touch any HTML — just swap the folder.
"""

import shutil
from pathlib import Path
from PIL import Image

SOURCE_DIR = Path("images")
OUTPUT_DIR = Path("images-compressed")
MAX_WIDTH = 1600
JPEG_QUALITY = 85

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def compress_image(src_path: Path, dst_path: Path) -> bool:
    """Returns True if a compressed version was written, False if the
    original was kept as-is because compression didn't actually help."""
    tmp_path = dst_path.with_suffix(dst_path.suffix + ".tmp")

    with Image.open(src_path) as img:
        # Resize if wider than MAX_WIDTH
        if img.width > MAX_WIDTH:
            new_height = int(img.height * (MAX_WIDTH / img.width))
            img = img.resize((MAX_WIDTH, new_height), Image.LANCZOS)

        ext = src_path.suffix.lower()
        if ext in (".jpg", ".jpeg"):
            # Flatten transparency if any (JPEG doesn't support alpha)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(tmp_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
        elif ext == ".png":
            img.save(tmp_path, "PNG", optimize=True)
        else:
            img.save(tmp_path)

    # Only keep the compressed version if it's actually smaller.
    # Small/already-optimized images sometimes get bigger on re-encode --
    # in that case just use the original untouched.
    if tmp_path.stat().st_size < src_path.stat().st_size:
        tmp_path.replace(dst_path)
        return True
    else:
        tmp_path.unlink()
        shutil.copy2(src_path, dst_path)
        return False


def main():
    if not SOURCE_DIR.exists():
        print(f"Couldn't find '{SOURCE_DIR}' folder. Run this script from your project root.")
        return

    OUTPUT_DIR.mkdir(exist_ok=True)

    total_before = 0
    total_after = 0
    results = []

    for file in sorted(SOURCE_DIR.iterdir()):
        if file.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        dst = OUTPUT_DIR / file.name
        size_before = file.stat().st_size
        was_compressed = compress_image(file, dst)
        size_after = dst.stat().st_size

        total_before += size_before
        total_after += size_after
        results.append((file.name, size_before, size_after, was_compressed))

    print(f"{'File':<35}{'Before':>10}{'After':>10}{'Saved':>10}")
    print("-" * 65)
    for name, before, after, was_compressed in results:
        saved_pct = (1 - after / before) * 100 if before else 0
        note = "" if was_compressed else "  (kept original)"
        print(f"{name:<35}{before/1024:>9.0f}K{after/1024:>9.0f}K{saved_pct:>9.0f}%{note}")

    print("-" * 65)
    total_saved_pct = (1 - total_after / total_before) * 100 if total_before else 0
    print(f"TOTAL: {total_before/1024/1024:.1f}MB -> {total_after/1024/1024:.1f}MB "
          f"({total_saved_pct:.0f}% smaller)")
    print(f"\nDone. Review the images in '{OUTPUT_DIR}/', then swap the folder in when happy.")


if __name__ == "__main__":
    main()