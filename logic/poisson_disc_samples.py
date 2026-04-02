import numpy as np
from shapely.geometry import Point

def poisson_disc_samples(layout, width, height, min_distance, min_distance_water, k=30, seed=None):
    """
    Poisson disc sampling для land, lake и sea.
    Для sea используется min_distance_water, для land/lake - min_distance.
    """
    if seed is not None:
        np.random.seed(seed)

    # размер ячейки сетки
    cell_size = min(min_distance, min_distance_water) / np.sqrt(2)
    grid_w = int(np.ceil(width / cell_size)) + 1
    grid_h = int(np.ceil(height / cell_size)) + 1
    grid = np.full((grid_h, grid_w), -1, dtype=int)

    def random_in_ring(center, r_min):
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(r_min, 2 * r_min)
        return center + np.array([radius * np.cos(angle), radius * np.sin(angle)])

    points = []
    types = []  # land, lake, sea
    active = []

    def pixel_to_meters(px, py, layout):
        x = px / layout.scale_x + layout.minx
        y = layout.maxy - (py / layout.scale_y)
        return x, y

    def point_type(px, py):
        x, y = pixel_to_meters(px, py, layout)
        pt = Point(x, y)

        # озёра
        if layout.lakes_polygons and any(poly.contains(pt) for poly in layout.lakes_polygons):
            return "lake"
        # море
        elif layout.local_water.contains(pt):
            return "sea"
        # суша
        elif layout.local_land.contains(pt):
            return "land"
        else:
            return None

    # первая точка
    first_x = np.random.uniform(0, width)
    first_y = np.random.uniform(0, height)
    t = point_type(first_x, first_y)
    if t is None:
        raise RuntimeError("Не удалось найти первую точку внутри суши, озера или моря")

    first = np.array([first_x, first_y])
    points.append(first)
    types.append(t)
    active.append(first)
    gx, gy = (first // cell_size).astype(int)
    grid[gy, gx] = 0

    while active:
        idx = np.random.randint(len(active))
        center = active[idx]
        center_type = types[idx]

        # радиус по типу центра
        r_min = min_distance if center_type in ["land", "lake"] else min_distance_water

        found = False
        for _ in range(k):
            candidate = random_in_ring(center, r_min)

            if not (0 <= candidate[0] < width and 0 <= candidate[1] < height):
                continue

            cand_type = point_type(candidate[0], candidate[1])
            if cand_type is None:
                continue

            cx, cy = (candidate // cell_size).astype(int)
            too_close = False

            # проверка соседей в сетке
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < grid_w and 0 <= ny < grid_h:
                        n_idx = grid[ny, nx]
                        if n_idx >= 0:
                            neighbor = points[n_idx]
                            neighbor_type = types[n_idx]

                            dist = np.linalg.norm(candidate - neighbor)

                            # минимальное расстояние между типами
                            if cand_type in ["land", "lake"] and neighbor_type in ["land", "lake"]:
                                min_dist = min_distance
                            elif cand_type == "sea" and neighbor_type == "sea":
                                min_dist = min_distance_water
                            else:
                                # граница суша/море/озёра
                                min_dist = max(min_distance, min_distance_water)

                            if dist < min_dist:
                                too_close = True
                                break
                if too_close:
                    break

            if not too_close:
                points.append(candidate)
                types.append(cand_type)
                active.append(candidate)
                grid[cy, cx] = len(points) - 1
                found = True

        if not found:
            active.pop(idx)

    return np.array(points)