# Маленький урок по географии
# Широта и долгота - это координаты, которые определяют положение точки на поверхности Земли.
# Долгота (longitude) - это координата, которая измеряет расстояние на восток или запад от нулевого меридиана (который проходит через Гринвич, Англия). 
# Долгота может быть от -180 до +180 градусов. Если долгота положительная, то это восточное полушарие, если отрицательная - западное полушарие.
# Широта (latitude) - это координата, которая измеряет расстояние на север или юг от экватора. 
# Широта может быть от -90 до +90 градусов. Если широта положительная, то это северное полушарие, если отрицательная - южное полушарие.
# Здесь мы получаем файл с населенными пунктами, извлекаем их координаты и преобразуем их в пиксели для отображения на карте.

import geopandas as gpd
from PyQt6.QtWidgets import QFileDialog

# доп проверки
def _is_point(obj) -> bool:
    return (
        isinstance(obj, (tuple, list))
        and len(obj) == 2
        and isinstance(obj[0], (int, float))
        and isinstance(obj[1], (int, float))
    )

def _bounds_from_seeds(
    seeds: list[tuple[float, float]] | list[list[tuple[float, float]]]
) -> tuple[float, float, float, float]:
    # вычисляет minx,miny,maxx,maxy по плоскому списку точек или по списку линий, додумался до такого простого решения
    xs: list[float] = []
    ys: list[float] = []

    def collect(pt):
        xs.append(pt[0]); ys.append(pt[1])

    if not seeds:
        return 0.0, 0.0, 0.0, 0.0

    if _is_point(seeds[0]):
        for p in seeds:
            collect(p)
    else:
        for line in seeds:
            for p in line:
                collect(p)

    return min(xs), min(ys), max(xs), max(ys)


def conversion_to_pixels(
    pixels_per_meter: float,
    seeds: list[tuple[float, float]] | list[list[tuple[float, float]]],
    bounds: tuple[float, float, float, float] | None = None
) -> tuple[
       list[tuple[float, float]] | list[list[tuple[float, float]]],
       tuple[int, int]
   ]:
    """
    pixels_per_meter – коэффициент пикселей на метр;
    seeds – либо список точек, либо список линий (каждая линия
    – список кортежей);
    bounds – если передан, используются эти границы, иначе считаются
             по самих seeds.

    Возвращает:
      * список преобразованных координат (float),
      * размер карты в пикселях (int,int).
    """
    if bounds is None:
        minx, miny, maxx, maxy = _bounds_from_seeds(seeds)
    else:
        minx, miny, maxx, maxy = bounds

    if maxx == minx and maxy == miny:
        center = (32.0, 32.0)
        return ([center] if _is_point(seeds[0]) else [[center]]), (64, 64)

    w_m = maxx - minx
    h_m = maxy - miny
    # перевод размер границ в пиксели с минимумом размера по 64 пикселя
    map_w_px = max(int(round(w_m * pixels_per_meter)), 64)
    map_h_px = max(int(round(h_m * pixels_per_meter)), 64)

    # сохраняем пропорции, деля меньшую сторону на большую
    scale_x = map_w_px / w_m if w_m > 0 else map_h_px / h_m
    scale_y = map_h_px / h_m if h_m > 0 else scale_x

    def transform(x, y):
        # перевод координат в пиксели, с инверсией по Y
        px = (x - minx) * scale_x
        py = (maxy - y) * scale_y       # инверсия по Y
        px = max(0.0, min(px, map_w_px - 1))
        py = max(0.0, min(py, map_h_px - 1))
        return px, py

    if _is_point(seeds[0]):
        return [transform(x, y) for x, y in seeds], (map_w_px, map_h_px)
    else:
        return [[transform(x, y) for x, y in line] for line in seeds], (map_w_px, map_h_px)


def import_file_of_areas(layout, text: str, exp_pix: str):
    path, _ = QFileDialog.getOpenFileName(
        layout,
        text,
        "",
        "GIS (*.geojson *.osm *.gpkg *.json)"
    )
    if not path:
        return

    try:
        ppm = float(exp_pix)
    except Exception:
        ppm = 0.01

    data = gpd.read_file(path)
    if data.empty:
        layout.success_label.setText("Файл пустой")
        return
    data = data.to_crs(epsg=3857) # переводим координаты геоданных в метры, чтобы потом корректно преобразовать в пиксели
    layout.geo_data = data

    # извлекаем точки из геоданных, если они есть
    if 'place' in data.columns:
        populated = data[data['place'].isin(['village', 'city', 'town'])]
        # Крпрче, из-за того, что в некоторых файлах точки могут быть представлены как полигоны (например, город может быть полигоном), 
        # мы берем их центры для генерации провинций. Если же это уже точки, то просто берем их координаты.
        seeds = [(p.centroid.x, p.centroid.y)
                 for p in populated.geometry]
        pix_seeds, size = conversion_to_pixels(ppm, seeds)
        layout.pix_seeds = pix_seeds
        layout.map_pixels_size = size

    # извлекаем линии рек, если они есть
    if 'waterway' in data.columns:
        waterways = data[data['waterway'].isin(['river'])]
        # Тут есть тип не только way, но и relation, и в зависимости от типа геометрии может быть LineString или MultiLineString.
        line_seeds = [list(l.coords)
                      for l in waterways.geometry
                      if l.geom_type == 'LineString' or l.geom_type == 'MultiLineString']
        pix_lines, size = conversion_to_pixels(ppm, line_seeds)
        layout.line_seeds = pix_lines
        layout.map_pixels_size = size

    layout.success_label.show()
    print("Принял файл и закончил обработку")