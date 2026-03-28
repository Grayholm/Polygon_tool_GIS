from pathlib import Path

import geopandas as gpd
import numpy as np
from scipy.spatial import Voronoi
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
import random

def poisson_disk_sampling_global(land_union, r=2.8, k=30, max_attempts_first=20000):
    """
    Poisson Disk Sampling (Bridson) строго внутри суши всего мира.
    """
    if land_union.is_empty or land_union.area < 1:
        raise ValueError("Геометрия суши пустая или слишком мала")

    # Границы всего мира (с запасом)
    xmin, ymin, xmax, ymax = -180, -90, 180, 90

    cell_size = r / np.sqrt(2)
    nx = int(np.ceil((xmax - xmin) / cell_size)) + 4
    ny = int(np.ceil((ymax - ymin) / cell_size)) + 4
    grid = np.full((ny, nx), -1, dtype=int)

    points = []

    def grid_coords(x, y):
        i = int((x - xmin) / cell_size)
        j = int((y - ymin) / cell_size)
        return max(0, min(nx-1, i)), max(0, min(ny-1, j))

    # === Поиск первой точки (более надёжный способ) ===
    print("Ищем первую точку внутри суши...")
    found = False
    for attempt in range(max_attempts_first):
        x = np.random.uniform(xmin, xmax)
        y = np.random.uniform(ymin, ymax)
        if land_union.contains(Point(x, y)):
            points.append([x, y])
            i, j = grid_coords(x, y)
            grid[j, i] = 0
            found = True
            print(f"Первая точка найдена: ({x:.2f}, {y:.2f})")
            break
    if not found:
        raise ValueError("Не удалось найти ни одной точки внутри суши. Проверьте файл.")

    active = [0]

    while active:
        idx = random.choice(active)
        px, py = points[idx]

        found_candidate = False
        for _ in range(k):
            angle = 2 * np.pi * np.random.random()
            dist = r + r * np.random.random()
            cx = px + dist * np.cos(angle)
            cy = py + dist * np.sin(angle)

            # Проверка границ мира
            if not (xmin <= cx <= xmax and ymin <= cy <= ymax):
                continue

            candidate = Point(cx, cy)
            if land_union.contains(candidate):
                gi, gj = grid_coords(cx, cy)
                valid = True

                # Проверка соседей в сетке
                for di in range(-2, 3):
                    for dj in range(-2, 3):
                        ni, nj = gi + di, gj + dj
                        if 0 <= ni < nx and 0 <= nj < ny:
                            nidx = grid[nj, ni]
                            if nidx >= 0:
                                nx_, ny_ = points[nidx]
                                if np.hypot(cx - nx_, cy - ny_) < r:
                                    valid = False
                                    break
                    if not valid:
                        break

                if valid:
                    new_idx = len(points)
                    points.append([cx, cy])
                    grid[gj, gi] = new_idx
                    active.append(new_idx)
                    found_candidate = True
                    break

        if not found_candidate:
            active.remove(idx)

    return np.array(points)

BASE_DIR = Path(__file__).resolve().parent
file_path = BASE_DIR.parent / "ne_10m_land" / "ne_10m_land.shp"


land_gdf = gpd.read_file(file_path)

print("Объединяем геометрию суши...")
land_union = land_gdf.union_all()

# Опционально: упрощаем геометрию для ускорения contains()
if land_union.geom_type == "GeometryCollection":
    land_union = unary_union([geom for geom in land_union.geoms if geom.geom_type in ("Polygon", "MultiPolygon")])

land_union = land_union.simplify(tolerance=0.01, preserve_topology=True)

print(f"Суша загружена. Общая геометрия: {land_union.geom_type}, площадь ≈ {land_union.area:.1f}")

# ====================== ГЕНЕРАЦИЯ ТОЧЕК ======================

r = 2.8          # ← Меняй это значение:
                 # 3.5–4.0 → мало провинций (~100–200)
                 # 2.5–2.8 → средне (~400–700)
                 # 2.0–2.3 → много провинций

points = poisson_disk_sampling_global(land_union, r=r, k=30)

print(f"Сгенерировано центров провинций: {len(points)}")

if len(points) < 5:
    raise ValueError("Слишком мало точек. Попробуйте уменьшить r.")

# ====================== VORONOI + ВИЗУАЛИЗАЦИЯ ======================

vor = Voronoi(points)

fig, ax = plt.subplots(figsize=(18, 10))

# Фон суши
land_gdf.plot(ax=ax, color="#d0e0b0", edgecolor="none", alpha=0.9)

# Центры
ax.scatter(points[:, 0], points[:, 1], c="#003366", s=6, zorder=5, label="Центры провинций")

# Границы провинций (только внутри суши)
print("Обрезаем рёбра Voronoi по суше...")
for ridge in vor.ridge_vertices:
    if -1 not in ridge and len(ridge) >= 2:
        line = LineString(vor.vertices[ridge])
        clipped = line.intersection(land_union)
        
        if not clipped.is_empty:
            if clipped.geom_type == "LineString":
                x, y = clipped.xy
                ax.plot(x, y, color="#9b1c2c", linewidth=0.8, alpha=0.9)
            elif clipped.geom_type == "MultiLineString":
                for sub in clipped.geoms:
                    x, y = sub.xy
                    ax.plot(x, y, color="#9b1c2c", linewidth=0.8, alpha=0.9)

ax.set_title(f"Провинции мира по Voronoi + Poisson Disk Sampling (r = {r})", 
             fontsize=16, pad=15)
ax.set_xlabel("Долгота")
ax.set_ylabel("Широта")
ax.legend()
ax.set_aspect("equal", adjustable="box")
ax.set_xlim(-180, 180)
ax.set_ylim(-90, 90)

plt.tight_layout()
plt.show()