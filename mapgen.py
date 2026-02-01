import math
import os
import cv2
import numpy as np


class TileMapRenderer:
    TILE_SIZE = 256

    def __init__(self, tile_root: str):
        """
        tile_root: root directory of tiles (contains z/x/y.png)
        """
        self.tile_root = tile_root

    # --------------------------------------------------
    # TILE MATH
    # --------------------------------------------------

    @staticmethod
    def latlon_to_tile_fractional(lat, lon, zoom):
        lat = max(min(lat, 85.05112878), -85.05112878)
        n = 2 ** zoom

        x = (lon + 180.0) / 360.0 * n
        y = (
            1.0
            - math.log(
                math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))
            )
            / math.pi
        ) / 2.0 * n

        return x, y

    # --------------------------------------------------
    # TILE LOADING
    # --------------------------------------------------

    def _tile_path(self, z, x, y):
        return os.path.join(self.tile_root, str(z), str(x), f"{y}.png")

    def _load_tile(self, z, x, y):
        path = self._tile_path(z, x, y)
        if not os.path.exists(path):
            return None
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        return img

    # --------------------------------------------------
    # MAIN API
    # --------------------------------------------------

    def render(
        self,
        center_lat: float,
        center_lon: float,
        zoom: int,
        width: int,
        height: int,
    ) -> np.ndarray:
        """
        Returns a stitched image as a NumPy array (BGR, OpenCV format)
        """

        # Center position in global pixel space
        tile_x, tile_y = self.latlon_to_tile_fractional(
            center_lat, center_lon, zoom
        )

        center_px_x = tile_x * self.TILE_SIZE
        center_px_y = tile_y * self.TILE_SIZE

        half_w = width // 2
        half_h = height // 2

        # Global pixel bounds
        min_px_x = int(center_px_x - half_w)
        min_px_y = int(center_px_y - half_h)
        max_px_x = min_px_x + width
        max_px_y = min_px_y + height

        # Tile bounds
        tile_x_min = min_px_x // self.TILE_SIZE
        tile_y_min = min_px_y // self.TILE_SIZE
        tile_x_max = (max_px_x - 1) // self.TILE_SIZE
        tile_y_max = (max_px_y - 1) // self.TILE_SIZE

        tiles_w = tile_x_max - tile_x_min + 1
        tiles_h = tile_y_max - tile_y_min + 1

        # Create a canvas large enough for all tiles
        canvas = np.zeros(
            (tiles_h * self.TILE_SIZE, tiles_w * self.TILE_SIZE, 3),
            dtype=np.uint8,
        )

        # Load and place tiles
        for tx in range(tile_x_min, tile_x_max + 1):
            for ty in range(tile_y_min, tile_y_max + 1):
                tile = self._load_tile(zoom, tx, ty)
                if tile is None:
                    continue

                cx = (tx - tile_x_min) * self.TILE_SIZE
                cy = (ty - tile_y_min) * self.TILE_SIZE

                canvas[
                    cy : cy + self.TILE_SIZE,
                    cx : cx + self.TILE_SIZE,
                ] = tile

        # Crop to exact requested output
        crop_x = min_px_x - tile_x_min * self.TILE_SIZE
        crop_y = min_px_y - tile_y_min * self.TILE_SIZE

        result = canvas[
            crop_y : crop_y + height,
            crop_x : crop_x + width,
        ]

        return result



if __name__ == "__main__":
    renderer = TileMapRenderer(tile_root="tiles")

    img = renderer.render(
        center_lat=52.266862,
        center_lon=20.750421,
        zoom=17,
        width=200,
        height=200,
    )

    cv2.imwrite("output.png", img)
