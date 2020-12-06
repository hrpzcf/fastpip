# -*- coding: utf-8 -*-


class 目录查找异常(Exception):
    pass


class 文件查找异常(Exception):
    pass


class 数据类型异常(Exception):
    pass


class 适用平台异常(Exception):
    pass


class 参数值异常(Exception):
    pass


class PyEnvNotFound(Exception):
    pass


__all__ = [
    '目录查找异常',
    '文件查找异常',
    '数据类型异常',
    '适用平台异常',
    '参数值异常',
    'PyEnvNotFound',
]

