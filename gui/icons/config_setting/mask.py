from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QColorDialog

from gui.icons.MaskManager import MaskManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Penguin Mask Demo")

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create PenguinMask instance
        self.config_setting_mask = MaskManager(
            'selected.png',  # Replace with your image path
            'mask1.png',  # Replace with your mask1 path
            'mask2.png',  # Replace with your mask2 path
            width=64,
            height=64,
            color1='#FF0000',  # Initial red color
            color2='#0000FF'  # Initial blue color
        )

        layout.addWidget(self.config_setting_mask)

        self.resize(500, 400)

    def change_color1(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.config_setting_mask.set_color1(color.name())

    def change_color2(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.config_setting_mask.set_color2(color.name())


def main():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()