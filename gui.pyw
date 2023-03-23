from tendo.singleton import SingleInstance
me = SingleInstance()

import ctypes
import os
import sys
import time
from ctypes.wintypes import MSG
from threading import Thread, Event
import json
import keyboard
import mouse
import win32api
import win32con
from pyperclip import paste
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QObject, Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from win32api import GetMonitorInfo, MonitorFromPoint
import darkdetect

from tkinter import messagebox
import tkinter as tk
root = tk.Tk()
root.withdraw()

from scraper import Searchify, SearchEngine
from textshot import *
from windoweffect import WindowEffect

user32 = ctypes.windll.user32


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


# workaround for pyqtSignal requiring a QObject parent
class pyqtSignalWrapper(QObject):
    signal = pyqtSignal()


class KeyboardManager:
    hotkeys = {}

    def start(self, label, hotkey):
        self.hotkeys[label] = {'hotkey': hotkey, 'signal': pyqtSignalWrapper()}
        keyboard.add_hotkey(hotkey, self.hotkeys[label]['signal'].signal.emit, suppress=True)
        return self.hotkeys[label]['signal'].signal
    
    def end(self, label):
        if label in self.hotkeys:
            keyboard.remove_hotkey(self.hotkeys[label]['hotkey'])
            del self.hotkeys[label]
    
    def set(self, label, hotkey):
        self.end(label)
        return self.start(label, hotkey)



