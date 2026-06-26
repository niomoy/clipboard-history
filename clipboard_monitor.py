# -*- coding: utf-8 -*-
"""
剪贴板监听模块 — 后台线程轮询 Windows 剪贴板，自动捕获文字和图片
"""

import os
import time
import hashlib
import threading
from datetime import datetime

import win32clipboard
from PIL import Image, ImageGrab
import io


class ClipboardMonitor:
    """剪贴板监听器，后台线程每 0.5 秒检测一次变化"""

    # Windows 剪贴板格式常量
    CF_UNICODETEXT = 13

    def __init__(self, storage, on_new_record=None):
        """
        :param storage: Storage 实例
        :param on_new_record: 回调函数，参数为 record dict
        """
        self.storage = storage
        self.on_new_record = on_new_record
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._last_text_hash = None
        self._last_image_data = None  # 用于图片去重

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------

    def start(self):
        """启动监听线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止监听线程"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------

    def _run(self):
        """后台轮询主循环"""
        while self._running:
            try:
                self._check_clipboard()
            except Exception:
                pass  # 剪贴板被其他程序占用时静默跳过
            time.sleep(0.5)

    # ------------------------------------------------------------------
    # 剪贴板检测
    # ------------------------------------------------------------------

    def _check_clipboard(self):
        """检测剪贴板内容变化"""
        with self._lock:
            try:
                win32clipboard.OpenClipboard()
            except Exception:
                return

            try:
                # 检测图片（优先，因为剪贴板可能同时有文字和图片）
                if self._clipboard_has_image():
                    self._handle_image()
                # 检测文字
                elif win32clipboard.IsClipboardFormatAvailable(self.CF_UNICODETEXT):
                    text = self._get_clipboard_text()
                    if text and text.strip():
                        self._handle_text(text.strip())
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # 文字处理
    # ------------------------------------------------------------------

    def _get_clipboard_text(self):
        """从剪贴板获取文字"""
        try:
            data = win32clipboard.GetClipboardData(self.CF_UNICODETEXT)
            return data if isinstance(data, str) else data.decode("utf-8", errors="replace")
        except Exception:
            return None

    def _handle_text(self, text):
        """处理文字：去重后存入 storage"""
        text_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        if text_hash == self._last_text_hash:
            return

        self._last_text_hash = text_hash
        self._last_image_data = None

        record_id = self.storage.add_record("text", content=text)
        record = {"id": record_id, "type": "text", "content": text, "pinned": 0}
        if self.on_new_record:
            self.on_new_record(record)

    # ------------------------------------------------------------------
    # 图片处理
    # ------------------------------------------------------------------

    def _clipboard_has_image(self):
        """检测剪贴板是否包含图片"""
        # 先关闭当前打开的剪贴板，让 ImageGrab 能访问
        # 用 win32clipboard 的格式检测（不冲突）
        return (
            win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB)
            or win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIBV5)
            or win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_BITMAP)
        )

    def _handle_image(self):
        """处理图片：用 Pillow ImageGrab 获取 → 保存 + 缩略图 → 存入 storage"""
        # ImageGrab 需要关闭当前剪贴板句柄
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass

        # 用 Pillow 自带的剪贴板截图功能（最可靠的方式）
        try:
            img = ImageGrab.grabclipboard()
        except Exception:
            return

        if img is None:
            return
        if not isinstance(img, Image.Image):
            return

        # 去重：比较图片缩略后的像素数据
        img_small = img.copy()
        img_small.thumbnail((64, 64), Image.LANCZOS)
        img_data = img_small.tobytes()
        img_hash = hashlib.md5(img_data).hexdigest()
        if img_hash == self._last_image_data:
            return

        self._last_image_data = img_hash
        self._last_text_hash = None

        # 确保可保存的模式
        if img.mode not in ("RGB", "RGBA", "P"):
            img = img.convert("RGB")
        elif img.mode == "P":
            img = img.convert("RGBA")

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        img_filename = f"img_{timestamp}.png"
        thumb_filename = f"thumb_{timestamp}.png"

        img_path = os.path.join(self.storage.images_dir, img_filename)
        thumb_path = os.path.join(self.storage.thumbnails_dir, thumb_filename)

        # 保存原图
        img.save(img_path, "PNG")

        # 生成缩略图
        thumb = img.copy()
        thumb.thumbnail((160, 120), Image.LANCZOS)
        thumb.save(thumb_path, "PNG")

        record_id = self.storage.add_record(
            "image", image_path=img_path, thumbnail=thumb_path
        )
        record = {
            "id": record_id,
            "type": "image",
            "image_path": img_path,
            "thumbnail": thumb_path,
            "pinned": 0,
        }
        if self.on_new_record:
            self.on_new_record(record)
