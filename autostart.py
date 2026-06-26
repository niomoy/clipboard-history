# -*- coding: utf-8 -*-
"""
开机自启管理 — 通过 Windows 启动文件夹快捷方式实现
"""

import os
import sys


def get_startup_folder():
    """获取 Windows 启动文件夹路径"""
    return os.path.join(
        os.environ.get("APPDATA", ""),
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
    )


def get_shortcut_path():
    """获取自启快捷方式的路径"""
    return os.path.join(get_startup_folder(), "历史粘贴板.lnk")


def get_target_path():
    """
    获取快捷方式的目标路径
    打包后指向 .exe，开发中指向 main.py（用 pythonw 启动）
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后
        return sys.executable
    else:
        # 开发模式：使用当前 Python 的 pythonw.exe
        python_dir = os.path.dirname(sys.executable)
        pythonw = os.path.join(python_dir, "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable  # 回退
        return pythonw


def get_working_dir():
    """获取工作目录"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def auto_start_enabled():
    """检查开机自启是否已启用"""
    return os.path.exists(get_shortcut_path())


def enable_auto_start():
    """启用开机自启（创建快捷方式）"""
    shortcut_path = get_shortcut_path()
    target = get_target_path()
    working_dir = get_working_dir()

    # 确保启动文件夹存在
    os.makedirs(get_startup_folder(), exist_ok=True)

    # 使用 Windows COM 创建 .lnk 快捷方式
    try:
        import pythoncom
        from win32com.client import Dispatch

        pythoncom.CoInitialize()

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = working_dir

        if getattr(sys, "frozen", False):
            shortcut.Arguments = ""
        else:
            # 开发模式：传递 main.py 路径给 pythonw
            main_py = os.path.join(working_dir, "main.py")
            shortcut.Arguments = f'"{main_py}"'

        shortcut.Description = "历史粘贴板 - 剪贴板历史管理"
        shortcut.WindowStyle = 7  # 最小化
        shortcut.IconLocation = target
        shortcut.Save()

        return True
    except Exception:
        # COM 不可用时，尝试创建简单的批处理文件来启动
        try:
            # 删除可能存在的旧快捷方式
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)

            # 写一个 .vbs 脚本来静默启动
            vbs_path = shortcut_path.replace(".lnk", ".vbs")
            main_py = os.path.join(working_dir, "main.py")
            vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """{target}"" "{main_py}"", 0, False
'''
            with open(vbs_path, "w") as f:
                f.write(vbs_content)
            return True
        except Exception:
            return False
    finally:
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def disable_auto_start():
    """禁用开机自启（删除快捷方式）"""
    shortcut_path = get_shortcut_path()
    removed = False

    if os.path.exists(shortcut_path):
        try:
            os.remove(shortcut_path)
            removed = True
        except Exception:
            pass

    # 也清理 .vbs 备用文件
    vbs_path = shortcut_path.replace(".lnk", ".vbs")
    if os.path.exists(vbs_path):
        try:
            os.remove(vbs_path)
        except Exception:
            pass

    return removed
