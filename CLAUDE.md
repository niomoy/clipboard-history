# CLAUDE.md — 历史粘贴板项目

## 项目简介

这是一个 Windows 剪贴板历史管理工具。后台自动记录用户复制的文字和图片，用户可随时打开面板查看、搜索、置顶和再次粘贴。

**目标用户**：不懂代码的普通用户
**最终交付**：单个 .exe 文件，双击即用

---

## 文档索引

| 文档 | 路径 | 用途 |
|------|------|------|
| 需求文档 | [docs/requirements.md](docs/requirements.md) | 功能需求清单、软件形态 |
| 技术规范 | [docs/tech-spec.md](docs/tech-spec.md) | 技术栈、数据库结构、模块职责 |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) | UI 颜色、布局、组件样式 |
| 执行计划 | [docs/dev-plan.md](docs/dev-plan.md) | 分步执行步骤、验收标准 |
| 计划文件 | `.claude/plans/windows-1-3-5-ui-atomic-moler.md` | 原始计划文档 |

---

## 项目结构

```
clipboard_history/
├── CLAUDE.md                   # ← 本文件
├── docs/
│   ├── requirements.md
│   ├── tech-spec.md
│   ├── design-spec.md
│   └── dev-plan.md
├── 开发日志/
│   └── YYYY-MM-DD.md
├── main.py                     # 入口
├── clipboard_monitor.py        # 剪贴板监听
├── storage.py                  # 数据存储
├── ui/
│   ├── main_window.py          # 主窗口
│   ├── card_widget.py          # 卡片组件
│   └── settings_window.py      # 设置窗口
├── assets/
│   └── icon.png
└── requirements.txt
```

---

## 开发日志制度

每次工作前，AI 应先做以下事情：

1. **读取最新开发日志** — 查看 `开发日志/` 中最新日期的文件
2. **读取规范文档** — 按需阅读 docs/ 下的相关文件
3. **执行当前任务** — 按 dev-plan.md 中的步骤推进
4. **更新开发日志** — 记录今日完成、待办、问题和下一步

### 日志文件命名

格式：`开发日志/YYYY-MM-DD.md`

### 日志模板

```markdown
# 开发日志 — YYYY-MM-DD

## ✅ 今日完成
- [x] ...

## 📋 待办事项
- [ ] ...

## 🐛 遇到的问题
- 

## 🔜 下一步计划
- 
```

---

## 工作流程（SOP）

```
1. 读 开发日志/最新.md → 了解当前进度
2. 读 docs/dev-plan.md → 确认当前步骤
3. 读 docs/tech-spec.md → 确认技术约定
4. 执行任务 → 增量推进，不跨步骤
5. 测试验证 → 符合验收标准再进入下一步
6. 更新开发日志 → 记录完成事项和下一步
```

---

## 编码规范

### Python 风格
- 使用 UTF-8 编码，文件头加 `# -*- coding: utf-8 -*-`
- 中文注释允许，但函数/变量名使用英文
- 每个文件一个主要类或一组相关函数
- 添加 type hints 提升可读性

### 模块间通信
- 所有数据操作通过 `storage.py` 模块，不直接写 SQL
- 剪贴板监听 → UI 刷新通过回调函数
- UI 更新使用 `after()` 回到主线程

### 错误处理
- 剪贴板访问失败不崩溃，静默重试
- 数据库操作使用 try/except
- 图片处理失败时跳过该条记录

### 路径处理
- 使用 `os.path` 和 `pathlib`，不用硬编码路径
- 数据目录：`%APPDATA%/ClipboardHistory/`
- 开发时的相对路径和打包后的绝对路径都要兼容

---

## 依赖安装

```bash
pip install -r requirements.txt
```

## 运行方式（开发中）

```bash
cd "d:/vibe coding/历史粘贴/"
python main.py
```

## 打包命令（最终）

```bash
pyinstaller --onefile --windowed --icon=assets/icon.png --name "历史粘贴板" main.py
```
