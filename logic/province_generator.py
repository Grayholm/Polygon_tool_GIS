from collections import deque
from PIL import Image
import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

used_colors = set()

def generate_province_map(layout, exp_pix, image_display):
    """
    Генерация карты провинций с сохранением пропорций исходной области,
    выравниванием размеров провинций по наименьшей найденной провинции и
    крупными провинциями на море.
    - exp_pix: целевая ширина результата в пикселях (высота рассчитывается по пропорциям)
    - image_display: объект с методом set_image(PIL.Image)
    - main_layout.progress — QProgressBar (опционально)
    """
    used_colors.clear()
    points = np.array(layout.pix_seeds)
    if points.size == 0:
        return
    vor = Voronoi(points)
    fig = voronoi_plot_2d(vor)
    plt.gca().invert_yaxis()      # т.к. мы зеркалим Y при трансформации
    plt.show()