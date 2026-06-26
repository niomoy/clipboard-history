# -*- coding: utf-8 -*-
"""
卡片组件 — 单条剪贴板记录的展示卡片（文字 / 图片）
"""

import os
import customtkinter as ctk
from PIL import Image as PILImage


class ClipboardCard(ctk.CTkFrame):
    """单条剪贴板记录卡片"""

    # 颜色常量
    CARD_BG = "#E3F2FD"        # 普通卡片背景
    CARD_HOVER = "#BBDEFB"     # 悬停 / 置顶背景
    TEXT_COLOR = "#333333"     # 主文字色
    TIME_COLOR = "#888888"     # 时间戳色
    ACCENT = "#42A5F5"         # 强调色
    DANGER = "#EF5350"         # 删除按钮色
    DANGER_HOVER = "#E53935"   # 删除按钮悬停

    def __init__(self, master, record, on_copy=None, on_pin=None, on_delete=None, **kwargs):
        """
        :param master: 父容器
        :param record: 记录 dict（id, type, content, image_path, thumbnail, created_at, pinned）
        :param on_copy: 点击复制回调
        :param on_pin: 置顶切换回调
        :param on_delete: 删除回调
        """
        # 置顶用不同背景色
        bg = self.CARD_HOVER if record.get("pinned") else self.CARD_BG
        super().__init__(master, fg_color=bg, corner_radius=8, **kwargs)

        self.record = record
        self.on_copy = on_copy
        self.on_pin = on_pin
        self.on_delete = on_delete
        self._bg_normal = bg
        self._bg_hover = self.CARD_HOVER

        self._build()

        # 悬停效果
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    # ------------------------------------------------------------------
    # 构建卡片内容
    # ------------------------------------------------------------------

    def _build(self):
        """根据记录类型构建卡片内容"""
        if self.record["type"] == "image":
            self._build_image_card()
        else:
            self._build_text_card()

        # 底部栏：时间戳 + 操作按钮
        self._build_footer()

    def _build_text_card(self):
        """构建文字卡片"""
        content = self.record.get("content", "")

        # 文字内容标签（最多3行，溢出省略）
        display_text = self._truncate_text(content, max_chars=200)

        self.content_label = ctk.CTkLabel(
            self,
            text=display_text,
            font=ctk.CTkFont(size=13),
            text_color=self.TEXT_COLOR,
            wraplength=340,
            justify="left",
            anchor="w",
        )
        self.content_label.pack(fill="x", padx=12, pady=(12, 4))
        self.content_label.bind("<Button-1>", self._on_copy_click)

        # 让整个卡片可点击
        self.bind("<Button-1>", self._on_copy_click)

    def _build_image_card(self):
        """构建图片卡片"""
        thumb_path = self.record.get("thumbnail", "")
        img_path = self.record.get("image_path", "")

        # 图片容器
        img_frame = ctk.CTkFrame(self, fg_color="transparent")
        img_frame.pack(fill="x", padx=12, pady=(12, 4))

        # 尝试加载缩略图
        thumb_displayed = False
        for path in (thumb_path, img_path):
            if path and os.path.exists(path):
                try:
                    img = PILImage.open(path)
                    # 缩略图最大 160×120
                    img.thumbnail((160, 120), PILImage.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    thumb_label = ctk.CTkLabel(img_frame, image=ctk_img, text="")
                    thumb_label.image = ctk_img  # 保持引用
                    thumb_label.pack(side="left", padx=(0, 8))
                    thumb_displayed = True
                    break
                except Exception:
                    pass

        if not thumb_displayed:
            # 缩略图加载失败，显示占位符
            placeholder = ctk.CTkLabel(
                img_frame,
                text="🖼 图片",
                font=ctk.CTkFont(size=20),
                text_color=self.TIME_COLOR,
            )
            placeholder.pack(side="left", padx=(0, 8))

        # 图片标签
        type_label = ctk.CTkLabel(
            img_frame,
            text="点击复制图片",
            font=ctk.CTkFont(size=12),
            text_color=self.TIME_COLOR,
        )
        type_label.pack(side="left")

        img_frame.bind("<Button-1>", self._on_copy_click)
        self.bind("<Button-1>", self._on_copy_click)

    def _build_footer(self):
        """构建底部栏"""
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=12, pady=(4, 8))

        # 时间戳
        created = self.record.get("created_at", "")
        display_time = self._format_time(created)

        time_label = ctk.CTkLabel(
            footer,
            text=display_time,
            font=ctk.CTkFont(size=11),
            text_color=self.TIME_COLOR,
        )
        time_label.pack(side="left")

        # 置顶按钮
        pin_text = "📌 取消置顶" if self.record.get("pinned") else "📌 置顶"
        pin_btn = ctk.CTkButton(
            footer,
            text=pin_text,
            width=70,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=self.ACCENT,
            hover_color="#1E88E5",
            corner_radius=6,
            command=self._on_pin_click,
        )
        pin_btn.pack(side="right", padx=(4, 0))

        # 删除按钮
        del_btn = ctk.CTkButton(
            footer,
            text="🗑 删除",
            width=60,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color=self.DANGER,
            hover_color=self.DANGER_HOVER,
            corner_radius=6,
            command=self._on_delete_click,
        )
        del_btn.pack(side="right", padx=(4, 0))

    # ------------------------------------------------------------------
    # 交互事件
    # ------------------------------------------------------------------

    def _on_copy_click(self, event=None):
        """点击复制"""
        if self.on_copy:
            self.on_copy(self.record)

    def _on_pin_click(self):
        """点击置顶"""
        if self.on_pin:
            self.on_pin(self.record)

    def _on_delete_click(self):
        """点击删除"""
        if self.on_delete:
            self.on_delete(self.record)

    def _on_enter(self, event=None):
        """鼠标进入"""
        if not self.record.get("pinned"):
            self.configure(fg_color=self._bg_hover)

    def _on_leave(self, event=None):
        """鼠标离开"""
        if not self.record.get("pinned"):
            self.configure(fg_color=self._bg_normal)

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    @staticmethod
    def _truncate_text(text, max_chars=200):
        """截断文字，超过长度用 ... 省略"""
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3] + "..."

    @staticmethod
    def _format_time(time_str):
        """格式化时间戳显示"""
        if not time_str:
            return ""
        # SQLite 格式：2026-06-25 14:30:00
        # 简化显示：06-25 14:30
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
