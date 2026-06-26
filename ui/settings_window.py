# -*- coding: utf-8 -*-
"""
设置窗口 — 保留天数、开机自启配置
"""

import customtkinter as ctk

try:
    from autostart import enable_auto_start, disable_auto_start
except ImportError:
    enable_auto_start = lambda: None
    disable_auto_start = lambda: None


class SettingsWindow(ctk.CTkToplevel):
    """设置弹窗"""

    WIDTH = 340
    HEIGHT = 240

    def __init__(self, master, storage, on_save=None):
        super().__init__(master)

        self.storage = storage
        self.on_save = on_save

        self.title("设置")
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.resizable(False, False)

        # 模态行为
        self.transient(master)
        self.grab_set()

        self._build()
        self._load_settings()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------

    def _build(self):
        """构建设置界面"""
        # 标题
        title = ctk.CTkLabel(
            self,
            text="设置",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#333333",
        )
        title.pack(pady=(20, 16))

        # 保留天数
        retention_frame = ctk.CTkFrame(self, fg_color="transparent")
        retention_frame.pack(fill="x", padx=24, pady=(0, 12))

        retention_label = ctk.CTkLabel(
            retention_frame,
            text="保留天数",
            font=ctk.CTkFont(size=14),
            text_color="#333333",
        )
        retention_label.pack(side="left")

        self.retention_var = ctk.StringVar(value="3")
        retention_menu = ctk.CTkOptionMenu(
            retention_frame,
            values=["1", "3", "5"],
            variable=self.retention_var,
            width=80,
            font=ctk.CTkFont(size=13),
            fg_color="#42A5F5",
            button_color="#42A5F5",
            button_hover_color="#1E88E5",
        )
        retention_menu.pack(side="right")

        # 天数说明
        day_hint = ctk.CTkLabel(
            self,
            text="超过保留天数的普通记录将自动清理",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
        )
        day_hint.pack(padx=24, anchor="w", pady=(0, 16))

        # 开机自启
        auto_frame = ctk.CTkFrame(self, fg_color="transparent")
        auto_frame.pack(fill="x", padx=24, pady=(0, 6))

        auto_label = ctk.CTkLabel(
            auto_frame,
            text="开机自启",
            font=ctk.CTkFont(size=14),
            text_color="#333333",
        )
        auto_label.pack(side="left")

        self.auto_var = ctk.BooleanVar(value=True)
        auto_switch = ctk.CTkSwitch(
            auto_frame,
            variable=self.auto_var,
            text="",
            progress_color="#42A5F5",
            width=44,
        )
        auto_switch.pack(side="right")

        # 按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(16, 12))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="取消",
            width=80,
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color="#888888",
            hover_color="#E3F2FD",
            command=self.destroy,
        )
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            btn_frame,
            text="保存",
            width=80,
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color="#42A5F5",
            hover_color="#1E88E5",
            command=self._on_save,
        )
        save_btn.pack(side="right")

    # ------------------------------------------------------------------
    # 数据加载与保存
    # ------------------------------------------------------------------

    def _load_settings(self):
        """从 storage 加载当前设置"""
        retention = self.storage.get_setting("retention_days", "3")
        self.retention_var.set(retention)

        auto_start = self.storage.get_setting("auto_start", "1")
        self.auto_var.set(auto_start == "1")

    def _on_save(self):
        """保存设置"""
        self.storage.set_setting("retention_days", self.retention_var.get())
        self.storage.set_setting("auto_start", "1" if self.auto_var.get() else "0")

        # 实际启用/禁用开机自启
        if self.auto_var.get():
            enable_auto_start()
        else:
            disable_auto_start()

        # 立即执行一次过期清理
        self.storage.cleanup_expired()

        if self.on_save:
            self.on_save()

        self.destroy()
