
import os
import gpxpy
import contextily as ctx
import matplotlib.pyplot as plt
from shapely.geometry import box
from pyproj import Transformer
import numpy as np
import contextily as ctx
ctx.set_cache_dir("tile_cache")  # Optional, to control where tiles are saved

import time

def clean_old_files(folder, max_age_seconds=3600):
    now = time.time()
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath) and now - os.path.getmtime(filepath) > max_age_seconds:
            os.remove(filepath)



OUTPUT_FOLDER = 'static/output'

def parse_kurviger_gpx(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        gpx = gpxpy.parse(f)

    points = []
    pois = []

    # Try to extract track points first
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.longitude, point.latitude))

    # If no track found, fall back to route points
    if not points:
        for rte in gpx.routes:
            for rtept in rte.points:
                points.append((rtept.longitude, rtept.latitude))


    for wp in gpx.waypoints:
        name = (wp.name or "").strip()
        if name and not any(bad in name.lower() for bad in ['shaping point', 'additional waypoint', 'omv', 'petrom', 'mol', 'lukoil', 'rompetrol', 'gas station', 'ulita', 'Ulita', 'Ulița', 'Ulița mare, DJ105E', 'Ulita mare, DJ105E', 'calea', 'waypoint', 'Waypoint', 'Centura' 'Centura de Vest, DN1 ', 'Continue', 'Șoseaua', 'Soseaua', 'Șoseaua Bran, DN73, DN73A']) and not name.lower().startswith(('dj', 'dn', 'dc', 'strada', 'omv', 'petrom', 'mol', 'lukoil', 'rompetrol', 'gas station', 'ulita', 'Ulita', 'Ulița', 'Ulița mare, DJ105E', 'Ulita mare, DJ105E', 'calea', 'waypoint', 'Waypoint', 'Centura' 'Centura de Vest, DN1 ', 'Continue', 'Șoseaua', 'Soseaua', 'Șoseaua Bran, DN73, DN73A', 'Bulevard', 'Centura', 'Continue')):
            pois.append((wp.longitude, wp.latitude, name))

    for rte in gpx.routes:
        for rtept in rte.points:
            name = (rtept.name or "").strip()
            if name and not any(bad in name.lower() for bad in ['shaping point', 'additional waypoint', 'omv', 'petrom', 'mol', 'lukoil', 'rompetrol', 'gas station', 'ulita', 'Ulita', 'Ulița', 'Ulița mare, DJ105E', 'Ulita mare, DJ105E', 'calea', 'waypoint']) and not name.lower().startswith(('dj', 'dn', 'dc', 'strada', 'omv', 'petrom', 'mol', 'lukoil', 'rompetrol', 'gas station', 'ulita', 'Ulita', 'Ulița', 'Ulița mare, DJ105E', 'Ulita mare, DJ105E', 'calea', 'waypoint', 'Waypoint', 'Centura' 'Centura de Vest, DN1 ', 'Continue', 'Șoseaua', 'Soseaua', 'Șoseaua Bran, DN73, DN73A', 'Bulevard', 'Centura', 'Continue')):
                pois.append((rtept.longitude, rtept.latitude, name))

    return points, pois

def repel_labels(pois_proj, padding=10000, min_px_dist=30, max_iter=100):
    pois_proj = np.array(pois_proj, dtype=np.float64)
    label_positions = pois_proj.copy()

    for _ in range(max_iter):
        displacement = np.zeros_like(label_positions)
        for i, pos_i in enumerate(label_positions):
            for j, pos_j in enumerate(label_positions):
                if i == j:
                    continue
                diff = pos_i - pos_j
                distance = np.linalg.norm(diff)
                if distance < padding and distance > 0:
                    repulsion = (padding - distance) * (diff / distance)
                    displacement[i] += repulsion
        label_positions += displacement * 0.01
    return label_positions

