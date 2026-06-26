# -*- coding: utf-8 -*-
"""
数据存储层 — SQLite 数据库操作
所有剪贴板记录的增删改查、配置读写、过期清理
"""

import os
import sqlite3
import shutil
from datetime import datetime, timedelta
from pathlib import Path


class Storage:
    """剪贴板历史数据存储管理"""

    def __init__(self):
        # 数据目录：%APPDATA%/ClipboardHistory/
        appdata = os.environ.get("APPDATA", os.path.expanduser("~"))
        self.data_dir = os.path.join(appdata, "ClipboardHistory")
        self.db_path = os.path.join(self.data_dir, "clipboard.db")
        self.images_dir = os.path.join(self.data_dir, "images")
        self.thumbnails_dir = os.path.join(self.data_dir, "thumbnails")

        # 确保目录存在
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)

        # 初始化数据库
        self._init_db()

    # ------------------------------------------------------------------
    # 数据库初始化
    # ------------------------------------------------------------------

    def _get_conn(self):
        """获取数据库连接（每次调用创建新连接，避免线程问题）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clipboard_history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    type        TEXT    NOT NULL CHECK(type IN ('text', 'image')),
                    content     TEXT,
                    image_path  TEXT,
                    thumbnail   TEXT,
                    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
                    pinned      INTEGER NOT NULL DEFAULT 0 CHECK(pinned IN (0, 1))
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            # 默认配置（不存在才插入）
            conn.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES ('retention_days', '3')
            """)
            conn.execute("""
                INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_start', '1')
            """)
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 记录 CRUD
    # ------------------------------------------------------------------

    def add_record(self, record_type, content=None, image_path=None, thumbnail=None):
        """
        新增一条记录
        :param record_type: 'text' 或 'image'
        :param content: 文字内容
        :param image_path: 图片文件路径
        :param thumbnail: 缩略图文件路径
        :return: 新记录的 id
        """
        conn = self._get_conn()
        try:
            cursor = conn.execute(
                """INSERT INTO clipboard_history (type, content, image_path, thumbnail)
                   VALUES (?, ?, ?, ?)""",
                (record_type, content, image_path, thumbnail),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_last_record(self):
        """
        获取最新一条记录（用于去重判断）
        :return: dict 或 None
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM clipboard_history ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_records(self, search=None, limit=200):
        """
        获取记录列表：置顶优先，时间降序
        :param search: 搜索关键词（可选）
        :param limit: 最大返回数
        :return: list[dict]
        """
        conn = self._get_conn()
        try:
            if search and search.strip():
                keyword = f"%{search.strip()}%"
                rows = conn.execute(
                    """SELECT * FROM clipboard_history
                       WHERE type='text' AND content LIKE ?
                       ORDER BY pinned DESC, id DESC
                       LIMIT ?""",
                    (keyword, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM clipboard_history
                       ORDER BY pinned DESC, id DESC
                       LIMIT ?""",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def toggle_pin(self, record_id):
        """
        切换置顶状态
        :param record_id: 记录 id
        :return: 新的置顶状态 (0 或 1)
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT pinned FROM clipboard_history WHERE id=?", (record_id,)
            ).fetchone()
            if not row:
                return None
            new_state = 0 if row["pinned"] else 1
            conn.execute(
                "UPDATE clipboard_history SET pinned=? WHERE id=?",
                (new_state, record_id),
            )
            conn.commit()
            return new_state
        finally:
            conn.close()

    def delete_record(self, record_id):
        """
        删除记录，同时删除关联的图片文件
        :param record_id: 记录 id
        :return: 是否成功
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT image_path, thumbnail FROM clipboard_history WHERE id=?",
                (record_id,),
            ).fetchone()
            if not row:
                return False

            # 删除图片文件
            if row["image_path"] and os.path.exists(row["image_path"]):
                os.remove(row["image_path"])
            if row["thumbnail"] and os.path.exists(row["thumbnail"]):
                os.remove(row["thumbnail"])

            conn.execute("DELETE FROM clipboard_history WHERE id=?", (record_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 过期清理
    # ------------------------------------------------------------------

    def cleanup_expired(self):
        """
        清理超过保留天数的非置顶记录，同时删除图片文件
        """
        retention_days = int(self.get_setting("retention_days", "3"))
        cutoff = (datetime.now() - timedelta(days=retention_days)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        conn = self._get_conn()
        try:
            # 查询过期记录
            expired = conn.execute(
                """SELECT id, image_path, thumbnail FROM clipboard_history
                   WHERE pinned=0 AND created_at < ?""",
                (cutoff,),
            ).fetchall()

            for row in expired:
                if row["image_path"] and os.path.exists(row["image_path"]):
                    os.remove(row["image_path"])
                if row["thumbnail"] and os.path.exists(row["thumbnail"]):
                    os.remove(row["thumbnail"])

            conn.execute(
                "DELETE FROM clipboard_history WHERE pinned=0 AND created_at < ?",
                (cutoff,),
            )
            conn.commit()
            return len(expired)
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 配置读写
    # ------------------------------------------------------------------

    def get_setting(self, key, default=None):
        """
        读取配置项
        :param key: 配置键名
        :param default: 默认值
        :return: 配置值（字符串）
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT value FROM settings WHERE key=?", (key,)
            ).fetchone()
            return row["value"] if row else default
        finally:
            conn.close()

    def set_setting(self, key, value):
        """
        写入配置项
        :param key: 配置键名
        :param value: 配置值
        """
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, str(value)),
            )
            conn.commit()
        finally:
            conn.close()
