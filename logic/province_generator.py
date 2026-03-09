import numpy as np

from logic.poisson_disc_samples import poisson_disc_samples
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt

used_colors = set()

def generate_province_map(layout, image_display, min_distance):
    """
    Генерация карты провинций с сохранением пропорций исходной области,
    выравниванием размеров провинций по наименьшей найденной провинции и
    крупными провинциями на море.
    - exp_pix: целевая ширина результата в пикселях (высота рассчитывается по пропорциям)
    - image_display: объект с методом set_image(PIL.Image)
    - main_layout.progress — QProgressBar (опционально)
    """
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

    if type(min_distance) is str:
        layout.error_label.setText("Минимальное расстояние должно быть числом!")
        layout.error_label.show()
        return

    layout.error_label.hide()

    # Генерируем заполняющие точки по всей карте
    extra_points = poisson_disc_samples(w, h, min_distance, k=30, seed=42)

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

    fig = voronoi_plot_2d(vor)
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