class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi(resource_path("window.ui"), self)

        self.conf = self.loadjson() # get old config
        self.set_conf_keys()

        self.quizlet_button.setChecked(self.conf['quizlet'])
        self.quizizz_button.setChecked(self.conf['quizizz'])

        self.quizlet_button.toggled.connect(lambda: self.updatejson('quizlet'))
        self.quizizz_button.toggled.connect(lambda: self.updatejson('quizizz'))

        self.settings_button.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))

        # icons
        self.setWindowIcon(QtGui.QIcon(resource_path("img\\search.png")))

        self.quizizz_button.setIcon(QtGui.QIcon(resource_path("img\\quizizz.png")))
        self.quizlet_button.setIcon(QtGui.QIcon(resource_path("img\\quizlet.png")))
        self.titleIcon.setPixmap(QtGui.QPixmap(resource_path("img\\search.png")))

        # SETTINGS PAGE

        # hotkeys
        self.hotkeys = KeyboardManager()
        self.window_shown = True

        self.hide_show_key.setKeySequence(QtGui.QKeySequence.fromString(self.conf['hide_show_key']))
        self.ocr_key.setKeySequence(QtGui.QKeySequence.fromString(self.conf['ocr_key']))
        self.paste_key.setKeySequence(QtGui.QKeySequence.fromString(self.conf['paste_key']))
        self.win_transp_key.setKeySequence(QtGui.QKeySequence.fromString(self.conf['win_transp_key']))
        self.win_trasp_value.setValue(self.conf['win_transp_value'])

        self.win_trasp_value.valueChanged.connect(lambda: self.updatejson('win_transp_value'))

        hide_show_cmd = lambda: self.set_global_hotkey('hide_show_key', self.hide_show_key.keySequence(), self.run_hide_show)
        ocr_cmd       = lambda: self.set_global_hotkey('ocr_key', self.ocr_key.keySequence(), lambda: self.run_ocr_tool(True))
        paste_cmd     = lambda: self.set_global_hotkey('paste_key', self.paste_key.keySequence(), lambda: self.paste_text(True))
        win_trasp_cmd = lambda: self.set_global_hotkey('win_transp_key', self.win_transp_key.keySequence(), lambda: self.transp_slider.setValue(self.win_trasp_value.value()))

        self.hide_show_key.editingFinished.connect(hide_show_cmd)
        self.ocr_key.editingFinished.connect(ocr_cmd)
        self.paste_key.editingFinished.connect(paste_cmd)
        self.win_transp_key.editingFinished.connect(win_trasp_cmd)

        hide_show_cmd()
        ocr_cmd()
        paste_cmd()
        win_trasp_cmd()

        # clear hotkey
        self.hide_show_key_clear.clicked.connect(lambda: [x() for x in [self.hide_show_key.clear, hide_show_cmd]])
        self.ocr_key_clear.clicked.connect(lambda: [x() for x in [self.ocr_key.clear, ocr_cmd]])
        self.paste_key_clear.clicked.connect(lambda: [x() for x in [self.paste_key.clear, paste_cmd]])
        self.win_transp_key_clear.clicked.connect(lambda: [x() for x in [self.win_transp_key.clear, win_trasp_cmd]])

        # checks
        self.setting_search_ocr.setChecked(self.conf['search_ocr'])
        self.setting_search_ocr.toggled.connect(lambda: self.updatejson('search_ocr'))

        self.setting_search_paste.setChecked(self.conf['search_paste'])
        self.setting_search_paste.toggled.connect(lambda: self.updatejson('search_paste'))

        self.setting_hide_taskbar.setChecked(self.conf['hide_taskbar'])
        self.setting_hide_taskbar.toggled.connect(lambda: self.set_hide_taskbar())
        
        self.setting_hide_window.setChecked(self.conf['hide_window'])
        self.setting_hide_window.toggled.connect(lambda: self.set_hide_window())

        if self.conf['save_focus'] != None:
            self.setting_save_focus.setChecked(True)
            self.toggle_noactive.setChecked(self.conf['save_focus'])
        self.setting_save_focus.toggled.connect(lambda: self.updatejson('save_focus'))

        if self.conf['save_transp']:
            self.setting_save_transp.setChecked(True)
            self.transp_slider.setValue(self.conf['save_transp'])
            self.setWindowOpacity(self.conf['save_transp'] / 100)

        self.setting_save_transp.toggled.connect(lambda: self.updatejson('save_transp'))
        self.transp_slider.sliderReleased.connect(lambda: self.updatejson('save_transp'))

        self.setting_rightclick_reset.setChecked(self.conf['rclick_reset'])
        self.setting_rightclick_reset.toggled.connect(lambda: self.updatejson('rclick_reset'))

        self.setting_on_top.setChecked(self.conf['on_top'])
        self.setting_on_top.toggled.connect(lambda: self.set_window_on_top())
        
        self.search_engine_combo = self.findChild(QtWidgets.QComboBox, "search_engine_combo")
        self.search_engine_combo.setCurrentIndex(self.conf['search_engine'])
        self.search_engine = SearchEngine(self.search_engine_combo.currentText().lower())
        self.search_engine_combo.currentIndexChanged.connect(lambda: self.run_search_engine())

        # window theme
        self.themeInput.setCurrentIndex(self.conf['theme'])
        self.font_size.setValue(self.conf['font_size'])
        
        self.themeInput.currentIndexChanged.connect(self.set_window_theme)
        self.font_size.valueChanged.connect(self.set_window_theme)

        # exit settings
        self.back_label.mousePressEvent = lambda x: self.stackedWidget.setCurrentIndex(0) if x.button() == Qt.LeftButton else None
        self.back_button.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))

        # search bar events
        self.search_bar.focusInEvent = self.search_bar_focus_in
        self.search_bar.focusOutEvent = self.search_bar_focus_out
        self._modifiers = QtCore.Qt.KeyboardModifiers()
        self._bar_thread = self._bar_thread_end = None

        # set connections
        self.search_bar.returnPressed.connect(self.run_searcher)
        self.toggle_noactive.toggled.connect(lambda x: self.active_button_toggle(x))
        self.close_button.clicked.connect(sys.exit)
        self.minimize_button.clicked.connect(lambda: self.setWindowState(QtCore.Qt.WindowMinimized))
        self.transp_slider.valueChanged.connect(lambda: self.set_window_opacity())
        self.ocr_button.clicked.connect(self.run_ocr_tool)
        self.paste_button.clicked.connect(self.paste_text)
        self.search_button.clicked.connect(self.run_searcher)

        # set column width
        self.treeWidget.setColumnWidth(1, 250)

        self.windowEffect = WindowEffect()
        self.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)

        if self.setting_on_top.isChecked(): # fix white flash on start
            self.setWindowFlags(Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        else:
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        
        self.windowEffect.addWindowAnimation(self.winId())
        self.windowEffect.addShadowEffect(self.winId())

        if self.conf['save_pos']:
            self.setting_save_pos.setChecked(True)
            _geo = self.conf['save_pos']
            self.setGeometry(_geo[0], _geo[1], _geo[2], _geo[3])
            self.setting_save_pos.toggled.connect(lambda: self.updatejson('save_pos'))
        else:
            self.set_window_geometry()
        self.set_window_opacity()
        self.set_window_theme()
        self.dc = int(self.winId())
        self.set_hide_taskbar()

        self.active_button_toggle(self.toggle_noactive.isChecked())

        self._pressed = False

        # show ui
        self.show()
    
    # search bar keyboard listener
    
    def search_bar_focus_in(self, event):
        # create thread to listen for keyboard events
        if self.toggle_noactive.isChecked():
            self._bar_thread_end = Event()
            self._bar_thread = Thread(target=self.search_bar_listener, daemon=True)
            self._bar_thread.start()
        super(QtWidgets.QLineEdit, self.search_bar).focusInEvent(event)
    
    def search_bar_listener(self):
        # hacky method to activate cursor
        for key, mod in ((QtCore.Qt.Key_Left, QtCore.Qt.ShiftModifier), (QtCore.Qt.Key_Right, QtCore.Qt.NoModifier)):
            QtWidgets.QApplication.postEvent(self.search_bar,
                QtGui.QKeyEvent(QtGui.QKeyEvent.KeyPress, key, mod, text=''))
        # listen for keyboard events, and forward them to the search bar
        mouse_hook = mouse.on_click(
            lambda: None
            if self.geometry().contains(QtGui.QCursor.pos())
            else self.search_bar.clearFocus()
        )
        hook = keyboard.hook(self.search_bar_keypress, suppress=True)
        self._bar_thread_end.wait()
        keyboard.unhook(hook)
        mouse.unhook(mouse_hook)
        
    scan_code_map = {
        75: QtCore.Qt.Key_Left,
        77: QtCore.Qt.Key_Right,
        14: QtCore.Qt.Key_Backspace,
        57: QtCore.Qt.Key_Space,
        71: QtCore.Qt.Key_Home,
        79: QtCore.Qt.Key_End,
        83: QtCore.Qt.Key_Delete,
        28: QtCore.Qt.Key_Return,
    }
    modifier_map = {
        29: QtCore.Qt.ControlModifier,
        42: QtCore.Qt.ShiftModifier,
        56: QtCore.Qt.AltModifier,
    }
    key_exceptions = {58, 69}
    
    def search_bar_keypress(self, key: keyboard.KeyboardEvent):
        # send the keypress to the self.search_bar
        if key.scan_code in self.modifier_map:
            if key.event_type == 'down':
                self._modifiers = self._modifiers | self.modifier_map[key.scan_code]
            else:
                self._modifiers = self._modifiers & ~self.modifier_map[key.scan_code]
            return
        # exempt select keys
        if key.scan_code in self.key_exceptions:
            if key.event_type == 'down':
                keyboard.press(key.scan_code)
            else:
                keyboard.release(key.scan_code)
            return
        # exit on meta key
        elif key.scan_code == 91:
            self.search_bar.clearFocus()
            return
        # ignore None events
        elif not key.name:
            return
        # handle ctrl+a
        elif key.scan_code == 30 and self._modifiers & QtCore.Qt.ControlModifier:
            self.search_bar.selectAll()
            return
            
        scan_code = self.scan_code_map.get(key.scan_code, key.scan_code)
        keypress = QtGui.QKeyEvent(
            {'up': QtGui.QKeyEvent.KeyRelease, 'down': QtGui.QKeyEvent.KeyPress}[key.event_type],
            scan_code,
            self._modifiers,
            text=key.name if len(key.name) == 1 else ' ' if key.name == 'space' else '',
        )
        # print(keypress.key(), key.scan_code, key.event_type, key.is_keypad, self._modifiers)
        # send the keypress to the search bar
        QtWidgets.QApplication.postEvent(self.search_bar, keypress)
        
    def search_bar_focus_out(self, event):
        # kill thread
        if self._bar_thread and self._bar_thread.is_alive():
            self._bar_thread_end.set()
            self._bar_thread.join()
        super(QtWidgets.QLineEdit, self.search_bar).focusOutEvent(event)
    
    # setting window attributes
    
    def set_window_opacity(self):
        self.setWindowOpacity(self.transp_slider.value() / 100)

    def set_window_geometry(self):
        cursor = QtGui.QCursor.pos()
        
        area = GetMonitorInfo(MonitorFromPoint((cursor.x(), cursor.y())))
        work = area.get('Work')
        if not work:
            screen = QtWidgets.QApplication.screenAt(cursor).geometry() # get screen
            work = (screen.width(), screen.height())
        else:
            work = (work[2], work[3])

        geo = self.geometry()
        geo.moveBottomRight(QtCore.QPoint(work[0], work[1]))
        self.setGeometry(geo.left(), geo.top(), geo.width(), geo.height())

    def set_window_theme(self):
        theme = self.themeInput.currentIndex()
        font_size = self.font_size.value()

        # icon sizes
        for obj in [self.quizizz_button, self.quizlet_button]:
            obj.setIconSize(QtCore.QSize(font_size*2, font_size*2))

        if theme == 2 or (DARK_MODE and not theme): # dark
            app.setPalette(dark_palette)
            self.titleBar.setPalette(dark_titleBar_palette)
        else: # light themes
            app.setPalette(light_palette)
            self.titleBar.setPalette(light_titleBar_palette)
            if theme == 3: # win32 theme
                app.setStyle('windowsvista')
                self.setFont(QtGui.QFont('Segoe UI', font_size))
                return
        app.setStyle('Fusion')
        self.setFont(QtGui.QFont('Poppins Medium', font_size))

        self.updatejson('theme')
        self.updatejson('font_size')

    # calling scraper and adding to ui
    
    def run_search_engine(self):
        self.search_engine = SearchEngine(self.search_engine_combo.currentText().lower())
        self.updatejson('search_engine')
    
    def run_searcher(self):
        query = self.search_bar.text().strip()

        if not query:
            self.status_label.setText('Please enter a search query')
            return

        self.status_label.setText('Searching...')
        self.search_frame.setEnabled(False)
        QtWidgets.QApplication.processEvents()

        sites = []

        if self.quizizz_button.isChecked(): sites.append('quizizz')
        if self.quizlet_button.isChecked(): sites.append('quizlet')

        if not sites:
            self.status_label.setText('Please select at least one site.')
            self.search_frame.setEnabled(True)
            return
        
        searchify = Searchify(query, sites, self.search_engine)

        t = Thread(target=searchify.main)
        t.daemon = True
        t.start()
        while t.is_alive():
            self.status_label.setText(f'Searching... {round(time.time() - searchify.timer.elapsed_total, 1)}s')
            QtWidgets.QApplication.processEvents()
        
        fc_count = len(searchify.flashcards)
        self.status_label.setText(f'{fc_count} result{"" if fc_count == 1 else "s"} found ({round(searchify.stop_time, 2)}s)')
        self.search_frame.setEnabled(True)
        self.add_to_tree(searchify.flashcards)

    def add_to_tree(self, flashcards):
        self.treeWidget.clear()
        for card in flashcards:
            item = QtWidgets.QTreeWidgetItem(self.treeWidget, ['']*3)
            labels = [
                QtWidgets.QLabel(card['similarity']),
                QtWidgets.QLabel(card['question']),
                QtWidgets.QLabel(card['answer'])
            ]
            for col in range(3):
                labels[col].setWordWrap(True)
                labels[col].setMargin(5)
                labels[col].setFrameShape(QtWidgets.QFrame.StyledPanel)
                labels[col].setFrameShadow(QtWidgets.QFrame.Plain)
                labels[col].setLineWidth(1)
                labels[col].setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
                self.treeWidget.setItemWidget(item, col, labels[col])

    # data entry tools
    
    def run_ocr_tool(self, force_run_searcher=False):
        if not check_tesseract_paths():
            self.status_label.setText('Tesseract not found.')
            return

        self.status_label.setText('OCR in progress...')
        QtWidgets.QApplication.processEvents()

        self.setWindowOpacity(0)
        self.stackedWidget.setCurrentIndex(0)
        QtWidgets.QApplication.processEvents()

        window = QtWidgets.QMainWindow()
        snipper = Snipper(window)
        snipper.run()

        self.set_window_opacity()
        
        while snipper._running:
            QtWidgets.QApplication.processEvents()
        r = snipper.result
        if r:
            self.search_bar.setText(' '.join(r.split()))
            self.status_label.setText('OCR complete.')
            if force_run_searcher or self.setting_search_ocr.isChecked():
                self.run_searcher()
        elif snipper._running is None:
            self.status_label.setText('OCR failed.')
        else:
            self.status_label.setText('OCR cancelled.')
    
    def paste_text(self, force_run_searcher=False):
        self.search_bar.setText(' '.join(paste().split()))
        self.stackedWidget.setCurrentIndex(0)
        if force_run_searcher or self.setting_search_paste.isChecked():
            self.run_searcher()

    # global hotkeys

    def run_hide_show(self):
        if self.window_shown:
            self.hide(); self.window_shown = False
        else:
            self.show(); self.window_shown = True

    def set_global_hotkey(self, label, keysequence, cmd):
        self.updatejson(label)
        if keysequence.isEmpty():
            self.hotkeys.end(label)
            return
        self.hotkeys.set(label, keysequence.toString()).connect(cmd)

    # moving/resizing window

    BORDER_WIDTH = 5    # border for resizing window
    def nativeEvent(self, eventType, message):
        """ Handle the Windows message """
        msg = MSG.from_address(message.__int__())
        if msg.message == win32con.WM_NCHITTEST:
            xPos = (win32api.LOWORD(msg.lParam) -
                    self.frameGeometry().x()) % 65536
            yPos = win32api.HIWORD(msg.lParam) - self.frameGeometry().y()
            w, h = self.width(), self.height()
            lx = xPos < self.BORDER_WIDTH
            rx = xPos + 9 > w - self.BORDER_WIDTH
            ty = yPos < self.BORDER_WIDTH
            by = yPos > h - self.BORDER_WIDTH
            if lx and ty:
                return True, win32con.HTTOPLEFT
            elif rx and by:
                return True, win32con.HTBOTTOMRIGHT
            elif rx and ty:
                return True, win32con.HTTOPRIGHT
            elif lx and by:
                return True, win32con.HTBOTTOMLEFT
            elif ty:
                return True, win32con.HTTOP
            elif by:
                return True, win32con.HTBOTTOM
            elif lx:
                return True, win32con.HTLEFT
            elif rx:
                return True, win32con.HTRIGHT
        elif msg.message == win32con.WM_NCCALCSIZE:
            return True, 0

        return QMainWindow.nativeEvent(self, eventType, message)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
            self._pressed = True
            # QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))
        elif event.button() == Qt.RightButton and self.setting_rightclick_reset.isChecked():
            self.set_window_geometry()
            self._pressed = False
        self.updatejson('save_pos')
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pressed:
            delta = QtCore.QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()
        return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        # QtWidgets.QApplication.restoreOverrideCursor()
        return super().mouseReleaseEvent(event)
    
    # window switch safety lock

    def active_button_toggle(self, x):
        if x:
            self.set_noactive_style()
        else:
            self.remove_noactive_style() 
        # set placeholder text om lineEdit
        self.search_bar.setPlaceholderText('Type a question here (Window focus safety ON)' if x else 'Type a question here')
        self._bar_thread_end and self._bar_thread_end.set()  # end safety lock typing thread
        # hide minimize button
        self.minimize_button.setVisible(not (x or self.setting_hide_taskbar.isChecked()))
        self.updatejson('save_focus')
        self.set_window_on_top()
        self.setFocus(x)

    def set_noactive_style(self):
        user32.SetWindowLongW(self.dc, win32con.GWL_EXSTYLE, user32.GetWindowLongW(self.dc, win32con.GWL_EXSTYLE) | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_APPWINDOW)
    
    def remove_noactive_style(self):
        # removes win32con.WS_EX_NOACTIVATE
        user32.SetWindowLongW(self.dc, win32con.GWL_EXSTYLE, user32.GetWindowLongW(self.dc, win32con.GWL_EXSTYLE) & ~win32con.WS_EX_NOACTIVATE)

    # toggle always on top

    def set_hide_window(self):
        self.set_window_affinity()
        self.updatejson('hide_window')

    def set_window_affinity(self):
        if self.setting_hide_window.isChecked():
            ctypes.windll.user32.SetWindowDisplayAffinity(self.dc, 0x11)
        else:
            ctypes.windll.user32.SetWindowDisplayAffinity(self.dc, 0)

    def set_window_on_top(self):
        if self.setting_on_top.isChecked() or self.toggle_noactive.isChecked():
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.updatejson('on_top')
        self.windowEffect.addWindowAnimation(self.winId()) # add back animation
        ctypes.windll.user32.SetWindowDisplayAffinity(self.dc, 0x11)
        self.set_window_affinity()
        self.show()

    def set_hide_taskbar(self):
        if self.setting_hide_taskbar.isChecked():
            self.setWindowFlags(self.windowFlags() | Qt.Tool)
            self.minimize_button.setVisible(False)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.Tool)
            self.minimize_button.setVisible(not self.toggle_noactive.isChecked())
        self.updatejson('hide_taskbar')
        self.set_window_affinity()
        self.show()

    # saving/opening config

    def set_conf_keys(self):
        self.conf_keys = {
            # keybinds
            "quizlet":         lambda: self.quizlet_button.isChecked(),
            "quizizz":         lambda: self.quizizz_button.isChecked(),
            "hide_show_key":   lambda: self.hide_show_key.keySequence().toString(),
            "ocr_key":         lambda: self.ocr_key.keySequence().toString(),
            "paste_key":       lambda: self.paste_key.keySequence().toString(),
            "win_transp_key":  lambda: self.win_transp_key.keySequence().toString(),
            "win_transp_value": lambda: self.win_trasp_value.value(),
            "search_ocr":      lambda: self.setting_search_ocr.isChecked(),
            "search_paste":    lambda: self.setting_search_paste.isChecked(),
            "save_focus":      lambda: self.toggle_noactive.isChecked() if self.setting_save_focus.isChecked() else None,
            "save_transp":     lambda: self.transp_slider.value() if self.setting_save_transp.isChecked() else None,
            "save_pos":        lambda: (self.geometry().left(),
                                        self.geometry().top(),
                                        self.geometry().width(),
                                        self.geometry().height()
                                    ) if self.setting_save_pos.isChecked() else None,
            "rclick_reset":    lambda: self.setting_rightclick_reset.isChecked(),
            "on_top":          lambda: self.setting_on_top.isChecked(),
            "hide_taskbar":    lambda: self.setting_hide_taskbar.isChecked(),
            "hide_window":     lambda: self.setting_hide_window.isChecked(),
            "theme":           lambda: self.themeInput.currentIndex(),
            "font_size":       lambda: self.font_size.value(),
            "search_engine":   lambda: self.search_engine_combo.currentIndex(),
        }

    def updatejson(self, key):
        data = self.loadjson()
        with open(resource_path('config.json'), 'w') as f:
            data[key] = self.conf_keys[key]()
            json.dump(data, f, ensure_ascii=False, indent=4)

    def loadjson(self):
        with open(resource_path('config.json'), 'r') as f:
            return json.load(f)


