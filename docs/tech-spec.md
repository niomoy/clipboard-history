# 技术规范 — 历史粘贴板

## 技术栈

| 层面 | 选型 | 版本 | 用途 |
|------|------|------|------|
| 语言 | Python | ≥3.9 | 主开发语言 |
| GUI | customtkinter | ≥5.2 | 现代化 Tkinter 封装，圆角/主题 |
| 系统托盘 | pystray | ≥0.19 | 跨平台系统托盘 |
| 剪贴板 | pywin32 | ≥306 | Windows 原生剪贴板 API |
| 图片处理 | Pillow | ≥10.0 | 图片格式转换、缩略图生成 |
| 数据库 | sqlite3 | 内置 | 轻量级本地存储 |
| 打包 | PyInstaller | ≥6.0 | 单文件 .exe 打包 |

## 数据库设计

### 主表：clipboard_history

```sql
CREATE TABLE IF NOT EXISTS clipboard_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT    NOT NULL CHECK(type IN ('text', 'image')),
    content     TEXT,           -- 文字内容（type='text' 时使用）
    image_path  TEXT,           -- 原图文件路径（type='image' 时使用）
    thumbnail   TEXT,           -- 缩略图文件路径（type='image' 时使用）
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    pinned      INTEGER NOT NULL DEFAULT 0 CHECK(pinned IN (0, 1))
);
```

### 配置表：settings

```sql
CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

默认配置项：
- `retention_days`: `3`（保留天数，可选 1/3/5）
- `auto_start`: `1`（开机自启，0=关闭 1=开启）

## 存储路径

```
%APPDATA%/ClipboardHistory/
├── clipboard.db          # SQLite 数据库
├── images/               # 原始图片
│   └── {id}_{timestamp}.png
└── thumbnails/           # 缩略图
    └── {id}_{timestamp}_thumb.png
```

## 模块职责

### main.py — 入口文件
- 创建数据目录
- 初始化 storage 和 clipboard_monitor
- 启动系统托盘图标
- 创建主窗口（延迟加载）
- 处理应用生命周期

### storage.py — 数据存储层
- `init_db()` — 初始化数据库和表
- `add_record(type, content, image_path, thumbnail)` — 新增记录，返回 id
- `get_records(search=None, limit=200)` — 获取记录列表（置顶优先，时间降序）
- `toggle_pin(record_id)` — 切换置顶状态
- `delete_record(record_id)` — 删除记录及关联图片文件
- `get_last_record()` — 获取最新一条记录（用于去重）
- `cleanup_expired(retention_days)` — 清理过期记录
- `get_setting(key)` / `set_setting(key, value)` — 读写配置

### clipboard_monitor.py — 剪贴板监听
- `ClipboardMonitor` 类
- 后台线程，轮询间隔 0.5 秒
- `_check_clipboard()` — 检测剪贴板内容变化
- `_handle_text(text)` — 处理文字，去重后写入 storage
- `_handle_image(image)` — 处理图片，保存 PNG + 生成缩略图
- 通过回调通知 UI 刷新

### ui/main_window.py — 主窗口
- `MainWindow` 类（继承 customtkinter.CTk）
- 搜索栏 + 设置按钮（顶部）
- 卡片滚动区域（可滚动 Frame）
- `refresh_cards()` — 刷新卡片列表
- `on_search()` — 搜索过滤

### ui/card_widget.py — 卡片组件
- `ClipboardCard` 类（继承 customtkinter.CTkFrame）
- 支持文字卡片和图片卡片两种模式
- 点击卡片 → 复制内容到剪贴板
- 置顶按钮、删除按钮

### ui/settings_window.py — 设置窗口
- `SettingsWindow` 类（继承 customtkinter.CTkToplevel）
- 保留天数下拉选择
- 开机自启勾选框
- 保存按钮

## API 约定

所有模块间交互通过 storage 模块进行，不直接操作数据库。剪贴板监听线程通过回调函数与 UI 通信。

```python
# 回调签名
def on_new_record(record: dict) -> None:
    """剪贴板监听发现新记录时调用"""
    pass
```

## 线程安全

- SQLite 连接使用 `check_same_thread=False`，每个线程创建独立连接
- 剪贴板访问使用 `threading.Lock` 互斥
- UI 更新通过 `customtkinter` 的 `after()` 方法回到主线程
