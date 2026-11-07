import os
import sys
import zipfile
import shutil
import random

DATASET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset"))

def setup():
    zip_candidates = [
        os.path.join(DATASET_ROOT, "observations.zip"),
        os.path.join(DATASET_ROOT, "dataset_temp.zip"),
    ]

    zip_file = None
    for z in zip_candidates:
        if os.path.exists(z) and os.path.getsize(z) > 1024 * 1024:
            try:
                with zipfile.ZipFile(z, 'r') as test_zf:
                    # Verify zip integrity
                    test_zf.testzip()
                zip_file = z
                print(f"[Setup] Valid zip found: {z} ({os.path.getsize(z) // (1024*1024)} MB)")
                break
            except Exception as e:
                print(f"[Setup] {z} is not ready or incomplete yet: {e}")

    if not zip_file:
        print("[Setup] No completed zip file found yet.")
        return False

    extract_path = os.path.join(DATASET_ROOT, "extracted_dataset")
    print(f"[Setup] Extracting {zip_file}...")
    with zipfile.ZipFile(zip_file, 'r') as zf:
        zf.extractall(extract_path)

    # Search for with_mask and without_mask directories
    with_mask_src = None
    without_mask_src = None

    for root, dirs, files in os.walk(extract_path):
        for d in dirs:
            low = d.lower()
            if "with_mask" in low and "without" not in low:
                with_mask_src = os.path.join(root, d)
            elif "without_mask" in low or "no_mask" in low:
                without_mask_src = os.path.join(root, d)

    if not with_mask_src or not without_mask_src:
        print(f"[Setup] Could not locate with_mask/without_mask in {extract_path}")
        return False

    print(f"[Setup] Found sources:\n - With Mask: {with_mask_src}\n - Without Mask: {without_mask_src}")

    for split in ["train", "val"]:
        os.makedirs(os.path.join(DATASET_ROOT, split, "Mask"), exist_ok=True)
        os.makedirs(os.path.join(DATASET_ROOT, split, "No Mask"), exist_ok=True)

    def distribute(src_dir, target_class, ratio=0.8):
        valid_exts = ('.jpg', '.jpeg', '.png', '.bmp')
        images = [f for f in os.listdir(src_dir) if f.lower().endswith(valid_exts)]
        random.seed(42)
        random.shuffle(images)
        split_point = int(len(images) * ratio)
        train_files = images[:split_point]
        val_files = images[split_point:]

        for img in train_files:
            shutil.copy2(os.path.join(src_dir, img), os.path.join(DATASET_ROOT, "train", target_class, img))
        for img in val_files:
            shutil.copy2(os.path.join(src_dir, img), os.path.join(DATASET_ROOT, "val", target_class, img))

        print(f"[Setup] {target_class}: {len(train_files)} train, {len(val_files)} val images.")

    distribute(with_mask_src, "Mask")
    distribute(without_mask_src, "No Mask")

    # Clean up extraction temp folder
    shutil.rmtree(extract_path, ignore_errors=True)
    for z in zip_candidates:
        if os.path.exists(z):
            try:
                os.remove(z)
            except Exception:
                pass

    print("[Setup] Dataset organized successfully into train/ and val/ folders!")
    return True

if __name__ == "__main__":
    success = setup()
    sys.exit(0 if success else 1)

