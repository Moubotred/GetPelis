import sys
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from view.main_window import MainWindow
from controller.main_controller import MainController

app = QApplication(sys.argv)
loop = QEventLoop(app)
main_win = MainWindow()
controller = MainController(main_win)
main_win.show()

with loop:
    loop.run_forever()
