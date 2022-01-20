# coding: utf-8

# TODO 在正式版时清理并删除此模块

from warnings import warn

warn(
    "\n弃用警告：正式版 fastpip 将考虑删除 "
    "from fastpip.fastpip import parse_package_names 导入路径。"
    "\n\t新导入方式：from fastpip import parse_package_names 或 from fastpip import *"
    "\n请考虑将您代码中的旧导入方式改为以上展示的新方式，从这个版本到正式版之间的版本，两种导入方式将同时存在。",
    stacklevel=2,
)
# 为了兼容使用旧方法导入的程序
from .core.fastpip import parse_package_names
from .utils.findpath import all_py_paths
