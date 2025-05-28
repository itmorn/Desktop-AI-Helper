import sys
import threading
from PyQt5.QtWidgets import QWidget, QLabel, QMenu, QAction, QInputDialog, QMessageBox, QApplication
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, pyqtSlot
from PyQt5.QtGui import QPixmap, QCursor
import speech_recognition as sr
from random import choice
from .hotkey_manager import HotkeyManager
from .message import show_message

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.pet_label = QLabel(self)
        pixmap = QPixmap("tongtong.png")
        scale_factor = 0.2
        scaled_pixmap = pixmap.scaled(
            int(pixmap.width() * scale_factor),
            int(pixmap.height() * scale_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.pet_label.setPixmap(scaled_pixmap)
        self.resize(scaled_pixmap.width(), scaled_pixmap.height())
        self._opacity = 1.0
        self.opacity_animation = QPropertyAnimation(self, b"opacity")
        self.menu = QMenu(self)
        self.text_action = self.menu.addAction("文字输入")
        self.voice_action = self.menu.addAction("语音输入")
        self.menu.addSeparator()
        self.hide_action = self.menu.addAction("隐藏")
        self.exit_action = self.menu.addAction("退出")
        self.text_action.triggered.connect(self.show_text_input)
        self.voice_action.triggered.connect(self.start_voice_input_thread)
        self.hide_action.triggered.connect(self.hide_pet)
        self.exit_action.triggered.connect(lambda: (self.close(), sys.exit()))
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        self.hotkey_manager = HotkeyManager(self)
        QTimer.singleShot(0, self.hotkey_manager.setup_hotkeys)
        self.move_to_corner()
        self.dragging = False
        self.current_message = None

    def move_to_corner(self):
        screen_rect = QApplication.desktop().availableGeometry()
        x = screen_rect.width() - self.width() - 100
        y = screen_rect.height() - self.height() - 20
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
        elif event.button() == Qt.RightButton:
            self.menu.exec_(QCursor.pos())

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPos() - self.offset)

    def mouseReleaseEvent(self, event):
        self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            greetings = ["你好呀！", "很高兴见到你！", "今天天气真好！", "需要我帮你什么吗？"]
            self.show_message("打招呼", choice(greetings))

    @pyqtSlot()
    def show_text_input(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("文字输入")
        dialog.setLabelText("请输入指令:")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        dialog.show()
        dialog.activateWindow()
        dialog.raise_()
        if dialog.exec_() == QInputDialog.Accepted:
            text = dialog.textValue()
            if text:
                self.process_input(text)

    @pyqtSlot()
    def start_voice_input_thread(self):
        if not self.is_listening:
            QTimer.singleShot(0, self.start_voice_input)

    def start_voice_input(self):
        self.is_listening = True
        QTimer.singleShot(0, lambda: self.show_message("语音输入", "正在聆听..."))
        def voice_recognition():
            with sr.Microphone() as source:
                print("请说话...")
                try:
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio, language='zh-CN')
                    print("识别结果:", text)
                    QTimer.singleShot(0, lambda: self.process_input(text))
                except sr.WaitTimeoutError:
                    QTimer.singleShot(0, lambda: self.show_message("语音输入", "等待超时"))
                except sr.UnknownValueError:
                    QTimer.singleShot(0, lambda: self.show_message("语音输入", "无法识别语音"))
                except sr.RequestError as e:
                    QTimer.singleShot(0, lambda: self.show_message("语音输入错误", f"服务错误: {e}"))
                except Exception as e:
                    QTimer.singleShot(0, lambda: self.show_message("语音输入错误", f"发生错误: {e}"))
                finally:
                    self.is_listening = False
        threading.Thread(target=voice_recognition, daemon=True).start()

    def process_input(self, text):
        self.show_message("处理结果", f"已接收: {text}")
        if "隐藏" in text:
            self.hide_pet()
        elif "退出" in text:
            print("退出程序")
            self.close()
            sys.exit()

    def show_message(self, title, message):
        show_message(self, title, message)

    def hide_pet(self):
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.start()
        QTimer.singleShot(500, self.hide)

    @pyqtSlot()
    def show_pet(self):
        if self.isHidden():
            self.show()
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setStartValue(0.0)
        self.opacity_animation.setEndValue(1.0)
        self.opacity_animation.start()

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(value)

    opacity = pyqtProperty(float, get_opacity, set_opacity)

    @pyqtSlot()
    def show_text_input_at_cursor(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("文字输入")
        dialog.setLabelText("请输入指令:")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        pos = QCursor.pos()
        dialog.move(pos)
        dialog.show()
        dialog.activateWindow()
        dialog.raise_()
        if dialog.exec_() == QInputDialog.Accepted:
            text = dialog.textValue()
            if text:
                self.process_input(text) 