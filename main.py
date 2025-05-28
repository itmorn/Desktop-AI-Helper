import sys
import os
import threading
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QMenu, 
                            QAction, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, pyqtProperty, QObject, pyqtSlot
from PyQt5.QtGui import QPixmap, QCursor
import speech_recognition as sr
import keyboard
from random import choice

class HotkeyManager(QObject):
    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        
    def setup_hotkeys(self):
        try:
            # 使用 QTimer.singleShot 确保在主线程中执行回调
            keyboard.add_hotkey('ctrl+alt+t', lambda: QTimer.singleShot(0, self.pet.show_text_input), suppress=True)
            # 隐藏快捷键
            keyboard.add_hotkey('ctrl+alt+h', lambda: QTimer.singleShot(0, self.pet.hide_pet), suppress=True)
            # 恢复快捷键
            keyboard.add_hotkey('ctrl+alt+v', lambda: QTimer.singleShot(0, self.pet.start_voice_input_thread), suppress=True)
            # 
            keyboard.add_hotkey('ctrl+alt+r', lambda: QTimer.singleShot(0, self.pet.show_pet), suppress=True)
        except Exception as e:
            print(f"设置快捷键失败: {e}")
            QMessageBox.warning(self.pet, "警告", "无法设置快捷键，请以管理员权限运行程序")

class DesktopPet(QWidget):
    def __init__(self):
        super().__init__()
        
        # 窗口设置
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint | # 始终在最前
            Qt.SubWindow              # 不显示在任务栏
        )
        self.setAttribute(Qt.WA_TranslucentBackground)  # 透明背景
        
        # 宠物形象
        self.pet_label = QLabel(self)
        pixmap = QPixmap("tongtong.png")  # 准备一个透明背景的PNG图片
        # 设置图像大小
        scale_factor = 0.2  # 缩放因子，0.5表示缩小到原来的一半
        scaled_pixmap = pixmap.scaled(
            int(pixmap.width() * scale_factor),
            int(pixmap.height() * scale_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.pet_label.setPixmap(scaled_pixmap)
        self.resize(scaled_pixmap.width(), scaled_pixmap.height())
        
        # 添加动画属性
        self._opacity = 1.0  # 初始透明度
        self.opacity_animation = QPropertyAnimation(self, b"opacity")  # 创建动画对象
        
        # 右键菜单
        self.menu = QMenu(self)
        self.text_action = self.menu.addAction("文字输入")
        self.voice_action = self.menu.addAction("语音输入")
        self.menu.addSeparator()
        self.hide_action = self.menu.addAction("隐藏")
        self.exit_action = self.menu.addAction("退出")
        
        # 连接菜单动作
        self.text_action.triggered.connect(self.show_text_input)
        self.voice_action.triggered.connect(self.start_voice_input_thread)
        self.hide_action.triggered.connect(self.hide_pet)
        self.exit_action.triggered.connect(lambda: (self.close(), sys.exit()))
        
        # 语音识别
        self.recognizer = sr.Recognizer()
        self.is_listening = False
        
        # 设置快捷键管理器
        self.hotkey_manager = HotkeyManager(self)
        QTimer.singleShot(0, self.hotkey_manager.setup_hotkeys)
        
        # 初始化位置
        self.move_to_corner()
        self.dragging = False
        
        # 添加当前消息窗口的跟踪变量
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
        """处理双击事件"""
        if event.button() == Qt.LeftButton:
            greetings = ["你好呀！", "很高兴见到你！", "今天天气真好！", "需要我帮你什么吗？"]
            self.show_message("打招呼", choice(greetings))
    
    @pyqtSlot()
    def show_text_input(self):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("文字输入")
        dialog.setLabelText("请输入指令:")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
        # 显示对话框并设置焦点
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
        # 使用QTimer.singleShot确保在主线程中显示消息
        QTimer.singleShot(0, lambda: self.show_message("语音输入", "正在聆听..."))
        
        def voice_recognition():
            with sr.Microphone() as source:
                print("请说话...")
                try:
                    audio = self.recognizer.listen(source, timeout=5)
                    text = self.recognizer.recognize_google(audio, language='zh-CN')
                    print("识别结果:", text)
                    # 使用QTimer.singleShot确保在主线程中处理结果
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
        
        # 在单独的线程中运行语音识别
        threading.Thread(target=voice_recognition, daemon=True).start()
    
    def process_input(self, text):
        # 这里可以添加LLM处理逻辑
        self.show_message("处理结果", f"已接收: {text}")
        # 示例: 简单的命令识别
        if "隐藏" in text:
            self.hide_pet()
        elif "退出" in text:
            print("退出程序")
            self.close()
            sys.exit()
    
    def show_message(self, title, message):
        # 如果有正在显示的消息，立即关闭它
        if self.current_message is not None and not self.current_message.isHidden():
            self.current_message.close()
            self.current_message = None

        # 创建一个自定义的气泡消息窗口
        msg = QWidget(self)
        self.current_message = msg  # 保存当前消息窗口的引用
        msg.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        msg.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置样式
        msg.setStyleSheet("""
            QWidget {
                background-color: #FFEB3B;  /* 黄色背景 */
                border: 1px solid #FBC02D; /* 边框颜色 */
                border-radius: 10px;       /* 圆角 */
                padding: 10px;
                color: #000;
                font-size: 14px;
            }
        """)
        
        # 创建布局和标签
        from PyQt5.QtWidgets import QVBoxLayout, QLabel
        layout = QVBoxLayout(msg)
        
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setStyleSheet("font-size: 16px;")
        content_label = QLabel(message)
        
        layout.addWidget(title_label)
        layout.addWidget(content_label)
        layout.addStretch()
        
        # 自动调整大小
        msg.setLayout(layout)
        msg.adjustSize()
        
        # 定位在宠物旁边
        pet_rect = self.geometry()
        screen_rect = QApplication.desktop().availableGeometry()
        
        # 尝试在宠物上方显示
        msg_x = pet_rect.x() + (pet_rect.width() - msg.width()) // 2
        msg_y = pet_rect.y() - msg.height() - 10
        
        # 如果超出屏幕，则调整位置
        if msg_y < screen_rect.top():
            msg_y = pet_rect.y() + pet_rect.height() + 10
        if msg_x < screen_rect.left():
            msg_x = screen_rect.left() + 10
        elif msg_x + msg.width() > screen_rect.right():
            msg_x = screen_rect.right() - msg.width() - 10
        
        msg.move(msg_x, msg_y)
        msg.show()
        
        # 3秒后自动消失
        QTimer.singleShot(3000, msg.close)
    
    def hide_pet(self):
        """隐藏宠物"""
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setStartValue(1.0)
        self.opacity_animation.setEndValue(0.0)
        self.opacity_animation.start()
        QTimer.singleShot(500, self.hide)
    
    @pyqtSlot()
    def show_pet(self):
        """恢复显示宠物"""
        if self.isHidden():
            self.show()  # 先显示窗口
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 检查是否已经有实例运行
    existing_instances = [w for w in QApplication.topLevelWidgets() if isinstance(w, DesktopPet)]
    if existing_instances:
        existing_instances[0].show()
        existing_instances[0].activateWindow()
    else:
        pet = DesktopPet()
        pet.show()
    
    sys.exit(app.exec_())