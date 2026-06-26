# -*- coding: utf-8 -*-
"""
卡片组件 — 毛玻璃质感卡片（frosted glass card）
每张卡片模拟真实磨砂玻璃：大圆角、细白描边、顶部高光线、极轻阴影
"""

import os
import customtkinter as ctk
from PIL import Image as PILImage


class ClipboardCard(ctk.CTkFrame):
    """毛玻璃质感卡片 — 单条剪贴板记录"""

    # ── 毛玻璃色彩体系 ──
    GLASS_BG        = "#F5F7FA"   # 雾白卡片（模拟半透白）
    GLASS_HOVER     = "#FFFFFF"   # 悬停更亮（模拟"看清"）
    GLASS_PINNED    = "#EDF1F7"   # 置顶淡蓝白
    GLASS_BORDER    = "#FFFFFF"   # 白描边
    GLASS_HIGHLIGHT = "#FFFFFF"   # 顶部高光线

    TEXT_MAIN       = "#2C2C2E"   # iOS 主文字
    TEXT_SECONDARY  = "#8E8E93"   # iOS 次要文字（时间戳）
    ACCENT_BLUE     = "#9ACFFF"   # 柔和蓝
    ACCENT_BLUE_HOV = "#7AB8E8"   # 深一点
    DANGER_RED      = "#FF9C9A"   # 柔和红
    DANGER_RED_HOV  = "#E88987"   # 深一点

    CORNER_RADIUS = 18
    BORDER_WIDTH  = 1

    def __init__(self, master, record, on_copy=None, on_pin=None, on_delete=None, **kwargs):
        self.record = record
        self.on_copy = on_copy
        self.on_pin = on_pin
        self.on_delete = on_delete

        # 背景色
        bg = self.GLASS_PINNED if record.get("pinned") else self.GLASS_BG
        self._bg_normal = bg
        self._bg_hover  = self.GLASS_HOVER

        super().__init__(
            master,
            fg_color=bg,
            corner_radius=self.CORNER_RADIUS,
            border_width=self.BORDER_WIDTH,
            border_color=self.GLASS_BORDER,
            **kwargs,
        )

        self._build()
        self._bind_events()

    # ──────────────────────────────────────────────────────────────
    #  构建卡片
    # ──────────────────────────────────────────────────────────────

    def _build(self):
        """卡片 = 顶部高光线 + 内容区 + 底部操作栏"""
        self._build_highlight_line()
        self._build_body()
        self._build_footer()

    def _build_highlight_line(self):
        """顶部 1px 白色高光线，模拟玻璃边缘反光"""
        highlight = ctk.CTkFrame(
            self,
            height=1,
            fg_color=self.GLASS_HIGHLIGHT,
            corner_radius=0,
        )
        highlight.pack(fill="x", padx=self.CORNER_RADIUS - 4, pady=(6, 0))

    def _build_body(self):
        """卡片内容（文字或图片）"""
        if self.record["type"] == "image":
            self._build_image_body()
        else:
            self._build_text_body()

    def _build_text_body(self):
        content = self.record.get("content", "")
        display_text = self._truncate_text(content, max_chars=200)

        self.content_label = ctk.CTkLabel(
            self,
            text=display_text,
            font=ctk.CTkFont(family="Microsoft YaHei", size=13),
            text_color=self.TEXT_MAIN,
            wraplength=340,
            justify="left",
            anchor="w",
        )
        self.content_label.pack(fill="x", padx=16, pady=(10, 6))

    def _build_image_body(self):
        thumb_path = self.record.get("thumbnail", "")
        img_path   = self.record.get("image_path", "")

        body_frame = ctk.CTkFrame(self, fg_color="transparent")
        body_frame.pack(fill="x", padx=16, pady=(10, 6))

        thumb_shown = False
        for path in (thumb_path, img_path):
            if path and os.path.exists(path):
                try:
                    img = PILImage.open(path)
                    img.thumbnail((160, 120), PILImage.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    thumb_label = ctk.CTkLabel(body_frame, image=ctk_img, text="")
                    thumb_label.image = ctk_img
                    thumb_label.pack(side="left", padx=(0, 10))
                    thumb_shown = True
                    break
                except Exception:
                    pass

        if not thumb_shown:
            placeholder = ctk.CTkLabel(
                body_frame,
                text="🖼",
                font=ctk.CTkFont(size=28),
                text_color=self.TEXT_SECONDARY,
            )
            placeholder.pack(side="left", padx=(0, 10))

        type_label = ctk.CTkLabel(
            body_frame,
            text="图片",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_SECONDARY,
        )
        type_label.pack(side="left")

    def _build_footer(self):
        """底部：时间戳 + 操作按钮"""
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=14, pady=(4, 10))

        # 时间戳
        created = self.record.get("created_at", "")
        display_time = self._format_time(created)
        time_label = ctk.CTkLabel(
            footer,
            text=display_time,
            font=ctk.CTkFont(size=11),
            text_color=self.TEXT_SECONDARY,
        )
        time_label.pack(side="left")

        # 置顶按钮
        is_pinned = self.record.get("pinned", False)
        pin_text  = "📍 已置顶" if is_pinned else "📌 置顶"
        pin_btn = ctk.CTkButton(
            footer,
            text=pin_text,
            width=72,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=self.ACCENT_BLUE if not is_pinned else self.TEXT_SECONDARY,
            hover_color=self.ACCENT_BLUE_HOV if not is_pinned else "#757578",
            text_color="#1A1A2E",
            corner_radius=8,
            command=self._on_pin_click,
        )
        pin_btn.pack(side="right", padx=(6, 0))

        # 删除按钮
        del_btn = ctk.CTkButton(
            footer,
            text="🗑 删除",
            width=62,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=self.DANGER_RED,
            hover_color=self.DANGER_RED_HOV,
            text_color="#1A1A2E",
            corner_radius=8,
            command=self._on_delete_click,
        )
        del_btn.pack(side="right", padx=(6, 0))

    # ──────────────────────────────────────────────────────────────
    #  交互事件
    # ──────────────────────────────────────────────────────────────

    def _bind_events(self):
        """绑定鼠标事件"""
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_copy_click)

    def _on_copy_click(self, event=None):
        if self.on_copy:
            # 点击时短暂亮度变化（模拟玻璃受压反光）
            self.configure(fg_color="#FFFFFF")
            self.after(120, lambda: self.configure(fg_color=self._bg_hover))
            self.after(250, lambda: self.configure(
                fg_color=self.GLASS_HOVER if not self.record.get("pinned") else self.GLASS_PINNED
            ))
            self.on_copy(self.record)

    def _on_pin_click(self):
        if self.on_pin:
            self.on_pin(self.record)

    def _on_delete_click(self):
        if self.on_delete:
            self.on_delete(self.record)

    def _on_enter(self, event=None):
        self.configure(fg_color=self._bg_hover)

    def _on_leave(self, event=None):
        self.configure(fg_color=self._bg_normal)

    # ──────────────────────────────────────────────────────────────
    #  工具
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _truncate_text(text, max_chars=200):
        if len(text) <= max_chars:
            return text
        return text[:max_chars - 3] + "..."

    @staticmethod
    def _format_time(time_str):
        if not time_str:
            return ""
        try:
            parts = time_str.split(" ")
            if len(parts) == 2:
                date_part = parts[0]  # 2026-06-25
                time_part = parts[1][:5]  # 14:30
                date_short = date_part[5:]  # 06-25
                return f"{date_short} {time_part}"
        except Exception:
            pass
        return time_str[:16]
