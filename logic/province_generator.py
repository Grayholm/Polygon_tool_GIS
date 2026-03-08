from collections import deque
from PIL import Image
import numpy as np
import random
import math

used_colors = set()

def generate_province_map(main_layout, pix_seeds, line_seeds, exp_pix, image_display):
    """
    Генерация карты провинций с сохранением пропорций исходной области,
    выравниванием размеров провинций по наименьшей найденной провинции и
    крупными провинциями на море.
    - pix_seeds: list of (x,y) — исходные "деревни" (координаты в исходной системе)
    - line_seeds: list of lists of (x,y); every list of (x,y) is a line — исходные "реки" (координаты в исходной системе)
    - exp_pix: целевая ширина результата в пикселях (высота рассчитывается по пропорциям)
    - image_display: объект с методом set_image(PIL.Image)
    - main_layout.progress — QProgressBar (опционально)
    """
    used_colors.clear()
