from PyQt6.QtWidgets import QSpinBox, QLineEdit


class AutoSelectLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.all_selected = False

    def mouseReleaseEvent(self, evt):
        if self.all_selected:
            self.setCursorPosition(len(self.text()))
            self.all_selected = False
        else:
            self.selectAll()
            self.all_selected = True
        super().mouseReleaseEvent(evt)


class AutoSelectSpinBox(QSpinBox):
    def __init__(self):
        super().__init__()
        self.setLineEdit(AutoSelectLineEdit())