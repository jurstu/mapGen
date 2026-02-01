import math
import os
import requests
from tqdm import tqdm

# ----------------------------
# CONFIGURATION
# ----------------------------

TILE_URL = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
OUTPUT_DIR = "tiles"

MIN_LAT = 52.249531
MIN_LON = 20.749179
MAX_LAT = 52.271303
MAX_LON = 20.782088

MIN_ZOOM = 8
MAX_ZOOM = 18

HEADERS = {
    "User-Agent": "TileDownloader/1.0"
}

TIMEOUT = 10


# ----------------------------
# TILE MATH (Web Mercator)
# ----------------------------

def latlon_to_tile(lat, lon, zoom):
    lat = max(min(lat, 85.05112878), -85.05112878)
    n = 2 ** zoom

    x = int((lon + 180.0) / 360.0 * n)
    y = int(
        (1.0 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi)
        / 2.0
        * n
    )
    return x, y


# ----------------------------
# DOWNLOAD LOGIC
# ----------------------------

def download_tile(z, x, y):
    url = TILE_URL.format(z=z, x=x, y=y)
    path = os.path.join(OUTPUT_DIR, str(z), str(x))
    os.makedirs(path, exist_ok=True)

    filename = os.path.join(path, f"{y}.png")

    if os.path.exists(filename):
        return

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        with open(filename, "wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"Failed: z={z} x={x} y={y} ({e})")


def download_bbox():
    for z in range(MIN_ZOOM, MAX_ZOOM + 1):
        x_min, y_max = latlon_to_tile(MIN_LAT, MIN_LON, z)
        x_max, y_min = latlon_to_tile(MAX_LAT, MAX_LON, z)

        total = (x_max - x_min + 1) * (y_max - y_min + 1)
        print(f"Zoom {z}: {total} tiles")

        with tqdm(total=total) as pbar:
            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    download_tile(z, x, y)
                    pbar.update(1)


if __name__ == "__main__":
    download_bbox()
