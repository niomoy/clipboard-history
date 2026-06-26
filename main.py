# -*- coding: utf-8 -*-
"""
历史粘贴板 — 入口文件
启动系统托盘 + 剪贴板监听 + 主窗口
"""

import os
import sys
import threading
from pathlib import Path

from PIL import Image as PILImage
import pystray

from storage import Storage
from clipboard_monitor import ClipboardMonitor
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow


# 资源路径（兼容开发模式和打包后的路径）
def get_asset_path(filename):
    """获取资源文件路径（兼容 PyInstaller 打包）"""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", filename)


class ClipboardApp:
    """应用主控制器"""

    def __init__(self):
        self.storage = Storage()
        self.monitor = ClipboardMonitor(self.storage)
        self.window = None  # 主窗口，延迟创建
        self.tray = None

    def run(self):
        """启动应用"""
        # 启动剪贴板监听
        self.monitor.start()

        # 启动时执行一次过期清理
        self.storage.cleanup_expired()

        # 在后台线程启动系统托盘
        tray_thread = threading.Thread(target=self._run_tray, daemon=True)
        tray_thread.start()

        # 延迟创建主窗口（customtkinter 必须在主线程创建）
        self.window = MainWindow(
            self.storage,
            on_open_settings=self._open_settings,
        )
        self.window.set_monitor(self.monitor)

        # 默认隐藏，从托盘打开
        # self.window.show_window()  # 如果要在启动时显示，取消注释

        # 主循环（阻塞）
        self.window.mainloop()

    # ------------------------------------------------------------------
    # 系统托盘
    # ------------------------------------------------------------------

    def _run_tray(self):
        """在后台线程运行系统托盘"""
        icon_path = get_asset_path("icon.png")

        if os.path.exists(icon_path):
            icon_img = PILImage.open(icon_path)
        else:
            # 后备：创建一个纯色图标
            icon_img = PILImage.new("RGB", (64, 64), "#42A5F5")

        menu = pystray.Menu(
            pystray.MenuItem("打开面板", self._tray_show, default=True),
            pystray.MenuItem("设置", self._tray_settings),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._tray_quit),
        )

        self.tray = pystray.Icon(
            "clipboard_history",
            icon_img,
            "历史粘贴板",
            menu,
        )

        # 左键单击也打开面板
        self.tray.run()

    def _tray_show(self, icon=None, item=None):
        """托盘：打开主面板"""
        if self.window:
            self.window.after(0, self.window.show_window)

    def _tray_settings(self, icon=None, item=None):
        """托盘：打开设置"""
        if self.window:
            self.window.after(0, self._open_settings)

    def _tray_quit(self, icon=None, item=None):
        """托盘：退出"""
        self.monitor.stop()
        if self.tray:
            self.tray.stop()
        if self.window:
            self.window.after(0, self.window.destroy)

    # ------------------------------------------------------------------
    # 设置窗口
    # ------------------------------------------------------------------

    def _open_settings(self):
        """打开设置窗口"""
        SettingsWindow(self.window, self.storage)


# ------------------------------------------------------------------
# 入口
# ------------------------------------------------------------------

if __name__ == "__main__":
    app = ClipboardApp()
    app.run()
