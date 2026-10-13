import os
import sys
import logging
from pathlib import Path
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = BASE_DIR / "data" / "raw"

DATASET_URLS = {
    "institutions.csv": "https://huggingface.co/datasets/Mahadih534/Institutional-Information-of-Bangladesh/resolve/main/data.csv",
    "hospitals.csv": "https://huggingface.co/datasets/Mahadih534/all-bangladeshi-hospitals/resolve/main/all-bangladesh-hosptals.csv",
    "restaurants.csv": "https://huggingface.co/datasets/Mahadih534/Bangladeshi-Restaurant-Data/resolve/main/restaurants.csv"
}

def download_file(url: str, destination: Path, chunk_size: int = 1024 * 1024) -> None:
    """Download a file with streaming chunks and logging."""
    if destination.exists() and destination.stat().st_size > 0:
        logger.info(f"File already exists: {destination} ({destination.stat().st_size / (1024*1024):.2f} MB), skipping download.")
        return

    logger.info(f"Downloading from {url} to {destination}...")
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    total_bytes = 0
    with open(destination, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
                total_bytes += len(chunk)

    logger.info(f"Successfully downloaded {destination.name} ({total_bytes / (1024*1024):.2f} MB)")

def download_all_datasets() -> None:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in DATASET_URLS.items():
        dest = RAW_DATA_DIR / filename
        download_file(url, dest)

if __name__ == "__main__":
    download_all_datasets()
