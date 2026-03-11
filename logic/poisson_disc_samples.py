import numpy as np

def poisson_disc_samples(width, height, min_distance, k=30, seed=None, is_land=None):
    """
    Bridson's Poisson disk sampling — заполняет прямоугольник [0, width) × [0, height)
    точками так, чтобы расстояние между любыми двумя было не меньше min_distance.
    
    Возвращает np.array (n, 2) с координатами [x, y].
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Размер ячейки сетки для ускорения поиска
    cell_size = min_distance / np.sqrt(2)
    grid_w = int(np.ceil(width / cell_size)) + 1
    grid_h = int(np.ceil(height / cell_size)) + 1
    grid = np.full((grid_h, grid_w), -1, dtype=int)
    
    def random_in_ring(center):
        angle = np.random.uniform(0, 2 * np.pi)
        radius = np.random.uniform(min_distance, 2 * min_distance)
        return center + np.array([radius * np.cos(angle), radius * np.sin(angle)])
    
    points = []
    active = []
    
    # Первая случайная точка
    first = np.array([np.random.uniform(0, width), np.random.uniform(0, height)])
    points.append(first)
    active.append(first)
    gx, gy = (first // cell_size).astype(int)
    grid[gy, gx] = 0
    
    while active:
        idx = np.random.randint(len(active))
        center = active[idx]
        found = False
        
        for _ in range(k):
            candidate = random_in_ring(center)
            if not (0 <= candidate[0] < width and 0 <= candidate[1] < height):
                continue

            if not is_land(candidate[0], candidate[1]):
                continue
            
            cx, cy = (candidate // cell_size).astype(int)
            too_close = False
            
            # Проверяем соседние ячейки (в квадрате 5×5)
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < grid_w and 0 <= ny < grid_h:
                        n = grid[ny, nx]
                        if n >= 0:
                            dist = np.linalg.norm(candidate - points[n])
                            if dist < min_distance:
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