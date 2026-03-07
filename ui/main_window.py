from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QProgressBar, QTabWidget, QVBoxLayout, QWidget
from PyQt6.QtGui import QIntValidator

import config
from logic.province_generator import generate_province_map
from ui.buttons import create_button

from logic.import_module import import_file_of_areas
from ui.image_display import ImageDisplay

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.geo_data = None
        self.pix_seeds = None
        self.line_seeds = None

        # MAIN LAYOUT
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
        main_layout.addWidget(self.label_version)

        # TAB1 LAND IMAGE
        self.land_tab = QWidget()
        land_tab_layout = QVBoxLayout(self.land_tab)
        self.tabs.addTab(self.land_tab, "GIS file")

        # Кнопка для импорта GIS файла, которая вызывает функцию import_file_of_areas при нажатии
        create_button(land_tab_layout,
                      "Import GIS file",
                      lambda: import_file_of_areas(self,
                                           "Import GIS file"))
        
        # TAB2 PROVINCE IMAGE
        self.province_tab = QWidget()
        self.province_image_display = ImageDisplay()
        province_tab_layout = QVBoxLayout(self.province_tab)
        province_tab_layout.addWidget(self.province_image_display)
        self.tabs.addTab(self.province_tab, "Province Image")
        button_row = QHBoxLayout()
        province_tab_layout.addLayout(button_row)

        exp_pix = QLineEdit()
        exp_pix.setPlaceholderText("Введите количество пикселей")  # текст-подсказка
        exp_pix.setValidator(QIntValidator(1, 1000))  # только числа от 1 до 1000

        button_row.addWidget(exp_pix)

        self.button_gen_prov = create_button(province_tab_layout,
                                             "Generate Province Map",
                                             generate_province_map(self, self.pix_seeds, self.line_seeds, exp_pix=exp_pix.text()))