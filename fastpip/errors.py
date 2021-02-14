# coding: utf-8


class ParamTypeError(Exception):
    """参数数据类型异常"""

    pass


class ParamValueError(Exception):
    """参数值异常"""

    pass


class PathParamError(Exception):
    """路径参数异常"""

    pass


class UnsupportedPlatform(Exception):
    """运行在不支持的平台上"""

    pass


__all__ = [
    'ParamTypeError',
    'ParamValueError',
    'PathParamError',
    'UnsupportedPlatform',
]
