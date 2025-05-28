from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor

def show_message(parent, title, message):
    # 如果有正在显示的消息，立即关闭它
    if hasattr(parent, 'current_message') and parent.current_message is not None and not parent.current_message.isHidden():
        parent.current_message.close()
        parent.current_message = None

    # 创建一个自定义的气泡消息窗口
    msg = QWidget(parent)
    parent.current_message = msg  # 保存当前消息窗口的引用
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
    layout = QVBoxLayout(msg)
    title_label = QLabel(f"<b>{title}</b>")
    title_label.setStyleSheet("font-size: 16px;")
    content_label = QLabel(message)
    layout.addWidget(title_label)
    layout.addWidget(content_label)
    layout.addStretch()
    msg.setLayout(layout)
    msg.adjustSize()
    
    # 定位在宠物旁边
    pet_rect = parent.geometry()
    screen_rect = QApplication.desktop().availableGeometry()
    msg_x = pet_rect.x() + (pet_rect.width() - msg.width()) // 2
    msg_y = pet_rect.y() - msg.height() - 10
    if msg_y < screen_rect.top():
        msg_y = pet_rect.y() + pet_rect.height() + 10
    if msg_x < screen_rect.left():
        msg_x = screen_rect.left() + 10
    elif msg_x + msg.width() > screen_rect.right():
        msg_x = screen_rect.right() - msg.width() - 10
    msg.move(msg_x, msg_y)
    msg.show()
    QTimer.singleShot(3000, msg.close) 