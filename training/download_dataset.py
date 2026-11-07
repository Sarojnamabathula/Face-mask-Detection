import os
import sys
import zipfile
import shutil
import requests

DATASET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset"))

URLS = [
    ("Chandrika Deb Face Mask Dataset", "https://github.com/chandrikadeb7/Face-Mask-Detection/archive/refs/heads/master.zip"),
    ("Prajna Bhandary Face Mask Dataset", "https://github.com/prajnasb/observations/archive/refs/heads/master.zip")
]

def download_and_setup(target_dir=DATASET_ROOT):
    os.makedirs(target_dir, exist_ok=True)
    train_dir = os.path.join(target_dir, "train")
    val_dir = os.path.join(target_dir, "val")

    if os.path.exists(train_dir) and os.path.exists(val_dir):
        train_classes = [d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))]
        if len(train_classes) >= 2:
            print(f"[Dataset] Already configured at {target_dir} with classes: {train_classes}", flush=True)
            return True

    zip_path = os.path.join(target_dir, "dataset_temp.zip")
    extract_path = os.path.join(target_dir, "extracted_temp")

    downloaded = False
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    for name, url in URLS:
        print(f"[Dataset] Trying to download {name} from {url}...", flush=True)
        try:
            with requests.get(url, headers=headers, stream=True, timeout=60) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                print(f"[Dataset] Connected. Content length: {total_size} bytes. Downloading...", flush=True)
                downloaded_size = 0
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            if total_size > 0:
                                percent = (downloaded_size / total_size) * 100
                                print(f"[Dataset] Downloaded {downloaded_size // (1024*1024)} MB ({percent:.1f}%)", flush=True)
                            else:
                                print(f"[Dataset] Downloaded {downloaded_size // (1024*1024)} MB", flush=True)
            print("[Dataset] Download finished!", flush=True)
            downloaded = True
            break
        except Exception as e:
            print(f"[Dataset] Download error with {name}: {e}", flush=True)

    if not downloaded:
        print("[Dataset] Failed to download dataset.", flush=True)
        return False

    print("[Dataset] Extracting archive...", flush=True)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

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
        print(f"[Dataset] Could not find mask folders in {extract_path}", flush=True)
        return False

    for split in ["train", "val"]:
        os.makedirs(os.path.join(target_dir, split, "Mask"), exist_ok=True)
        os.makedirs(os.path.join(target_dir, split, "No Mask"), exist_ok=True)

    def distribute_images(src_folder, class_name, split_ratio=0.8):
        images = [f for f in os.listdir(src_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        import random
        random.seed(42)
        random.shuffle(images)
        split_idx = int(len(images) * split_ratio)
        train_imgs = images[:split_idx]
        val_imgs = images[split_idx:]

        for img in train_imgs:
            shutil.copy2(os.path.join(src_folder, img), os.path.join(target_dir, "train", class_name, img))
        for img in val_imgs:
            shutil.copy2(os.path.join(src_folder, img), os.path.join(target_dir, "val", class_name, img))

        print(f"[Dataset] Class '{class_name}': {len(train_imgs)} train, {len(val_imgs)} validation images.", flush=True)

    print("[Dataset] Organizing train and val sets...", flush=True)
    distribute_images(with_mask_src, "Mask")
    distribute_images(without_mask_src, "No Mask")

    if os.path.exists(zip_path):
        os.remove(zip_path)
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)

    print("[Dataset] Ready for training!", flush=True)
    return True

if __name__ == "__main__":
    success = download_and_setup()
    sys.exit(0 if success else 1)
