from global_land_mask import globe
import numpy as np
from pyproj import Transformer
from shapely import Point

from logic.poisson_disc_samples import poisson_disc_samples
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

used_colors = set()

# Создаем Transformer один раз при загрузке модуля (оптимизация)
_TRANSFORMER = Transformer.from_crs(3857, 4326, always_xy=True)

class PixelToLatLon:
    def __init__(self):
        # EPSG:3857 -> EPSG:4326 - используем глобальный transformer
        pass

    def transform(self, x, y):
        return _TRANSFORMER.transform(x, y)

# Кэшируем единственный экземпляр
_pixel_to_latlon = PixelToLatLon()

def pixels_to_degrees(px, py, minx, maxy, scale_x, scale_y, local_land):
    def meters_to_degrees(x, y):
        x, y = _pixel_to_latlon.transform(x, y)
        point = Point(x, y)
        return local_land.contains(point)

    def pixels_to_meters(px, py):
        x = px / scale_x + minx
        y = maxy - (py / scale_y)
        return x, y

    x, y = pixels_to_meters(px, py)

    return meters_to_degrees(x, y)

def is_land_pixel(layout, px, py):
    return pixels_to_degrees(
        px, py,
        layout.minx,
        layout.maxy,
        layout.scale_x,
        layout.scale_y,
        layout.local_land_polygons
    )

def to_land_pixel(layout, px, py):
    x = px / layout.scale_x + layout.minx
    y = layout.maxy - (py / layout.scale_y)

    dx, dy = _pixel_to_latlon.transform(x, y)

    return dx, dy

def generate_province_map(layout, image_display, min_distance: int):
    used_colors.clear()
    if not hasattr(layout, 'pix_seeds') or not layout.pix_seeds:
            layout.error_label.setText("Сначала импортируйте файл с населенными пунктами!")
            layout.error_label.show()
            return

    layout.error_label.hide()

    original_points = np.array(layout.pix_seeds)  # исходные точки
    w, h = layout.map_pixels_size

    layout.progress.setVisible(True)
    layout.progress.setValue(10)

    layout.error_label.hide()

    min_distance_water = min_distance * 2

    # Генерируем заполняющие точки по всей карте
    extra_points = poisson_disc_samples(layout, w, h, min_distance, min_distance_water=min_distance_water, k=30, seed=42, is_land=lambda px, py: is_land_pixel(layout, px, py), to_land=lambda px, py: to_land_pixel(layout, px, py))

    layout.progress.setValue(30)

    # Фильтруем: не добавляем точки слишком близко к исходным
    if len(original_points) > 0:
        from scipy.spatial import KDTree
        tree = KDTree(original_points)
        kept = []
        for p in extra_points:
            dist, _ = tree.query(p)
            if dist > min_distance * 0.65:
                kept.append(p)
        extra_points = np.array(kept)

    layout.progress.setValue(60)

    # Объединяем
    all_points = np.vstack([original_points, extra_points]) if len(extra_points) > 0 else original_points

    print(f"Добавлено фоновых точек: {len(extra_points)}, всего точек: {len(all_points)}")

    vor = Voronoi(all_points)

    voronoi_plot_2d(vor)
    plt.gca().invert_yaxis()  # Инвертируем Y, это из-за matplotlib

    layout.progress.setValue(80)

    # Подсветим исходные точки
    if len(original_points) > 0:
        plt.plot(original_points[:, 0], original_points[:, 1], 'ro', markersize=8, 
                markeredgecolor='black', label='Исходные населённые пункты')
        
    layout.progress.setValue(100)
    
    plt.plot(extra_points[:, 0], extra_points[:, 1], 'bo', markersize=4, alpha=0.6, label='Фоновые точки')
    plt.legend()
    plt.title(f"Провинции: {len(vor.regions)} (всего точек: {len(all_points)})")
    plt.show()