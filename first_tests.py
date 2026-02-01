"""Example: read GeoTIFF path from `geotiff_location`, print its corner coords,
and expose lon/lat <-> XYZ tile conversion helpers."""

import math
from pathlib import Path
from typing import Dict, Tuple

try:
    import rasterio
    from rasterio.warp import transform_bounds
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("rasterio is required to run this script") from exc

# --- File path helper ------------------------------------------------------ #


def read_geotiff_path() -> Path:
    """Read the GeoTIFF path from the sibling text file and return it as Path."""

    location_file = Path(__file__).with_name("geotiff_location")
    raw_path = location_file.read_text(encoding="utf-8").strip()
    if not raw_path:
        raise ValueError(f"{location_file} is empty; expected a GeoTIFF path")
    return Path(raw_path).expanduser()


# --- Tile conversion helpers ---------------------------------------------- #


def lonlat_to_tile_numbers(lon_deg: float, lat_deg: float, zoom: int) -> Tuple[float, float]:
    """
    Convert lon/lat (degrees) to fractional XYZ tile numbers at a given zoom.

    Returns (xtile, ytile) as floats (not floored to integers).
    """

    # Clamp latitude to Mercator valid range
    lat_deg = max(min(lat_deg, 85.05112877980659), -85.05112877980659)
    n = 2**zoom
    lat_rad = math.radians(lat_deg)
    xtile = n * ((lon_deg + 180.0) / 360.0)
    ytile = n * (1 - (math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi)) / 2
    return xtile, ytile


def tile_numbers_to_lonlat(xtile: float, ytile: float, zoom: int) -> Tuple[float, float]:
    """
    Convert fractional XYZ tile numbers back to lon/lat (degrees).
    """

    n = 2**zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return lon_deg, lat_deg


# --- GeoTIFF corner reader ------------------------------------------------- #


def geotiff_corners_wgs84(dataset: rasterio.io.DatasetReader) -> Dict[str, Tuple[float, float]]:
    """
    Return corner coordinates of the dataset in WGS84 as {name: (lat, lon)}.
    Names: top_left, top_right, bottom_left, bottom_right.
    """

    left, bottom, right, top = dataset.bounds
    lon_min, lat_min, lon_max, lat_max = transform_bounds(dataset.crs, "EPSG:4326", left, bottom, right, top, densify_pts=21)
    return {
        "top_left": (lat_max, lon_min),
        "top_right": (lat_max, lon_max),
        "bottom_left": (lat_min, lon_min),
        "bottom_right": (lat_min, lon_max),
    }


# --- Demo ------------------------------------------------------------------ #


def main():
    geotiff_path = read_geotiff_path()
    with rasterio.open(geotiff_path) as ds:
        corners = geotiff_corners_wgs84(ds)
        print("Corner coordinates (lat,lon):")
        for name in ("top_left", "top_right", "bottom_left", "bottom_right"):
            lat, lon = corners[name]
            print(f"{name}: {lat:.6f},{lon:.6f}")

        # Example: convert top-left corner to tile numbers at zoom 12 and back.
        lat, lon = corners["top_left"]
        xtile, ytile = lonlat_to_tile_numbers(lon, lat, zoom=12)

        int_x, int_y = int(xtile), int(ytile)
        for i in range(10):
            pass

        



        lon_back, lat_back = tile_numbers_to_lonlat(xtile, ytile, zoom=12)
        print("\nExample conversion @ zoom 12:")
        print(f"  top_left -> tile numbers: xtile={xtile:.4f}, ytile={ytile:.4f}")
        print(f"  back to lon/lat: lon={lon_back:.6f}, lat={lat_back:.6f}")


if __name__ == "__main__":
    main()
