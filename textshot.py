"""

HEAVILY ADAPTED FROM https://github.com/ianzhao05/textshot
USE PERMITTED UNDER MIT LICENSE

Copyright (c) 2020 Ian Zhao

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

"""

import io
import os
import sys
import ctypes, win32con

import pytesseract
from PIL import Image
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)

pytesseract.pytesseract.tesseract_cmd = resource_path(r"tesseract-ocr\tesseract.exe")
user32 = ctypes.windll.user32


class Snipper(QtWidgets.QWidget):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)
        self.setWindowTitle("TextShot")
        self.set_window_flags()
        self._pressed = False
        

    def set_window_flags(self):
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
        )
        self.setWindowState(self.windowState() | Qt.WindowFullScreen)

        dc = int(self.winId())
        user32.SetWindowLongW(dc, win32con.GWL_EXSTYLE, user32.GetWindowLongW(dc, win32con.GWL_EXSTYLE) | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_APPWINDOW)
        
        screen = QtWidgets.QApplication.screenAt(QtGui.QCursor.pos()) # get screen
        self.screen = screen.grabWindow(0) # screenshot
        geom = screen.geometry() # get position of screen
        self.setGeometry(geom.left(), geom.top(), geom.width(), geom.height()) # move window to monitor
        
        
    def run(self):
        self._running = True
        self.set_window_flags() # reset all window flags
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        
        palette = QtGui.QPalette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.screen))
        self.setPalette(palette)
        self.start = self.end = QtCore.QPoint()
        self._pressed = self.result = None
        self.show()
        

    def quit_app(self, canceled=False):
        self._running = False if canceled else None
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.processEvents()
        self.hide()
        # QtWidgets.QApplication.quit()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.quit_app(canceled=True)

        return super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 100))
        painter.drawRect(0, 0, self.width(), self.height())

        if self.start == self.end:
            return super().paintEvent(event)

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3))
        painter.setBrush(painter.background())
        painter.drawRect(QtCore.QRect(self.start, self.end))
        return super().paintEvent(event)


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start = self.end = event.pos()
            self._pressed = True
            self.update()
        elif event.button() == Qt.RightButton:
            if self._pressed:
                self.start = self.end = QtCore.QPoint()
                self.update()
                self._pressed = False
            else:
                self.hide()
                self.quit_app(canceled=True)
        return super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if self._pressed:
            self.end = event.pos()
            self.update()
        return super().mousePressEvent(event)


    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._pressed = False
            
        if self.start == self.end or event.button() != Qt.LeftButton:
            return super().mouseReleaseEvent(event)

        self.hide()
        QtWidgets.QApplication.restoreOverrideCursor()
        QtWidgets.QApplication.processEvents()
        
        shot = self.screen.copy(
            min(self.start.x(), self.end.x()),
            min(self.start.y(), self.end.y()),
            abs(self.start.x() - self.end.x()),
            abs(self.start.y() - self.end.y()),
        )
        self.processImage(shot)
        self.quit_app()
        print('done')


    def processImage(self, img):
        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QBuffer.ReadWrite)
        img.save(buffer, "PNG")
        pil_img = Image.open(io.BytesIO(buffer.data()))
        buffer.close()
    
        try:
            self.result = pytesseract.image_to_string(
                pil_img, lang=(sys.argv[1] if len(sys.argv) > 1 else None)
            ).strip()
        except RuntimeError as error:
            self.result = None
            print(f"ERROR: An error occurred when trying to process the image: {error}")
    
        if self.result:
            print(f'INFO: returned "{self.result}"')
        else:
            print("INFO: Unable to read text from image, did not copy")
    



if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    try:
        pytesseract.get_tesseract_version()
    except EnvironmentError:
        raise (
            "ERROR: Tesseract is either not installed or cannot be reached.\n"
            "Have you installed it and added the install directory to your system path?"
        )

    window = QtWidgets.QMainWindow()
    snipper = Snipper(window)
    snipper.run()
    sys.exit(app.exec_())
