import numpy as np
from pyproj import Transformer
from shapely import union_all
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from scipy.spatial import Voronoi
import matplotlib.pyplot as plt
from shapely.prepared import prep

from logic.poisson_disc_samples import poisson_disc_samples

TO_LATLON = Transformer.from_crs(3857, 4326, always_xy=True)
TO_METERS = Transformer.from_crs(4326, 3857, always_xy=True)


# === PIXELS -> METERS ===
def pixel_to_meters(px, py, layout):
    x = px / layout.scale_x + layout.minx
    y = layout.maxy - (py / layout.scale_y)
    return x, y


# === ПРОВЕРКА СУШИ ===
def is_land_pixel(layout, px, py):
    x, y = pixel_to_meters(px, py, layout)
    return layout.local_land.contains(Point(x, y))

def is_lake_pixel(layout, px, py):
    if not layout.lakes_polygons:
        return False
    x, y = pixel_to_meters(px, py, layout)
    pt = Point(x, y)
    return any(poly.contains(pt) for poly in layout.lakes_polygons)

def is_sea_pixel(layout, px, py):
    x, y = pixel_to_meters(px, py, layout)
    pt = Point(x, y)
    return layout.local_water.contains(pt)

# === SNAP К СУШЕ ===
def to_land_pixel(layout, px, py):
    x, y = pixel_to_meters(px, py, layout)
    return x, y


# === Вспомогательная функция для конечных полигонов Voronoi ===
def voronoi_finite_polygons_2d(vor, radius=None):
    import numpy as np
    from collections import defaultdict

    new_regions = []
    new_vertices = vor.vertices.tolist()
    center = vor.points.mean(axis=0)
    radius = radius or np.ptp(vor.points, axis=0).max() * 2

    all_ridges = defaultdict(list)
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges[p1].append((p2, v1, v2))
        all_ridges[p2].append((p1, v1, v2))

    for p1, region_idx in enumerate(vor.point_region):
        vertices = vor.regions[region_idx]
        if all(v >= 0 for v in vertices):
            new_regions.append(vertices)
            continue

        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                continue

            t = vor.points[p2] - vor.points[p1]
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
        new_region = [v for _, v in sorted(zip(angles, new_region))]

        new_regions.append(new_region)

    return new_regions, np.asarray(new_vertices)


