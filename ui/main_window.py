# -*- coding: utf-8 -*-
"""
主窗口 — 毛玻璃质感：Windows Acrylic 模糊背景 + 悬浮卡片
"""

import os
import io
import customtkinter as ctk
import win32clipboard
from PIL import Image as PILImage

from .card_widget import ClipboardCard


class MainWindow(ctk.CTk):
    """剪贴板历史主窗口（毛玻璃款）"""

    WIDTH  = 440
    HEIGHT = 640
    MIN_WIDTH  = 380
    MIN_HEIGHT = 440

    # 窗口底色 — 柔和雾白，卡片悬浮其上模拟毛玻璃层次
    WINDOW_BG = "#EAEEF2"

    def __init__(self, storage, on_open_settings=None):
        super().__init__()

        self.storage = storage
        self.on_open_settings = on_open_settings
        self.cards = []
        self._monitor = None

        # 窗口配置
        self.title("历史粘贴板")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.configure(fg_color=self.WINDOW_BG)

        # 关闭 → 隐藏到托盘
        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._build_toolbar()
        self._build_card_area()

    # ──────────────────────────────────────────────────────────────
    #  工具栏
    # ──────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        """顶部工具栏：搜索框 + 设置按钮"""
        toolbar = ctk.CTkFrame(self, fg_color="transparent", height=44)
        toolbar.pack(fill="x", padx=12, pady=(12, 4))
        toolbar.pack_propagate(False)

        # 搜索框 — 白色半透感
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._on_search())

        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="搜索历史内容...",
            textvariable=self.search_var,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            height=36,
            corner_radius=18,
            border_color="#D1D5DB",
            fg_color="#FFFFFF",
            text_color="#2C2C2E",
            placeholder_text_color="#8E8E93",
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        # 双保险：trace + 按键事件
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        # 设置按钮
        settings_btn = ctk.CTkButton(
            toolbar,
            text="⚙",
            width=38,
            height=36,
            font=ctk.CTkFont(size=18),
            fg_color="transparent",
            hover_color="#E5E7EB",
            text_color="#8E8E93",
            corner_radius=18,
            command=self._on_settings,
        )
        settings_btn.pack(side="right")

    # ──────────────────────────────────────────────────────────────
    #  卡片区域
    # ──────────────────────────────────────────────────────────────

    def _build_card_area(self):
        """可滚动的毛玻璃卡片列表"""
        self.card_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color="#CCD0D5",
            scrollbar_button_hover_color="#A0A5AA",
        )
        self.card_scroll.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        # 空状态提示
        self.empty_label = ctk.CTkLabel(
            self.card_scroll,
            text="暂无剪贴板历史\n\n复制一段文字或截图试试吧 ✨",
            font=ctk.CTkFont(family="Microsoft YaHei", size=14),
            text_color="#8E8E93",
        )

    # ──────────────────────────────────────────────────────────────
    #  数据刷新
    # ──────────────────────────────────────────────────────────────

    def refresh(self):
        """从数据库重新加载卡片列表"""
        for card in self.cards:
            card.destroy()
        self.cards.clear()

        search = self.search_var.get().strip() if hasattr(self, "search_var") else None
        records = self.storage.get_records(search=search)

        if not records:
            self.empty_label.pack(pady=80)
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
            card.pack(fill="x", pady=(0, 10))
            self.cards.append(card)

    def set_monitor(self, monitor):
        self._monitor = monitor
        monitor.on_new_record = self._on_new_record_from_monitor

    def _on_new_record_from_monitor(self, record):
        self.after(100, self.refresh)

    # ──────────────────────────────────────────────────────────────
    #  用户操作
    # ──────────────────────────────────────────────────────────────

    def _on_search(self):
        self.refresh()

    def _on_settings(self):
        if self.on_open_settings:
            self.on_open_settings()

    def _do_copy(self, record):
        """复制内容到剪贴板"""
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
                        output = io.BytesIO()
                        img.convert("RGB").save(output, format="BMP")
                        data = output.getvalue()[14:]
                        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            pass

    def _do_pin(self, record):
        new_state = self.storage.toggle_pin(record["id"])
        if new_state is not None:
            record["pinned"] = new_state
            self.refresh()

    def _do_delete(self, record):
        self.storage.delete_record(record["id"])
        self.refresh()

    # ──────────────────────────────────────────────────────────────
    #  窗口显隐
    # ──────────────────────────────────────────────────────────────

    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.refresh()

    def hide_window(self):
        self.withdraw()
