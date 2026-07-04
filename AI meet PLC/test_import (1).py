import os
import sys
import cv2
if "QT_QPA_PLATFORM_PLUGIN_PATH" in os.environ:
    os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread
class T(QThread):
    def run(self):
        c = cv2.VideoCapture(0)
        c.read()
        c.release()

app = QApplication(sys.argv)
t = T()
t.start()
t.wait()
print("Success 2")
