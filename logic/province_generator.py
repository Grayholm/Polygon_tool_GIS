import numpy as np
from pyproj import Transformer
from shapely.geometry import LineString, Point
from scipy.spatial import Voronoi
import matplotlib.pyplot as plt

from logic.poisson_disc_samples import poisson_disc_samples

# === TRANSFORMERS ===
# 3857 <-> 4326
TO_LATLON = Transformer.from_crs(3857, 4326, always_xy=True)
TO_METERS = Transformer.from_crs(4326, 3857, always_xy=True)


# === PIXELS -> METERS ===
def pixel_to_meters(px, py, layout):
    x = px / layout.scale_x + layout.minx
    y = layout.maxy - (py / layout.scale_y)
    return x, y


# === PIXELS -> LAT/LON ===
def pixel_to_latlon(px, py, layout):
    x, y = pixel_to_meters(px, py, layout)
    lon, lat = TO_LATLON.transform(x, y)
    return lon, lat


# === ПРОВЕРКА СУШИ ===
def is_land_pixel(layout, px, py):
    lon, lat = pixel_to_latlon(px, py, layout)
    return layout.local_land.contains(Point(lon, lat))


# === SNAP К СУШЕ ===
def to_land_pixel(layout, px, py):
    lon, lat = pixel_to_latlon(px, py, layout)
    return lon, lat


# === ГЛАВНАЯ ФУНКЦИЯ ===
def generate_province_map(layout, image_display, min_distance: int):

    if not hasattr(layout, 'pix_seeds') or not layout.pix_seeds:
        layout.error_label.setText("Сначала импортируйте файл!")
        layout.error_label.show()
        return

    layout.error_label.hide()

    original_px = np.array(layout.pix_seeds)
    w, h = layout.map_pixels_size

    layout.progress.setVisible(True)
    layout.progress.setValue(10)

    # === POISSON ===
    extra_px = poisson_disc_samples(
        layout,
        w, h,
        min_distance,
        min_distance_water=min_distance * 2,
        k=30,
        seed=42,
        is_land=lambda px, py: is_land_pixel(layout, px, py),
        to_land=lambda px, py: to_land_pixel(layout, px, py)
    )

    layout.progress.setValue(40)

    # === ФИЛЬТР ОТ ГОРОДОВ ===
    if len(original_px) > 0:
        from scipy.spatial import KDTree
        tree = KDTree(original_px)
        kept = []
        for p in extra_px:
            dist, _ = tree.query(p)
            if dist > min_distance * 0.65:
                kept.append(p)
        extra_px = np.array(kept)

    layout.progress.setValue(60)

    # === ПЕРЕВОД В ГРАДУСЫ ===
    def convert_to_latlon(points):
        result = []
        for px, py in points:
            x = px / layout.scale_x + layout.minx
            y = layout.maxy - (py / layout.scale_y)
            lon, lat = TO_LATLON.transform(x, y)
            result.append([lon, lat])
        return np.array(result)

    original_ll = convert_to_latlon(original_px)
    extra_ll = convert_to_latlon(extra_px)

    all_points = (
        np.vstack([original_ll, extra_ll])
        if len(extra_ll) > 0 else original_ll
    )

    print(f"Всего точек: {len(all_points)}")

    # === VORONOI В МЕТРАХ ===
    vor = Voronoi(all_points)

    fig, ax = plt.subplots(figsize=(16, 10))

    # === РИСУЕМ СУШУ (В МЕТРАХ!) ===
    layout.local_land_gdf.plot(
        ax=ax,
        color="#d0e0b0",
        edgecolor="none",
        alpha=0.9
    )

    layout.progress.setValue(80)

    print("Режем Voronoi по суше...")

    # === ОБРЕЗКА ===
    land = layout.local_land  # уже должен быть в 3857!

    for ridge in vor.ridge_vertices:
        if -1 in ridge or len(ridge) < 2:
            continue

        line = LineString(vor.vertices[ridge])
        clipped = line.intersection(land)

        if clipped.is_empty:
            continue

        if clipped.geom_type == "LineString":
            x, y = clipped.xy
            ax.plot(x, y, color="#9b1c2c", linewidth=0.8)

        elif clipped.geom_type == "MultiLineString":
            for sub in clipped.geoms:
                x, y = sub.xy
                ax.plot(x, y, color="#9b1c2c", linewidth=0.8)

    # === ТОЧКИ ===
    if len(original_ll) > 0:
        ax.scatter(
            original_ll[:, 0],
            original_ll[:, 1],
            c="red",
            s=30,
            edgecolors="black",
            label="Города",
            zorder=5
        )

    ax.scatter(
        extra_ll[:, 0],
        extra_ll[:, 1],
        c="blue",
        s=10,
        alpha=0.6,
        label="Фон",
        zorder=4
    )

    layout.progress.setValue(100)

    # === ГРАНИЦЫ ===
    minx, miny, maxx, maxy = layout.local_land_gdf.total_bounds
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    ax.set_aspect("equal")
    ax.legend()
    ax.set_title(f"Провинции: {len(all_points)} точек")

    plt.tight_layout()
    plt.show()