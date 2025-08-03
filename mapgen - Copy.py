import gpxpy
import contextily as ctx
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from pyproj import Transformer
from PIL import Image, ImageDraw, ImageFont
import os
import random

OUTPUT_FOLDER = 'static/output'
NORTH_ICON_PATH = 'static/icons/northstar.png'

def parse_kurviger_gpx(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        gpx = gpxpy.parse(f)

    points = []
    pois = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.longitude, point.latitude))

    # Waypoints (standard GPX)
    for wp in gpx.waypoints:
        name = (wp.name or "").strip()
        if name and not any(bad in name.lower() for bad in ['shaping point', 'additional waypoint']):
            pois.append((wp.longitude, wp.latitude, name))

    # Route points (used by Kurviger)
    for rte in gpx.routes:
        for rtept in rte.points:
            name = (rtept.name or "").strip()
            if name and not any(bad in name.lower() for bad in ['shaping point', 'additional waypoint']):
                pois.append((rtept.longitude, rtept.latitude, name))

    return points, pois

def render_map(gpx_files, output_path, basemap='OpenStreetMap.Mapnik'):
    image_paths = []

    for idx, gpx_file in enumerate(gpx_files):
        points, pois = parse_kurviger_gpx(gpx_file)
        if not points:
            continue

        transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
        points_proj = [transformer.transform(*pt) for pt in points]
        pois_proj = [(transformer.transform(lon, lat), name) for lon, lat, name in pois]

        x, y = zip(*points_proj)

        fig, ax = plt.subplots(figsize=(12, 10), dpi=300)
        ax.plot(x, y, color='red', linewidth=3, zorder=2)
        ctx.add_basemap(ax, crs='epsg:3857', source=ctx.providers.get(basemap))
        ax.set_aspect('equal')
        ax.set_axis_off()

        # Plot POIs
        legend_labels = []
        for i, ((px, py), name) in enumerate(pois_proj):
            ax.plot(px, py, 'o', color='yellow', markersize=6, zorder=4)

            offset_x = random.choice([-800, 800])
            offset_y = random.choice([-500, 500])
            ax.text(px + offset_x, py + offset_y, f"{i + 1}. {name}",
                    fontsize=9, color='white',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='gray', alpha=0.75),
                    zorder=5)
            legend_labels.append(f"{i + 1}. {name}")

        output_file = os.path.join(OUTPUT_FOLDER, f'map_{idx + 1}.png')
        fig.savefig(output_file, bbox_inches=None, pad_inches=0.1)
        plt.close(fig)

        # Reopen image for Pillow overlays
        image = Image.open(output_file).convert("RGBA")
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()

        # Draw POI Legend
        if legend_labels:
            box_padding = 14
            line_spacing = 26
            width = max(draw.textlength(line, font=font) for line in legend_labels) + 2 * box_padding
            height = len(legend_labels) * line_spacing + 2 * box_padding
            x, y = 30, image.height - height - 30
            draw.rectangle([x, y, x + width, y + height], fill=(50, 50, 50, 200))

            for i, line in enumerate(legend_labels):
                draw.text((x + box_padding, y + box_padding + i * line_spacing),
                          line, fill='white', font=font)

        # Add northstar
        try:
            north_img = Image.open(NORTH_ICON_PATH).convert("RGBA")
            nx, ny = image.width - north_img.width - 30, 30
            image.paste(north_img, (nx, ny), north_img)
        except Exception as e:
            print("Northstar icon missing or failed:", e)

        image.save(output_file)
        image_paths.append(output_file)

    return image_paths
