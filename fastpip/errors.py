# -*- coding: utf-8 -*-

'''异常集合，主要是为了中文异常名。'''


class 目录查找异常(Exception):
    pass


class Pip未找到异常(Exception):
    pass


class 参数数据类型异常(Exception):
    pass


class 适用平台异常(Exception):
    pass


class 参数值异常(Exception):
    pass


# __all__ = ['目录查找异常', 'Pip未找到异常', '参数数据类型异常', '适用平台异常', '参数值异常']