# initialize app
QtCore.QCoreApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
app = QApplication(sys.argv)
QtGui.QFontDatabase.addApplicationFont(resource_path('fonts\\Poppins Medium.ttf'))

# color palettes
DARK_MODE = darkdetect.isDark()

light_palette           = QtGui.QPalette()

light_titleBar_palette  = QtGui.QPalette()
light_titleBar_palette.setColor(QtGui.QPalette.Window, QtCore.Qt.white)

dark_palette = QtGui.QPalette()
dark_palette.setColor(QtGui.QPalette.Window, QtGui.QColor(25,35,45))
dark_palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
dark_palette.setColor(QtGui.QPalette.Base, QtGui.QColor(39, 49, 58))
dark_palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(25,35,45))
dark_palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
dark_palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
dark_palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
dark_palette.setColor(QtGui.QPalette.Button, QtGui.QColor(25,35,45))
dark_palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
dark_palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.blue)
dark_palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(20, 129, 216))
dark_palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)

dark_titleBar_palette   = QtGui.QPalette()
dark_titleBar_palette.setColor(QtGui.QPalette.Window, (QtGui.QColor(28, 38, 48)))


MainWindow = QtWidgets.QMainWindow()

try:
    window = UI()
    app.exec_()
except Exception as e:
    messagebox.showerror('SearchifyX - Error', str(e))

sys.exit()