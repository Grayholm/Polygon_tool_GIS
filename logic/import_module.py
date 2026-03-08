# Маленький урок по географии
# Широта и долгота - это координаты, которые определяют положение точки на поверхности Земли.
# Долгота (longitude) - это координата, которая измеряет расстояние на восток или запад от нулевого меридиана (который проходит через Гринвич, Англия). 
# Долгота может быть от -180 до +180 градусов. Если долгота положительная, то это восточное полушарие, если отрицательная - западное полушарие.
# Широта (latitude) - это координата, которая измеряет расстояние на север или юг от экватора. 
# Широта может быть от -90 до +90 градусов. Если широта положительная, то это северное полушарие, если отрицательная - южное полушарие.
# Здесь мы получаем файл с населенными пунктами, извлекаем их координаты и преобразуем их в пиксели для отображения на карте.

import geopandas as gpd
from PyQt6.QtWidgets import QFileDialog

def conversion_to_pixels(exp_pix, data: gpd.GeoDataFrame, seeds: list[tuple[int, int]] | list[list[tuple[float, ...]]]
    ) -> list[tuple[int, int]] | list[list[tuple[int, int]]]:
    lon_min, lat_min, lon_max, lat_max = data.total_bounds
    map_w, map_h = int((lat_max - lat_min) * exp_pix), int((lon_max - lon_min) * exp_pix)

    # Масштабирование координат в пиксели
    # (map_w - 1) - это ширина/высота карты в пикселях. 
    # Так как отсчет начинается от 0, то максимальный индекс пикселя будет на единицу меньше. 
    # (lon_max - lon_min) и (lat_max - lat_min) - это диапазон координат в градусах.
    # ДЕлим количество пикселей на диапазон координат в градусах, чтобы получить масштаб в пикселях на градус.
    scale_x = (map_w - 1) / (lon_max - lon_min)
    scale_y = (map_h - 1) / (lat_max - lat_min)

    # Преобразование координат в пиксели
    # (x - lon_min) * scale_x - это смещение от минимальной долготы, умноженное на масштаб, чтобы получить пиксели по горизонтали.
    # (lat_max - y) * scale_y - это смещение от максимальной широты, умноженное на масштаб, чтобы получить пиксели по вертикали.
    if isinstance(seeds[0], tuple):
        pix_seeds_float = [
            ((x - lon_min) * scale_x, (lat_max - y) * scale_y)
            for x, y in seeds
        ]
        # Округление координат до целых чисел
        pix_seeds = [(int(x), int(y)) for x, y in pix_seeds_float]

        return pix_seeds

    elif isinstance(seeds[0], list):
        line_seeds_float = [
            [((x - lon_min) * scale_x, (lat_max - y) * scale_y) for x, y in line]
            for line in seeds
        ]
        # Округление координат до целых чисел
        line_seeds = [[(int(x), int(y)) for x, y in line] for line in line_seeds_float]

        return line_seeds

def import_file_of_areas(layout, text: str, exp_pix: str):
    path, _ = QFileDialog.getOpenFileName(
        layout,
        text,
        "",
        "GIS (*.geojson *.osm *.gpkg *.json)"
    )
    if not path:
        return
    
    exp_pix = int(exp_pix)

    data = gpd.read_file(path)

    layout.geo_data = data

    # Получение координат населенных пунктов (Долгота и широта по типу (15.3296971, 49.9613718))
    if 'place' in data.columns:
        populated_areas = data[data['place'].isin(['village', 'hamlet', 'suburb'])]
        seeds = [(p.x, p.y) for p in populated_areas.geometry]

        pix_seeds = conversion_to_pixels(exp_pix, populated_areas, seeds)
        
        # На выход идет список кортежей с координатами в пикселях, типа [(x1, y1), (x2, y2), ...]
        layout.pix_seeds = pix_seeds

    if 'waterway' in data.columns:
        line_areas = data[data['waterway'].isin(['river', 'stream'])]

        line_linestrings = line_areas[line_areas.geometry.type == 'LineString'].geometry
        line_seeds = [list(line.coords) for line in line_linestrings]

        line_seeds = conversion_to_pixels(exp_pix, line_areas, line_seeds)

        # На выход идет список списков кортежей с координатами в пикселях, типа [[(x1, y1), (x2, y2), ...], [...], ...]
        layout.line_seeds = line_seeds

    layout.success_label.show()
    # print(layout.pix_seeds)
    print(layout.line_seeds)
    print("Принял файл и закончил обработку")