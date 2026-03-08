from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QProgressBar, QTabWidget, QVBoxLayout, QWidget
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtCore import QLocale

import config
from logic.province_generator import generate_province_map
from ui.buttons import create_button

from logic.import_module import import_file_of_areas
from ui.image_display import ImageDisplay

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.geo_data = None
        self.map_pixels_size = None
        self.pix_seeds = None
        self.line_seeds = None
        self.coastline_seeds = None

        # Главное окно
        self.setWindowTitle(config.TITLE)
        self.setMinimumSize(800, 600)
        self.resize(config.WINDOW_SIZE_WIDTH,
                    config.WINDOW_SIZE_HEIGHT)
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, stretch=1)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        main_layout.addWidget(self.progress)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)

        self.label_version = QLabel("Version "+config.VERSION)
        main_layout.addWidget(self.label_version) # Это внешние отступы внутри вкладки

        # Первая вкладка - импорт GIS файла
        self.land_tab = QWidget()
        land_tab_layout = QVBoxLayout(self.land_tab)
        land_tab_layout.setContentsMargins(20, 20, 20, 20) 
        land_tab_layout.setSpacing(12)

        self.tabs.addTab(self.land_tab, "GIS file") # Это расстояние между элементами внутри

        # Описание
        text = QLabel(
            "Импортируйте GIS файл с населенными пунктами и водными объектами."
        )
        text.setWordWrap(True) # Разрешаем перенос строк
        land_tab_layout.addWidget(text)

        # Блок ввода пикселей
        pix_layout = QHBoxLayout()

        pix_label = QLabel(
            "Размер карты (Отношение пикселей к метру, чем больше значение, тем больше карта):"
        )
        pix_layout.addWidget(pix_label)

        __exp_pix = QLineEdit()
        __exp_pix.setPlaceholderText("Например: 0.01")  # Подсказка

        # Валидатор: min=0.001, max=5, максимум 3 знака после точки
        validator = QDoubleValidator(0.001, 5.0, 3)
        validator.setLocale(QLocale(QLocale.Language.English))  # точка как разделитель
        __exp_pix.setValidator(validator)

        pix_layout.addWidget(__exp_pix)
        pix_layout.addStretch()
        land_tab_layout.addLayout(pix_layout)

        # Кнопка импорта
        create_button(
            land_tab_layout,
            "Import GIS file",
            lambda: import_file_of_areas(self, "Import GIS file", __exp_pix.text())
        )

        # Сообщение об успехе
        self.success_label = QLabel(
            "✓ Файл успешно импортирован. Перейдите во вкладку генерации провинций."
        )

        self.success_label.setStyleSheet("""
            color: #2e7d32;
            font-weight: bold;
        """)

        self.success_label.hide()
        land_tab_layout.addWidget(self.success_label)

        # Растяжка вниз
        land_tab_layout.addStretch()
        
        # Вторая вкладка - генерация карты провинций
        self.province_tab = QWidget()
        self.province_image_display = ImageDisplay()
        province_tab_layout = QVBoxLayout(self.province_tab)
        province_tab_layout.addWidget(self.province_image_display)
        self.tabs.addTab(self.province_tab, "Province Image")
        button_row = QHBoxLayout()
        province_tab_layout.addLayout(button_row)

        self.button_gen_prov = create_button(province_tab_layout,
                                             "Generate Province Map",
                                             lambda: generate_province_map(self, self.pix_seeds, self.line_seeds, __exp_pix.text(), image_display=self.province_image_display))