def render_map(gpx_files, output_path, basemap='OpenStreetMap.Mapnik'):
    print(f"[DEBUG] render_map called with: {gpx_files}")
    image_paths = []
    clean_old_files('static/output', 3600)  # 1 hour
    clean_old_files('static/gpx', 3600)

    for idx, gpx_file in enumerate(gpx_files):
        print(f"[DEBUG] Parsing: {gpx_file}")
        points, pois = parse_kurviger_gpx(gpx_file)
        print(f"[DEBUG] → {len(points)} route points, {len(pois)} POIs")

        if not points:
            print(f"[WARNING] No track points found in {gpx_file}")
            continue
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
        points_proj = [transformer.transform(*pt) for pt in points]
        pois_proj = [(transformer.transform(lon, lat), name) for lon, lat, name in pois]


        x, y = zip(*points_proj)

        # Calculate bounds based on projected track points
        buffer = 2000  # meters padding around the route
        left, right = min(x) - buffer, max(x) + buffer
        bottom, top = min(y) - buffer, max(y) + buffer

        # Create the figure
        fig, ax = plt.subplots(figsize=(11.69, 8.27), dpi=400)

        # Fetch basemap tiles directly using bounds2img()
        #zoom = 13  # You can adjust this for more/less detail
        #img, ext = ctx.bounds2img(left, bottom, right, top, zoom=zoom, source=ctx.providers.get(basemap))

        # Show basemap
        #ax.imshow(img, extent=ext, interpolation='bilinear', zorder=1)
        #ax.set_xlim(left, right)
        #ax.set_ylim(bottom, top)

        # Plot the route line on top
        ax.plot(x, y, color='red', linewidth=3, zorder=2)



        x, y = zip(*points_proj)
        fig, ax = plt.subplots(figsize=(12, 10), dpi=400)
        ax.plot(x, y, color='red', linewidth=3, zorder=2)
        ctx.add_basemap(ax, crs='epsg:3857', source=ctx.providers.get(basemap), zoom=13)




        ax.set_aspect('equal')
        ax.set_axis_off()

        # Repelling force label positioning
        positions_only = [pos for pos, _ in pois_proj]
        labels = [name for _, name in pois_proj]
        label_positions = repel_labels(positions_only, padding=20000)

        for (px, py), name in zip(label_positions, labels):
            ax.text(px, py, name,
                    fontsize=9,
                    color='white',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='gray', edgecolor='black', alpha=0.7),
                    zorder=5)

        for (px, py) in positions_only:
            ax.plot(px, py, 'o', color='yellow', markersize=6, zorder=4)

        output_file = os.path.join(OUTPUT_FOLDER, f'map_{idx + 1}.png')


        # Build POI legend
        legend_lines = [f"{i + 1}. {name}" for i, (_, name) in enumerate(pois_proj)]
        legend_text = "\n".join(legend_lines)

        # Compute placement: bottom-left corner of the map image
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        legend_x = x_min + 0.01 * (x_max - x_min)
        legend_y = y_min + 0.01 * (y_max - y_min)

        # Draw legend on the map
        ax.text(
            legend_x,
            legend_y,
            legend_text,
            fontsize=8,
            color='white',
            verticalalignment='bottom',            
            bbox=dict(boxstyle='round,pad=0.5', facecolor='gray', edgecolor='black', alpha=0.7),
            zorder=10,
            family='monospace',
        )


        fig.savefig(output_file, bbox_inches='tight', pad_inches=0)
        from PIL import Image

        # After saving figure to PNG
        fig.savefig(output_file, bbox_inches='tight', pad_inches=0)
        plt.close(fig)

        # --- Add northstar icon ---
        try:
            image = Image.open(output_file).convert("RGBA")
            north_icon = Image.open("static/icons/northstar.png").convert("RGBA")

            # Resize northstar (optional)
            from PIL import Image  # add this at the top if not already present

            # Compatibility fix for Pillow ≥ 10
            try:
                resample = Image.Resampling.LANCZOS
            except AttributeError:
                resample = Image.LANCZOS  # fallback for older versions

            north_icon.thumbnail((80, 80), resample)

            # Compute position for top-right corner with margin
            margin = 30
            x = image.width - north_icon.width - margin
            y = margin

            # Paste north icon with transparency
            image.paste(north_icon, (x, y), north_icon)
            image.save(output_file)
        except Exception as e:
            print(f"[WARNING] Could not add northstar icon: {e}")
        plt.close(fig)

        image_paths.append(output_file)

    return image_paths
