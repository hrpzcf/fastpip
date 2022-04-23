# coding: utf-8

# XXX 即将废弃的部分代码
from warnings import warn

warn(
    "\n警告：'fastpip'将考虑删除'from fastpip.fastpip import parse_package_names'等导入路径。"
    "\n\t新导入方式：'from fastpip import parse_package_names'或'from fastpip import *'等。"
    "\n请考虑将您代码中的旧导入方式改为以上展示的新方式，从此版本到正式版之间的版本，两种导入方式将同时存在。",
    stacklevel=2,
)

# 为了兼容使用旧方法导入的程序
from .core.fastpip import PipInformation, PyEnv, index_urls, parse_package_names
from .utils.findpath import all_py_paths
