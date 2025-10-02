
#!/usr/bin/env python3
"""
Download Phoenix aerial imagery pixels via ArcGIS ImageServer exportImage and save as Cloud Optimized GeoTIFF (COG).

Features
--------
- Accepts an AOI bounding box (WGS84 lon/lat) OR a CSV of points (lon,lat[,id,name]) with a buffer distance.
- Transforms bbox/points to the service CRS (auto-detected from the ImageServer).
- Requests imagery at *native* pixel resolution by deriving size from bbox + service pixel size
  (or you can override with --pixel-size).
- Automatically tiles requests if the server's maxImageWidth/Height would be exceeded, then mosaics tiles.
- Writes a proper COG using GDAL's COG driver.

Dependencies
------------
- Python: requests, shapely, pyproj
- GDAL (for Python): osgeo.gdal, osgeo.osr  (install via conda-forge recommended)

Install (conda recommended):
    conda create -n phoenix-cog python=3.11 -y
    conda activate phoenix-cog
    conda install -c conda-forge gdal shapely pyproj requests -y

CLI examples
------------
BBOX mode (lon/lat in WGS84):
    python phoenix_imagery_to_cog.py bbox \
      --service "https://utility.arcgis.com/usrsvcs/servers/0e7011b550e94ab99bc351a633d24952/rest/services/Aerials/Aerials/ImageServer" \
      --bbox -112.075 33.445 -112.065 33.455 \
      --out phoenix_school_aoi_cog.tif

CSV-of-points mode (buffers each point and exports one COG per row):
    python phoenix_imagery_to_cog.py csv \
      --service "https://utility.arcgis.com/usrsvcs/servers/0e7011b550e94ab99bc351a633d24952/rest/services/Aerials/Aerials/ImageServer" \
      --csv schools.csv \
      --buffer 150 \
      --buffer-unit meters \
      --out-dir ./cogs

CSV format:
    school_id,name,lon,lat
    101,Lincoln HS,-112.072,33.4501
    102,Roosevelt ES,-112.068,33.4482

Notes
-----
- If the service reports pixel size, we use it. If not, we fall back to 4-inch (0.333333 ft) default for metro.
  You can override with --pixel-size if needed (e.g., 0.75 for 9-inch areas).
- We preserve pixels with nearest-neighbor export and avoid reprojection by using the native service CRS for export.
- Respect the City's Terms of Use on the item page.

References
----------
- ArcGIS Image Service and `exportImage` (bbox, size, format, CRS) docs:
  https://developers.arcgis.com/rest/services-reference/enterprise/export-image/  (Esri)  [accessed Oct 2025]
- COG creation with GDAL COG driver:
  https://gdal.org/en/stable/drivers/raster/cog.html  (GDAL)  [accessed Oct 2025]
- Phoenix Aerials item (coverage, resolution, SR 2868):
  https://phoenix.maps.arcgis.com/home/item.html?id=0e7011b550e94ab99bc351a633d24952  [accessed Oct 2025]
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import pathlib
import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import requests
from shapely.geometry import box, Point
from shapely.ops import transform as shp_transform
from pyproj import Transformer, CRS

# GDAL bindings
from osgeo import gdal


# -------- Helper dataclasses --------

@dataclass
class ServiceInfo:
    url: str
    wkid: int
    max_w: int
    max_h: int
    pixel_size_x: Optional[float]  # service units per pixel (x)
    pixel_size_y: Optional[float]  # service units per pixel (y)
    units_name: str


# -------- REST helpers --------

def _get_json(url: str, params: dict) -> dict:
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def fetch_service_info(service_url: str) -> ServiceInfo:
    """
    Read service metadata and try to infer CRS, max image size, and pixel size.
    """
    info = _get_json(service_url, {"f": "pjson"})
    sr = info.get("spatialReference", {})
    wkid = sr.get("latestWkid") or sr.get("wkid")
    if wkid is None:
        raise RuntimeError("Could not resolve service WKID from spatialReference")

    max_w = int(info.get("maxImageWidth", 10000))
    max_h = int(info.get("maxImageHeight", 10000))

    # Try to find pixel size from service or keyProperties
    px_x = None
    px_y = None
    try:
        kp = _get_json(f"{service_url}/keyProperties", {"f": "pjson"})
    except Exception:
        kp = {}
    # Common key names (varies by publisher)
    for k in ["Pixel Size X", "PixelSizeX", "pixelSizeX", "pixelSizex", "pixelSize"]:
        if k in kp:
            try:
                px_x = float(str(kp[k]))
            except Exception:
                pass
    for k in ["Pixel Size Y", "PixelSizeY", "pixelSizeY", "pixelSizey"]:
        if k in kp:
            try:
                px_y = float(str(kp[k]))
            except Exception:
                pass

    # Service units (feet in State Plane 2868)
    try:
        units_name = CRS.from_epsg(int(wkid)).axis_info[0].unit_name or "unknown"
    except Exception:
        units_name = "unknown"

    return ServiceInfo(
        url=service_url,
        wkid=int(wkid),
        max_w=max_w,
        max_h=max_h,
        pixel_size_x=px_x,
        pixel_size_y=px_y,
        units_name=units_name
    )


# -------- Geometry + tiling helpers --------

def transform_bbox_wgs84_to_service(bbox_w84: Tuple[float, float, float, float], wkid: int) -> Tuple[float, float, float, float]:
    tr = Transformer.from_crs(4326, wkid, always_xy=True)
    x1, y1 = tr.transform(bbox_w84[0], bbox_w84[1])
    x2, y2 = tr.transform(bbox_w84[2], bbox_w84[3])
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def clip_bbox_to_service_extent(bbox_native: Tuple[float, float, float, float], service_url: str) -> Tuple[float, float, float, float]:
    info = _get_json(service_url, {"f": "pjson"})
    ext = info.get("extent")
    if not ext:
        return bbox_native
    service_extent = (ext["xmin"], ext["ymin"], ext["xmax"], ext["ymax"])
    inter = box(*bbox_native).intersection(box(*service_extent))
    if inter.is_empty:
        raise ValueError("Requested bbox is outside the service extent.")
    return inter.bounds


def compute_size_from_bbox_and_pixels(
    bbox_native: Tuple[float, float, float, float],
    pix_x: float,
    pix_y: float
) -> Tuple[int, int]:
    x1, y1, x2, y2 = bbox_native
    w = max(1e-9, x2 - x1)
    h = max(1e-9, y2 - y1)
    width = max(1, int(round(w / float(pix_x))))
    height = max(1, int(round(h / float(pix_y))))
    return width, height


def tile_counts(width: int, height: int, max_w: int, max_h: int) -> Tuple[int, int]:
    nx = math.ceil(width / max_w) if width > max_w else 1
    ny = math.ceil(height / max_h) if height > max_h else 1
    return nx, ny


def subdivide_bbox(bbox_native: Tuple[float, float, float, float], nx: int, ny: int) -> List[Tuple[float, float, float, float]]:
    x1, y1, x2, y2 = bbox_native
    dx = (x2 - x1) / nx
    dy = (y2 - y1) / ny
    tiles = []
    for iy in range(ny):
        for ix in range(nx):
            tiles.append((x1 + ix * dx, y1 + iy * dy, x1 + (ix + 1) * dx, y1 + (iy + 1) * dy))
    return tiles


def meters_to_service_units(meters: float, wkid: int) -> float:
    """
    Convert meters to service linear units by projecting (0,0) -> (1m,0) and measuring.
    """
    tr = Transformer.from_crs(3857, wkid, always_xy=True)  # using metric CRS as source scale helper
    # 1 meter in EPSG:3857 is not strictly "1", so do a true geodesic-based trick:
    # Better: transform geog WGS84  (lon=0, lat=0) and a point offset by 1m along X in a projected CRS.
    # Simpler robust approach: use pyproj's 'to_meter' via CRS if defined:
    try:
        target = CRS.from_epsg(wkid)
        to_meter = target.to_meter  # meters per target unit (e.g., 0.3048 for US feet)
        if to_meter and to_meter > 0:
            return meters / to_meter
    except Exception:
        pass
    # Fallback: assume feet if state plane
    return meters / 0.3048


# -------- Export + mosaic + COG --------

def export_image(
    service: ServiceInfo,
    bbox_native: Tuple[float, float, float, float],
    size: Tuple[int, int],
    out_path: pathlib.Path,
    token: Optional[str] = None
) -> pathlib.Path:
    params = {
        "f": "image",  # stream image bytes
        "bbox": ",".join(map(str, bbox_native)),
        "bboxSR": str(service.wkid),
        "imageSR": str(service.wkid),   # keep native CRS; no reprojection
        "size": f"{size[0]},{size[1]}",
        "format": "tiff",
        "interpolation": "RSP_NearestNeighbor"
    }
    if token:
        params["token"] = token
    r = requests.get(f"{service.url}/exportImage", params=params, timeout=180, allow_redirects=True)
    r.raise_for_status()
    out_path.write_bytes(r.content)
    return out_path


def mosaic_and_write_cog(
    parts: List[pathlib.Path],
    out_cog: pathlib.Path,
    blocksize: int = 512,
    compress: str = "DEFLATE"
) -> pathlib.Path:
    gdal.UseExceptions()
    if len(parts) == 1:
        # Translate directly to COG
        gdal.Translate(
            destName=str(out_cog),
            srcDS=str(parts[0]),
            format="COG",
            creationOptions=[f"BLOCKSIZE={blocksize}", f"COMPRESS={compress}", "NUM_THREADS=ALL_CPUS"],
        )
        return out_cog

    # Build VRT then write COG
    vrt_path = out_cog.with_suffix(".vrt")
    gdal.BuildVRT(str(vrt_path), [str(p) for p in parts], separate=False)
    gdal.Translate(
        destName=str(out_cog),
        srcDS=str(vrt_path),
        format="COG",
        creationOptions=[f"BLOCKSIZE={blocksize}", f"COMPRESS={compress}", "NUM_THREADS=ALL_CPUS"],
    )
    try:
        os.remove(vrt_path)
    except Exception:
        pass
    return out_cog


# -------- Workflows --------

def run_bbox_mode(args: argparse.Namespace) -> None:
    service = fetch_service_info(args.service)
    print(f"[INFO] Service WKID: {service.wkid}, units: {service.units_name}, max {service.max_w}x{service.max_h}px")
    # Determine pixel size
    if args.pixel_size is not None:
        pix_x = pix_y = float(args.pixel_size)
        print(f"[INFO] Using user-specified pixel size: {pix_x} (service units/pixel)")
    else:
        # Fallbacks: service pixel size, else 4-inch (0.333333 ft)
        pix_x = service.pixel_size_x if service.pixel_size_x else (1.0 / 3.0)
        pix_y = service.pixel_size_y if service.pixel_size_y else (1.0 / 3.0)
        print(f"[INFO] Using pixel size: {pix_x} x {pix_y} (service units/pixel)")

    # Transform bbox and clip
    bbox_w84 = tuple(map(float, args.bbox))
    bbox_native = transform_bbox_wgs84_to_service(bbox_w84, service.wkid)
    bbox_native = clip_bbox_to_service_extent(bbox_native, service.url)

    # Compute size
    width, height = compute_size_from_bbox_and_pixels(bbox_native, pix_x, pix_y)
    nx, ny = tile_counts(width, height, service.max_w, service.max_h)
    tiles = subdivide_bbox(bbox_native, nx, ny)

    out_dir = pathlib.Path(args.out).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = []
    for i, tile in enumerate(tiles, start=1):
        tw, th = compute_size_from_bbox_and_pixels(tile, pix_x, pix_y)
        part_path = out_dir / f"{pathlib.Path(args.out).stem}_part{i:03d}.tif"
        print(f"[INFO] Exporting tile {i}/{len(tiles)} size {tw}x{th}px ...")
        export_image(service, tile, (tw, th), part_path, token=args.token)
        parts.append(part_path)

    print("[INFO] Writing COG ...")
    out_cog = pathlib.Path(args.out)
    mosaic_and_write_cog(parts, out_cog, blocksize=args.blocksize, compress=args.compress)
    print(f"[OK] Wrote {out_cog}")

    # Cleanup temp parts
    if not args.keep_parts:
        for p in parts:
            try:
                p.unlink()
            except Exception:
                pass


def run_csv_mode(args: argparse.Namespace) -> None:
    service = fetch_service_info(args.service)
    print(f"[INFO] Service WKID: {service.wkid}, units: {service.units_name}, max {service.max_w}x{service.max_h}px")

    # Pixel size selection
    if args.pixel_size is not None:
        pix_x = pix_y = float(args.pixel_size)
        print(f"[INFO] Using user-specified pixel size: {pix_x} (service units/pixel)")
    else:
        pix_x = service.pixel_size_x if service.pixel_size_x else (1.0 / 3.0)
        pix_y = service.pixel_size_y if service.pixel_size_y else (1.0 / 3.0)
        print(f"[INFO] Using pixel size: {pix_x} x {pix_y} (service units/pixel)")

    # Buffer units
    if args.buffer_unit.lower().startswith("meter"):
        buf_dist = meters_to_service_units(float(args.buffer), service.wkid)
    else:
        # assume feet
        buf_dist = float(args.buffer)
    print(f"[INFO] Buffer distance in service units: {buf_dist:.3f}")

    out_dir = pathlib.Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(args.csv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"lon", "lat"}
        if not required.issubset(set(map(str.lower, reader.fieldnames or []))):
            print("[ERROR] CSV must have columns: lon, lat[, id, name]")
            sys.exit(2)

        # Determine exact column names (case-insensitive)
        cols = {c.lower(): c for c in reader.fieldnames}
        for row in reader:
            lon = float(row[cols["lon"]])
            lat = float(row[cols["lat"]])
            rid = row.get(cols.get("id", ""), "") or row.get(cols.get("school_id", ""), "") or ""
            name = row.get(cols.get("name", ""), "") or f"pt_{rid}" or "location"

            # Build square bbox around buffered point (in service CRS)
            tr = Transformer.from_crs(4326, service.wkid, always_xy=True)
            x, y = tr.transform(lon, lat)
            minx = x - buf_dist
            maxx = x + buf_dist
            miny = y - buf_dist
            maxy = y + buf_dist
            bbox_native = clip_bbox_to_service_extent((minx, miny, maxx, maxy), service.url)

            # Compute size and export (with tiling if needed)
            width, height = compute_size_from_bbox_and_pixels(bbox_native, pix_x, pix_y)
            nx, ny = tile_counts(width, height, service.max_w, service.max_h)
            tiles = subdivide_bbox(bbox_native, nx, ny)

            parts = []
            stem = f"{name or 'site'}_{rid}".strip().replace(" ", "_")
            for i, tile in enumerate(tiles, start=1):
                tw, th = compute_size_from_bbox_and_pixels(tile, pix_x, pix_y)
                part_path = out_dir / f"{stem}_part{i:03d}.tif"
                print(f"[INFO] {stem}: exporting tile {i}/{len(tiles)} ({tw}x{th})")
                export_image(service, tile, (tw, th), part_path, token=args.token)
                parts.append(part_path)

            out_cog = out_dir / f"{stem}.tif"
            mosaic_and_write_cog(parts, out_cog, blocksize=args.blocksize, compress=args.compress)
            print(f"[OK] Wrote {out_cog}")

            if not args.keep_parts:
                for p in parts:
                    try:
                        p.unlink()
                    except Exception:
                        pass


# -------- CLI --------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Export Phoenix Aerials pixels via ArcGIS ImageServer and write Cloud Optimized GeoTIFF (COG)."
    )
    p.add_argument("--token", default=None, help="ArcGIS token (if required).")
    p.add_argument("--compress", default="DEFLATE", help="COG compression (DEFLATE, LZW, JPEG).")
    p.add_argument("--blocksize", type=int, default=512, help="COG internal tile size (typ. 256 or 512).")
    p.add_argument("--keep-parts", action="store_true", help="Keep intermediate part TIFFs.")
    p.add_argument(
        "--pixel-size",
        type=float,
        default=None,
        help="Override service pixel size (in service units per pixel). "
             "If omitted, script tries to read from service; fallback 0.333333 (4 inches in feet).",
    )

    sub = p.add_subparsers(dest="mode", required=True)

    # BBOX mode
    b = sub.add_parser("bbox", help="Export a single COG for a WGS84 bbox.")
    b.add_argument("--service", required=True, help="ArcGIS ImageServer URL (ends with /ImageServer).")
    b.add_argument("--bbox", required=True, nargs=4, metavar=("minLon", "minLat", "maxLon", "maxLat"), help="WGS84 bbox.")
    b.add_argument("--out", required=True, help="Output COG path.")
    b.set_defaults(func=run_bbox_mode)

    # CSV mode
    c = sub.add_parser("csv", help="Export COGs for each point in a CSV (buffered square bbox).")
    c.add_argument("--service", required=True, help="ArcGIS ImageServer URL (ends with /ImageServer).")
    c.add_argument("--csv", required=True, help="CSV with columns: lon,lat[,id,name].")
    c.add_argument("--buffer", required=True, type=float, help="Half-size of square buffer around point.")
    c.add_argument("--buffer-unit", choices=["feet", "meters"], default="feet", help="Units for --buffer.")
    c.add_argument("--out-dir", required=True, help="Output directory for COGs.")
    c.set_defaults(func=run_csv_mode)

    return p


def main(argv: Optional[List[str]] = None) -> None:
    gdal.PushErrorHandler("CPLQuietErrorHandler")  # quieter GDAL output
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
