# coding: utf-8

LICENSE = """ MIT License

Copyright (c) 2020-2021 hrp/hrpzcf <hrpzcf@foxmail.com>

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
SOFTWARE."""

__all__ = [
    "AUTHOR",
    "all_py_paths",
    "Command",
    "cur_py_path",
    "decode_bytes",
    "execute_commands",
    "LICENSE",
    "NAME",
    "PipInformation",
    "PyEnv",
    "parse_package_names",
    "VERNUM",
    "VERSION",
    "WEBSITE",
    "index_urls",
]

from .__version__ import *
from .com.common import decode_bytes
from .core.fastpip import (
    PipInformation,
    PyEnv,
    execute_commands,
    index_urls,
    parse_package_names,
)
from .utils.cmdutil import Command
from .utils.findpath import all_py_paths, cur_py_path
