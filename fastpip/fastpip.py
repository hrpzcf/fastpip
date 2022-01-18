# coding: utf-8

from warnings import warn

warn(
    "警告：fastpip正式版将删除此导入路径，现在可以直接从fastpip导入"
    "parse_package_names而无需通过模块的相对路径，请尽快更改你的程序的相关代码。",
    stacklevel=2,
)

# 为了兼容改变fastpip目录结构前通过相对路径导入parse_package_names的程序
__all__ = [
    "all_py_paths",
    "parse_package_names",
]
from .core.fastpip import parse_package_names
from .utils.findpath import all_py_paths
