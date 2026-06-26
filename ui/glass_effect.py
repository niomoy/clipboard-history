# -*- coding: utf-8 -*-
"""
毛玻璃效果模块 — 调用 Windows Acrylic/Blur API 实现窗口背景模糊
仅 Windows 10+ 支持；不支持时回退为半透明纯色背景
"""

import ctypes
import sys
import platform


# ---------------------------------------------------------------------------
# 检测 Windows 版本
# ---------------------------------------------------------------------------

def _is_windows_10_or_later():
    """检查是否为 Windows 10 1803 或更高版本"""
    if sys.platform != "win32":
        return False
    try:
        ver = platform.version()
        # Windows 10 版本号 >= 10.0.17134 (1803)
        parts = ver.split(".")
        if len(parts) >= 2:
            major, minor = int(parts[0]), int(parts[1])
            return (major > 10) or (major == 10 and minor >= 0)
    except Exception:
        pass
    return True  # 默认尝试启用


# ---------------------------------------------------------------------------
# Windows DWM / Acrylic API（通过 ctypes）
# ---------------------------------------------------------------------------

# Accent State 常量
ACCENT_ENABLE_GRADIENT = 1
ACCENT_ENABLE_TRANSPARENTGRADIENT = 2
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4  # Win10 1803+
ACCENT_ENABLE_HOSTBACKDROP = 5       # Win11

# Window Composition 属性
WCA_ACCENT_POLICY = 19


class _ACCENTPOLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState",  ctypes.c_int),
        ("AccentFlags",  ctypes.c_int),
        ("GradientColor", ctypes.c_int),   # ABGR 格式: 0xAABBGGRR
        ("AnimationId",  ctypes.c_int),
    ]


class _WINCOMPATTRDATA(ctypes.Structure):
    _fields_ = [
        ("Attribute",   ctypes.c_int),
        ("Data",        ctypes.POINTER(_ACCENTPOLICY)),
        ("SizeOfData",  ctypes.c_size_t),
    ]


def _apply_accent(hwnd, accent_state, gradient_color=0):
    """
    为指定窗口应用 DWM 模糊效果
    :param hwnd: 窗口句柄（整数）
    :param accent_state: AccentState 常量
    :param gradient_color: 渐变颜色（ABGR 格式），模糊叠加色
    """
    user32 = ctypes.windll.user32
    SetWindowCompositionAttribute = user32.SetWindowCompositionAttribute
    SetWindowCompositionAttribute.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(_WINCOMPATTRDATA),
    ]
    SetWindowCompositionAttribute.restype = ctypes.c_int

    accent = _ACCENTPOLICY()
    accent.AccentState = accent_state
    accent.AccentFlags = 2
    accent.GradientColor = gradient_color
    accent.AnimationId = 0

    data = _WINCOMPATTRDATA()
    data.Attribute = WCA_ACCENT_POLICY
    data.SizeOfData = ctypes.sizeof(accent)
    data.Data = ctypes.pointer(accent)

    SetWindowCompositionAttribute(hwnd, ctypes.pointer(data))


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------

def get_hwnd(tk_widget):
    """
    从 Tkinter/customtkinter 窗口获取 Win32 HWND
    :param tk_widget: CTk 或 Tk 实例
    :return: 整数 HWND
    """
    # Tkinter 在 Windows 上，winfo_id() 返回十六进制字符串 HWND
    try:
        return int(tk_widget.winfo_id(), 16)
    except (ValueError, TypeError):
        return int(tk_widget.frame(), 16)


def apply_acrylic(tk_window, tint_abgr=0x01F0F4F0):
    """
    为窗口启用 Windows Acrylic 毛玻璃效果
    :param tk_window: CTk / Tk 窗口实例
    :param tint_abgr: ABGR 格式的叠加颜色 (0xAABBGGRR)
                      默认 0x01F0F4F0 = 极淡蓝白叠加，几乎透明
                      例如 0x80F0F0F0 = 50% 透明白
                      例如 0xC0E8F0F4 = 75% 淡蓝白
    """
    if not _is_windows_10_or_later():
        return False

    try:
        hwnd = get_hwnd(tk_window)
        _apply_accent(hwnd, ACCENT_ENABLE_ACRYLICBLURBEHIND, tint_abgr)
        return True
    except Exception:
        # Acrylic 不可用，尝试简单 Blur
        try:
            hwnd = get_hwnd(tk_window)
            _apply_accent(hwnd, ACCENT_ENABLE_BLURBEHIND, tint_abgr)
            return True
        except Exception:
            return False


def apply_blur(tk_window):
    """
    为窗口启用基础模糊效果（兼容旧版 Windows 10）
    """
    try:
        hwnd = get_hwnd(tk_window)
        _apply_accent(hwnd, ACCENT_ENABLE_BLURBEHIND, 0)
        return True
    except Exception:
        return False
