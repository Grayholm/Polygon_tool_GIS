from PyQt6.QtWidgets import QPushButton

def create_button(
    parent_layout,
    label_text: str,
    callback_function
):
    button = QPushButton(label_text)
    button.clicked.connect(callback_function)
    parent_layout.addWidget(button)
    return button