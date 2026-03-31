import numpy as np
from shapely import Point
from shapely.strtree import STRtree

def poisson_disc_samples(layout, width, height, min_distance, min_distance_water, k=30, seed=None, is_land=None, to_land=None):
    if seed is not None:
        np.random.seed(seed)
    
    # Размер ячейки (берём минимальный радиус для корректности)
    base_min_dist = min(min_distance, min_distance_water)
    cell_size = base_min_dist / np.sqrt(2)

    grid_w = int(np.ceil(width / cell_size)) + 1
    grid_h = int(np.ceil(height / cell_size)) + 1
    grid = np.full((grid_h, grid_w), -1, dtype=int)
    
    def random_in_ring(center, r_min):
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(r_min, 2 * r_min)
        return center + np.array([radius * np.cos(angle), radius * np.sin(angle)])
    
    points = []
    active = []

    has_lakes = layout.lakes_polygons is not None and len(layout.lakes_polygons) > 0
    has_bays = layout.bays_polygons is not None and len(layout.bays_polygons) > 0
    
    lakes_index = STRtree(layout.lakes_polygons) if has_lakes else None
    bays_index = STRtree(layout.bays_polygons) if has_bays else None
    
    # Первая точка
    first = np.array([np.random.uniform(0, width), np.random.uniform(0, height)])
    points.append(first)
    active.append(first)

    gx, gy = (first // cell_size).astype(int)
    grid[gy, gx] = 0
    
    while active:
        idx = np.random.randint(len(active))
        center = active[idx]

        # определяем тип центра
        center_is_land = is_land(center[0], center[1])
        r_min = min_distance if center_is_land else min_distance_water

        found = False
        
        for _ in range(k):
            candidate = random_in_ring(center, r_min)

            if not (0 <= candidate[0] < width and 0 <= candidate[1] < height):
                continue

            # определяем тип кандидата
            is_land_point = is_land(candidate[0], candidate[1])

            if is_land_point:
                x, y = to_land(candidate[0], candidate[1])
            else:
                x, y = candidate

            p = Point(x, y)

            # исключаем озёра и заливы
            if has_lakes:
                candidate_lakes = [layout.lakes_polygons[i] for i in lakes_index.query(p)]
                if any(poly.contains(p) for poly in candidate_lakes):
                    continue

            if has_bays:
                candidate_bays = [layout.bays_polygons[i] for i in bays_index.query(p)]
                if any(poly.contains(p) for poly in candidate_bays):
                    continue

            cx, cy = (candidate // cell_size).astype(int)

            too_close = False
            
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < grid_w and 0 <= ny < grid_h:
                        n = grid[ny, nx]
                        if n >= 0:
                            neighbor = points[n]
                            dist = np.linalg.norm(candidate - neighbor)

                            neighbor_is_land = is_land(neighbor[0], neighbor[1])

                            # выбираем дистанцию
                            if is_land_point and neighbor_is_land:
                                min_dist = min_distance
                            elif not is_land_point and not neighbor_is_land:
                                min_dist = min_distance_water
                            else:
                                # граница суша/вода
                                min_dist = max(min_distance, min_distance_water)

                            if dist < min_dist:
                                too_close = True
                                break
                if too_close:
                    break
            
            if not too_close:
                points.append(candidate)
                active.append(candidate)
                grid[cy, cx] = len(points) - 1
                found = True
        
        if not found:
            active.pop(idx)
    
    return np.array(points)