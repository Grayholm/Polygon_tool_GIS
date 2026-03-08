# Маленький урок по географии
# Широта и долгота - это координаты, которые определяют положение точки на поверхности Земли.
# Долгота (longitude) - это координата, которая измеряет расстояние на восток или запад от нулевого меридиана (который проходит через Гринвич, Англия). 
# Долгота может быть от -180 до +180 градусов. Если долгота положительная, то это восточное полушарие, если отрицательная - западное полушарие.
# Широта (latitude) - это координата, которая измеряет расстояние на север или юг от экватора. 
# Широта может быть от -90 до +90 градусов. Если широта положительная, то это северное полушарие, если отрицательная - южное полушарие.
# Здесь мы получаем файл с населенными пунктами, извлекаем их координаты и преобразуем их в пиксели для отображения на карте.

import geopandas as gpd
from PyQt6.QtWidgets import QFileDialog

def conversion_to_pixels(
    pixels_per_meter: float,          # например 0.5, 1.0, 2.0, 4.0
    data: gpd.GeoDataFrame,
    seeds: list[tuple[float, float]] | list[list[tuple[float, float]]]
) -> tuple[list[tuple[int, int]] | list[list[tuple[int, int]]], tuple[int, int]]:
    """
    Возвращает:
    - преобразованные координаты в пикселях
    - итоговый размер карты (width, height) в пикселях
    """
    if data.empty:
        return [], (1, 1)

    minx, miny, maxx, maxy = data.total_bounds

    # Реальная ширина и высота в метрах (в проекции 3857)
    w_meters  = maxx - minx
    h_meters = maxy - miny

    # Размер в пикселях
    map_w_px  = int(w_meters  * pixels_per_meter)
    map_h_px = int(h_meters * pixels_per_meter)

    # Защита от слишком маленькой карты
    map_w_px  = max(map_w_px,  64)
    map_h_px = max(map_h_px, 64)

    # Вычисляем масштаб для преобразования координат в пиксели, сохраняя пропорции
    scale_x = map_w_px  / w_meters   if w_meters  > 0 else 1
    scale_y = map_h_px / h_meters  if h_meters > 0 else 1

    # Преобразование координат в пиксели
    def transform(x, y):
        px = int((x - minx) * scale_x)
        py = int((maxy - y) * scale_y)   # инверсия Y для экрана
        # Ограничиваем, чтобы не вылезти за пределы из-за округления
        px = max(0, min(px, map_w_px - 1))
        py = max(0, min(py, map_h_px - 1))
        return px, py


    if isinstance(seeds[0], (tuple, list)) and len(seeds[0]) == 2:
        # список точек
        pix_seeds = [transform(x, y) for x, y in seeds]
        return pix_seeds, (map_w_px, map_h_px)
    else:
        # список линий / мультигеометрий
        pix_lines = [[transform(x, y) for x, y in line] for line in seeds]
        return pix_lines, (map_w_px, map_h_px)

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
        ppm = float(exp_pix)  # например "1.0" или "0.8"
    except:
        ppm = 0.01   # значение по умолчанию

    data = gpd.read_file(path)
    data = gpd.read_file(path)
    if data.empty:
        layout.success_label.setText("Файл пустой")
        return
    data = data.to_crs(epsg=3857) # Преобразуем координаты в проекцию Web Mercator (EPSG:3857), которая использует метры в качестве единиц измерения. Это позволит нам работать с координатами в пикселях более точно.

    layout.geo_data = data

    # Получение координат населенных пунктов (Долгота и широта по типу (15.3296971, 49.9613718))
    if 'place' in data.columns:
        populated_areas = data[data['place'].isin(['village', 'hamlet', 'suburb'])]
        seeds = [(p.x, p.y) for p in populated_areas.geometry]

        pix_seeds, (x, y) = conversion_to_pixels(ppm, data, seeds)
        
        # На выход идет список кортежей с координатами в пикселях, типа [(x1, y1), (x2, y2), ...]
        layout.pix_seeds = pix_seeds
        layout.map_pixels_size = (x, y)

    if 'waterway' in data.columns:
        line_areas = data[data['waterway'].isin(['river', 'stream'])]

        line_linestrings = line_areas[line_areas.geometry.type == 'LineString'].geometry
        line_seeds = [list(line.coords) for line in line_linestrings]

        line_seeds, (x, y) = conversion_to_pixels(ppm, data, line_seeds)

        # На выход идет список списков кортежей с координатами в пикселях, типа [[(x1, y1), (x2, y2), ...], [...], ...]
        layout.line_seeds = line_seeds
        layout.map_pixels_size = (x, y)

    layout.success_label.show()
    print(layout.pix_seeds)
    print(len(layout.pix_seeds))
    print(layout.line_seeds)
    print("Принял файл и закончил обработку")