# -*- coding: utf-8 -*-

license = ''' MIT License

Copyright (c) 2020 hrpzcf / hrp < hrpzcf@foxmail.com >

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.'''

from .errors import (
    参数值异常,
    数据类型异常,
    文件查找异常,
    目录查找异常,
    适用平台异常,
    PyEnvNotFound,
)
from .fastpip import PyEnv, all_py_paths, cur_py_path, index_urls

__all__ = [
    'PyEnv',
    'all_py_paths',
    'cur_py_path',
    'index_urls',
    '参数值异常',
    '数据类型异常',
    '文件查找异常',
    '目录查找异常',
    '适用平台异常',
    'PyEnvNotFound',
]

NAME = 'fastpip'
VERSION = '0.3.4'
AUTHOR = 'hrpzcf'
EMAIL = 'hrpzcf@foxmail.com'
WEBSITE = 'https://gitee.com/hrpzcf/fastpip'
