# -*- coding: utf-8 -*-
"""
主窗口 — 搜索栏 + 卡片列表滚动区
"""

import os
import io
import customtkinter as ctk
import win32clipboard
from PIL import Image as PILImage

from .card_widget import ClipboardCard


class MainWindow(ctk.CTk):
    """剪贴板历史主窗口"""

    WIDTH = 420
    HEIGHT = 600
    MIN_WIDTH = 360
    MIN_HEIGHT = 400

    def __init__(self, storage, on_open_settings=None):
        super().__init__()

        self.storage = storage
        self.on_open_settings = on_open_settings
        self.cards = []  # 当前显示的卡片组件列表
        self._monitor = None  # 剪贴板监听器引用（由 main.py 设置）

        # 窗口配置
        self.title("历史粘贴板")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # 设置关闭行为：隐藏而非退出
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._build_toolbar()
        self._build_card_area()

    # ------------------------------------------------------------------
    # 工具栏
    # ------------------------------------------------------------------

    def _build_toolbar(self):
        """顶部工具栏：搜索框 + 设置按钮"""
        toolbar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        toolbar.pack(fill="x", padx=10, pady=(10, 4))
        toolbar.pack_propagate(False)

        # 搜索框
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._on_search())

        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="搜索历史内容...",
            textvariable=self.search_var,
            font=ctk.CTkFont(size=13),
            height=34,
            border_color="#90CAF9",
            fg_color="#FFFFFF",
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        # 设置按钮
        settings_btn = ctk.CTkButton(
            toolbar,
            text="⚙",
            width=36,
            height=34,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color="#E3F2FD",
            text_color="#42A5F5",
            command=self._on_settings,
        )
        settings_btn.pack(side="right")

    # ------------------------------------------------------------------
    # 卡片区域
    # ------------------------------------------------------------------

    def _build_card_area(self):
        """可滚动卡片列表"""
        self.card_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#BBDEFB",
            scrollbar_button_hover_color="#90CAF9",
        )
        self.card_scroll.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        # 空状态提示
        self.empty_label = ctk.CTkLabel(
            self.card_scroll,
            text="暂无剪贴板历史\n\n复制一段文字或截图试试吧 ✨",
            font=ctk.CTkFont(size=14),
            text_color="#888888",
        )

    # ------------------------------------------------------------------
    # 数据刷新
    # ------------------------------------------------------------------

    def refresh(self):
        """刷新卡片列表（从数据库重新加载）"""
        # 清除旧卡片
        for card in self.cards:
            card.destroy()
        self.cards.clear()

        search = self.search_var.get().strip() if hasattr(self, "search_var") else None
        records = self.storage.get_records(search=search)

        if not records:
            self.empty_label.pack(pady=60)
        else:
            self.empty_label.pack_forget()

        for rec in records:
            card = ClipboardCard(
                self.card_scroll,
                rec,
                on_copy=self._do_copy,
                on_pin=self._do_pin,
                on_delete=self._do_delete,
            )
            card.pack(fill="x", pady=(0, 8))
            self.cards.append(card)

    def set_monitor(self, monitor):
        """绑定剪贴板监听器，有新记录时自动刷新"""
        self._monitor = monitor
        monitor.on_new_record = self._on_new_record_from_monitor

    def _on_new_record_from_monitor(self, record):
        """监听器回调：在主线程刷新 UI"""
        self.after(100, self.refresh)

    # ------------------------------------------------------------------
    # 用户操作
    # ------------------------------------------------------------------

    def _on_search(self):
        """搜索框内容变化"""
        self.refresh()

    def _on_settings(self):
        """打开设置"""
        if self.on_open_settings:
            self.on_open_settings()

    def _do_copy(self, record):
        """复制记录到剪贴板"""
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            try:
                if record["type"] == "text":
                    win32clipboard.SetClipboardText(record["content"])
                elif record["type"] == "image":
                    img_path = record.get("image_path", "")
                    if img_path and os.path.exists(img_path):
                        img = PILImage.open(img_path)
                        # 转换为 BMP 写入剪贴板
                        output = io.BytesIO()
                        img.convert("RGB").save(output, format="BMP")
                        data = output.getvalue()[14:]  # 去掉 BMP 文件头
                        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            pass

    def _do_pin(self, record):
        """切换置顶"""
        new_state = self.storage.toggle_pin(record["id"])
        if new_state is not None:
            record["pinned"] = new_state
            self.refresh()

    def _do_delete(self, record):
        """删除记录"""
        self.storage.delete_record(record["id"])
        self.refresh()

    # ------------------------------------------------------------------
    # 窗口显隐
    # ------------------------------------------------------------------

    def show_window(self):
        """显示并提到最前"""
        self.deiconify()
        self.lift()
        self.focus_force()
        self.refresh()

    def hide_window(self):
        """隐藏窗口（缩回托盘）"""
        self.withdraw()