# === Функция отрисовки полигона ===
def draw_geom(ax, geom, color, alpha=0.6):
    if geom.is_empty:
        return
    if geom.geom_type == "Polygon":
        x, y = geom.exterior.xy
        ax.fill(x, y, color=color, alpha=alpha, linewidth=0)
    elif geom.geom_type == "MultiPolygon":
        for g in geom.geoms:
            x, y = g.exterior.xy
            ax.fill(x, y, color=color, alpha=alpha, linewidth=0)


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
        width=w,
        height=h,
        min_distance=90,
        min_distance_water=180,
        k=30,
        seed=42
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

    # === ПЕРЕВОД В МЕТРЫ ===
    def convert_to_meters(points):
        result = []
        for px, py in points:
            x = px / layout.scale_x + layout.minx
            y = layout.maxy - (py / layout.scale_y)
            result.append([x, y])
        return np.array(result)

    original_m = convert_to_meters(original_px)
    extra_m = convert_to_meters(extra_px)
    all_points = np.vstack([original_m, extra_m]) if len(extra_m) > 0 else original_m

    print(f"Всего точек: {len(all_points)}")

    # === РАЗДЕЛЕНИЕ ТОЧЕК НА СУШУ И ВОДУ ===
    lakes_geom = union_all(layout.lakes_polygons) if layout.lakes_polygons else None

    prep_land = prep(layout.local_land)
    prep_water = prep(layout.local_water)
    prep_lakes = prep(lakes_geom) if lakes_geom else None

    land_points = []
    lake_points = []
    sea_points = []
    for px, py in all_points:
        pt = Point(px, py)

        if prep_lakes and prep_lakes.contains(pt):
            lake_points.append([px, py])

        elif prep_water.contains(pt):
            sea_points.append([px, py])

        elif prep_land.contains(pt):
            land_points.append([px, py])

    land_points = np.array(land_points)
    lake_points = np.array(lake_points)
    sea_points = np.array(sea_points)

    fig, ax = plt.subplots(figsize=(16, 10))

    # === РИСУЕМ СУШУ (фон) ===
    layout.local_land_gdf.plot(ax=ax, color="#d0e0b0", edgecolor="none", alpha=0.9)
    layout.progress.setValue(80)

    # === VORONOI ДЛЯ ОЩЕР ===
    if len(lake_points) >= 4:
        vor_lakes = Voronoi(lake_points)
        lake_regions, lake_vertices = voronoi_finite_polygons_2d(vor_lakes)
        for region in lake_regions:
            poly = Polygon(lake_vertices[region])
            if not poly.is_valid:
                poly = poly.buffer(0)
            poly_lake = poly.intersection(lakes_geom)
            draw_geom(ax, poly_lake, "#4a86e8", alpha=0.6)  # заливка

            # линия границы
            if not poly_lake.is_empty:
                if poly_lake.geom_type == "Polygon":
                    x, y = poly_lake.exterior.xy
                    ax.plot(x, y, color="#003366", linewidth=1.2)  # границы озёр
                elif poly_lake.geom_type == "MultiPolygon":
                    for g in poly_lake.geoms:
                        x, y = g.exterior.xy
                        ax.plot(x, y, color="#003366", linewidth=1.2)

    # === VORONOI ДЛЯ СУШИ ===
    if len(land_points) >= 4:
        vor_land = Voronoi(land_points)
        land_regions, land_vertices = voronoi_finite_polygons_2d(vor_land)
        for region in land_regions:
            poly = Polygon(land_vertices[region])
            if not poly.is_valid:
                poly = poly.buffer(0)
            poly_land = poly.intersection(layout.local_land)
            draw_geom(ax, poly_land, "#030203", alpha=0.6)  # заливка

            # линия границы
            if not poly_land.is_empty:
                if poly_land.geom_type == "Polygon":
                    x, y = poly_land.exterior.xy
                    ax.plot(x, y, color="#7f0000", linewidth=1.2)  # границы суши
                elif poly_land.geom_type == "MultiPolygon":
                    for g in poly_land.geoms:
                        x, y = g.exterior.xy
                        ax.plot(x, y, color="#7f0000", linewidth=1.2)

    # === VORONOI ДЛЯ МОРЯ ===
    if len(sea_points) >= 4:
        vor_water = Voronoi(sea_points)
        water_regions, water_vertices = voronoi_finite_polygons_2d(vor_water)
        for region in water_regions:
            poly = Polygon(water_vertices[region])
            if not poly.is_valid:
                poly = poly.buffer(0)
            poly_water = poly.intersection(layout.local_water)
            draw_geom(ax, poly_water, "#1f4e79", alpha=0.6)  # заливка

            # линия границы
            if not poly_water.is_empty:
                if poly_water.geom_type == "Polygon":
                    x, y = poly_water.exterior.xy
                    ax.plot(x, y, color="#003366", linewidth=1.2)  # границы воды
                elif poly_water.geom_type == "MultiPolygon":
                    for g in poly_water.geoms:
                        x, y = g.exterior.xy
                        ax.plot(x, y, color="#003366", linewidth=1.2)

    # === РИСУЕМ ТОЧКИ ===
    if len(original_m) > 0:
        ax.scatter(original_m[:, 0], original_m[:, 1], c="red", s=30,
                   edgecolors="black", label="Города", zorder=5)

    if len(extra_m) > 0:
        ax.scatter(extra_m[:, 0], extra_m[:, 1], c="blue", s=10, alpha=0.6,
                   label="Фон", zorder=4)

    # === БЕРЕГОВАЯ ЛИНИЯ ===
    coastline = layout.local_land.boundary
    if not coastline.is_empty:
        if coastline.geom_type == "LineString":
            x, y = coastline.xy
            ax.plot(x, y, color="black", linewidth=1.5)
        elif coastline.geom_type == "MultiLineString":
            for line in coastline.geoms:
                x, y = line.xy
                ax.plot(x, y, color="black", linewidth=1.5)

    layout.progress.setValue(100)

    # === ГРАНИЦЫ ВИДА ===
    # all_x = all_points[:, 0]
    # all_y = all_points[:, 1]
    min_x, min_y, max_x, max_y = layout.bbox_3857
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.set_aspect("equal")
    ax.legend()
    ax.set_title(f"Провинции: {len(all_points)} точек")

    plt.tight_layout()
    plt.show()