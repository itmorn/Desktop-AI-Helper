import time
from PyQt5.QtCore import QTimer, QObject
from PyQt5.QtWidgets import QMessageBox, QApplication
import keyboard

class HotkeyManager(QObject):
    def __init__(self, pet):
        super().__init__()
        self.pet = pet
        self.last_ctrl_time = 0
        self.ctrl_count = 0
        self.ctrl_timer = None
        
    def setup_hotkeys(self):
        try:
            # 使用 QTimer.singleShot 确保在主线程中执行回调
            keyboard.add_hotkey('ctrl+alt+t', lambda: QTimer.singleShot(0, self.pet.show_text_input), suppress=True)
            # 隐藏
            keyboard.add_hotkey('ctrl+alt+h', lambda: QTimer.singleShot(0, self.pet.hide_pet), suppress=True)
            # 开始语音
            keyboard.add_hotkey('ctrl+alt+v', lambda: QTimer.singleShot(0, self.pet.start_voice_input_thread), suppress=True)
            # 恢复
            keyboard.add_hotkey('ctrl+alt+r', lambda: QTimer.singleShot(0, self.pet.show_pet), suppress=True)
            # 退出
            keyboard.add_hotkey('ctrl+alt+q', lambda: QTimer.singleShot(0, self.quit_app), suppress=True)
            # 光标处显示框
            keyboard.on_release_key('ctrl', self.on_ctrl_release, suppress=False)
        except Exception as e:
            print(f"设置快捷键失败: {e}")
            QMessageBox.warning(self.pet, "警告", "无法设置快捷键，请以管理员权限运行程序")

    def on_ctrl_release(self, e):
        now = time.time()
        if now - self.last_ctrl_time < 0.5:  # 0.5秒内双击
            self.ctrl_count += 1
        else:
            self.ctrl_count = 1
        self.last_ctrl_time = now
        if self.ctrl_count == 2:
            self.ctrl_count = 0
            QTimer.singleShot(0, self.pet.show_text_input_at_cursor) 

    def quit_app(self):
        print("退出应用")
        app = QApplication.instance()
        if app is not None:
            app.quit()
        else:
            print("QApplication instance is None") 