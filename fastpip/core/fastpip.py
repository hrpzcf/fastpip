# coding: utf-8

################################################################################
# MIT License

# Copyright (c) 2020-2021 hrp/hrpzcf <hrpzcf@foxmail.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################
# Formatted with black.
################################################################################

import os
import re
import shutil
import time
from collections import OrderedDict
from copy import deepcopy
from random import randint
from subprocess import *
from typing import *

if os.name != "nt":
    raise Exception("此模块不支持 Windows 以外的操作系统")

from ..__version__ import VERSION
from ..com.common import *  # 一些常用量
from ..utils.cmdutil import Command
from ..utils.findpath import cur_py_path

_INIT_WK_DIR = os.getcwd()
_STARTUP = STARTUPINFO()
_STARTUP.dwFlags = STARTF_USESHOWWINDOW
_STARTUP.wShowWindow = SW_HIDE


# 预设的 PYPI 官方源及国内镜像源：
index_urls = {
    "pypi": "https://pypi.org/simple",  # PYPI 官方源（国外）
    "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",  # 清华源
    "tencent": "https://mirrors.cloud.tencent.com/pypi/simple",  # 腾讯源
    "aliyun": "https://mirrors.aliyun.com/pypi/simple",  # 阿里源
    "bfsu": "https://mirrors.bfsu.edu.cn/pypi/web/simple",  # 北京外国语大学源
    "opentuna": "https://opentuna.cn/pypi/web/simple",  # 清华源
    "douban": "https://pypi.doubanio.com/simple",  # 豆瓣源
    "huawei": "https://mirrors.huaweicloud.com/repository/pypi/simple",  # 华为源
    "netease": "https://mirrors.163.com/pypi/simple",  # 网易源
}

# 预置部分 pip 命令字符串元组格式
_PREFIX = ("-m", "pip")
_PIPCMDS = {
    "FREEZE": (*_PREFIX, "freeze"),
    "ENSUREPIP": ("-m", "ensurepip"),
    "INSTALL": (*_PREFIX, "install"),
    "UNINSTALL": (*_PREFIX, "uninstall", "-y"),
    "LIST": (*_PREFIX, "list"),
    "INFO": (*_PREFIX, "-V"),
    "OUTDATED": (*_PREFIX, "list", "--outdated"),
    "PIPUP": (*_PREFIX, "install", "-U", "pip"),
    "SETINDEX": (*_PREFIX, "config", "set", "global.index-url"),
    "GETINDEX": (*_PREFIX, "config", "list"),
    "DOWNLOAD": (*_PREFIX, "download"),
}


class PipInformation:
    """### pip 信息类。"""

    def __init__(self, pipver, path, pyver):
        self.__path = path
        self.__pyver = pyver
        self.__pipver = pipver

    def __str__(self):
        return "pip_info(pipver={}, path={}, pyver={})".format(
            self.__pipver, self.__path, self.__pyver
        )

    __repr__ = __str__

    @property
    def path(self):
        return self.__path

    @property
    def pyver(self):
        return self.__pyver

    @property
    def pipver(self):
        return self.__pipver


def execute_commands(
    cmds: Command, output: bool, timeout: Union[int, float, None]
) -> Tuple[str, int]:
    """
    ### 执行命令，打印命令输出，返回输出字符串和结束状态码。

    请注意，如果 output 参数值为 True，则 timeout 参数不生效。

    ```python
    :param cmds: Command, 要执行的命令，详见 Command 类的文档
    :param output: bool, 是否逐行向控制台打印命令的输出流
    :param timeout,  Union[int, float, None], 执行命令的超时时长，单位：秒
    :return: Tuple[str, int], 命令执行时输出的全部字符串和退出状态码
    ```
    """
    env = cmds.environment()
    cwd = os.path.dirname(cmds.executable)
    process = Popen(
        cmds,
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
        startupinfo=_STARTUP,
        cwd=cwd,
        env=env,
    )
    if output:
        strings = list()
        while process.poll() is None:
            try:
                line = process.stdout.readline()
            except UnicodeDecodeError as exc:
                line = f"fastpip: {exc.reason}\n"
            if line:
                strings.append(line)
                if output:
                    print(line, end="")
        out_strings = "".join(strings)
        return_code = process.returncode
    else:
        try:
            out_strings, _ = process.communicate(None, timeout)
            return_code = process.returncode
        except:
            return_code = 1
            out_strings = ""
    return out_strings, return_code


def parse_package_names(names):
    """
    ### 排除列表中包名的版本号限制符。

    例如传入['fastpip>=0.5,<0.8']，返回['fastpip']。
    """
    package_names = list()
    pt = re.compile(r"[^<>=,!]+")
    for n in names:
        m_obj = pt.match(n)
        if not m_obj:
            continue
        package_names.append(m_obj.group())
    return package_names


class PyEnv:
    """
    ### Python 环境类。

    此类实例的绝大多数方法效果都将作用于该实例所指的 Python 环境，不对其他环境产生影响。

    只有一个例外：使用 set_global_index 方法设置本机 pip 全局镜像源地址，产生全局作用。
    """

    __CLS_CALLBACK_DICT = OrderedDict()
    _cache_refresh_maximum_interval = 3
    _HOME = os.path.join(
        os.getenv("HOMEDRIVE", EMPTY_STR), os.getenv("HOMEPATH", EMPTY_STR)
    )
    USER_DOWNLOADS = os.path.join(_HOME or _INIT_WK_DIR, "Downloads")
    FILE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    __string_pyinfo = "Python {} :: {} bit"
    __sitepkg_pattern = re.compile(r"\[.*\]", re.S)
    __pyinfo_pattern = re.compile(r"(\d+\.\d+\.\d+)\+? [(|].+(32|64) bit \(.+\)")
    __info_pkgname_pattern = re.compile(r"^Name: ([A-Za-z0-9_\-\.]+)$")
    __canonical_imp_pattern = re.compile(r"^[A-Za-z_]?[A-Za-z0-9_]+")
    __full_canonical_imp_pattern = re.compile(r"^[A-Za-z_]?[A-Za-z0-9_]+$")
    __module_pattern = re.compile(r"^([A-Z0-9_]+).*(?<!_d)\.py[cdw]?$", re.I)

    def __execute(
        self, cmds: Command, output: bool, timeout: Union[int, float, None]
    ) -> Tuple[str, int]:
        env = cmds.environment()
        cwd = os.path.dirname(cmds.executable)
        process = Popen(
            cmds,
            stdout=PIPE,
            stderr=STDOUT,
            text=True,
            startupinfo=_STARTUP,
            cwd=cwd,
            env=env,
        )
        if not output and not self.__CLS_CALLBACK_DICT:
            try:
                out_strings, _ = process.communicate(None, timeout)
                return_code = process.returncode
            except:
                return_code = 1
                out_strings = ""
        else:
            strings = list()
            while process.poll() is None:
                try:
                    line = process.stdout.readline()
                except UnicodeDecodeError as exc:
                    line = f"fastpip: {exc.reason}\n"
                if line:
                    strings.append(line)
                    if output:
                        print(line, end="")
                    for callback in self.__CLS_CALLBACK_DICT.values():
                        callback(line.rstrip("\n"))
            out_strings = "".join(strings)
            return_code = process.returncode
        return out_strings, return_code

    def __init__(self, path=None):
        """
        ### PyEnv 类初始化方法。

        ```
        :param path: str or None, 一个指向 Python 解释器所在目录的路径。对于 venv 创建的虚拟环境，因 python.exe 在 Scrpits 目录内，所以该路径参数即可以是 Scripts 目录路径也可以是 Scripts 目录的父目录路径。
        ```

        PyEnv 类有参数实例化时，如果参数 path 数据类型既不是 str 也不是 None 则抛出 TypeError 异常。如果参数是空字符串，则代表实例化一个空 PyEnv 实例，稍后可通过对 path 属性赋值使实例具体化。

        PyEnv 类无参数实例化时或参数值为 None 实例化时，使用 cur_py_path 函数选取系统环境变量 PATH 中的首个 Python 目录路径，如果系统环境变量 PATH 中没有找到 Python 目录路径，则将路径属性 path 及 env_path 设置为空字符串。
        """
        self.__time_last_activity = time.time()
        self.__cached_packages_imps: Dict[str, Dict[str, str]] = dict()
        self.__cached_python_info = EMPTY_STR
        # 解释器是否在 Scripts 目录的标识
        self.__pyexe_is_in_scripts = False
        self.__designated_path = self.__init_path(path)

    @staticmethod
    def __init_path(_path):
        """
        ### 初始化 Python 路径。

        `如果路径参数不是字符串，则抛出 TypeError 异常。`
        """
        if isinstance(_path, str):
            if not _path:
                return _path
            return os.path.normpath(_path)
        if _path is None:
            return cur_py_path()
        raise TypeError("路径参数类型错误。")

    @classmethod
    def register(cls, output_callback: Callable[[str], Any]):
        """
        ### 向 PyEnv 类注册回调函数，可多次调用以注册不同函数。

        ```
        :param output_callback: Callable, 回调函数，此函数必须可以接受一个字符串参数。
        :return: str or None, 如果注册成功，此方法返回回调函数在 PyEnv 类中的标识符，用于 deregister 方法，注册失败返回 None。
        ```
        """
        if not isinstance(output_callback, Callable):
            return None
        while True:
            handle = str(randint(0x10000000, 0xFFFFFFFF))
            if handle not in cls.__CLS_CALLBACK_DICT:
                break
        cls.__CLS_CALLBACK_DICT[handle] = output_callback
        return handle

    @classmethod
    def deregister(cls, handle: str):
        """
        ### 向 PyEnv 类反注册已经使用 register 注册过的回调函数。

        ```
        :param handle: str, register 方法的返回值。
        :return: bool, 反注册成功返回 True，失败返回 False。
        ```
        """
        if handle in cls.__CLS_CALLBACK_DICT:
            del cls.__CLS_CALLBACK_DICT[handle]
            return True
        else:
            return False

    @classmethod
    def clear_registered(cls):
        """
        ### 清空所有已注册到 PyEnv 类的回调函数
        """
        cls.__CLS_CALLBACK_DICT.clear()

    @property
    def path(self):
        """
        ### 代表 PyEnv 类实例化时所传入的 Python 环境的绝对路径。

        可重新赋值一个路径(字符串)以改变 PyEnv 类实例所指的 Python 环境。

        赋值类型非 str 则抛出 TypeError 异常。
        """
        if not self.__designated_path:
            return self.__designated_path
        return os.path.abspath(self.__designated_path)

    @path.setter
    def path(self, _path):
        if not isinstance(_path, str):
            raise TypeError("路径参数类型错误。")
        if not _path:
            self.__designated_path = _path
        else:
            self.__designated_path = os.path.normpath(_path)
        self.__cached_python_info = EMPTY_STR

    def __check(self, _path):
        """### 检查参数 path 在当前是否是一个有效的 Python 目录路径。"""
        # 此属性需要实时更新
        # 因为有可能原实例是 venv环境，后来通过对 path 属性赋值变为常规环境
        self.__pyexe_is_in_scripts = False
        _path = os.path.abspath(_path)
        # 传入的目录内没有 python.exe 可执行文件则进入此分支
        if not os.path.isfile(os.path.join(_path, PYTHON_EXE)):
            # 检查是否是 venv 虚拟环境的 Scripts 的上级目录
            if os.path.isfile(os.path.join(_path, VENV_CFG)) and os.path.isfile(
                os.path.join(_path, PYTHON_SCR, PYTHON_EXE)
            ):
                self.__pyexe_is_in_scripts = True
                return os.path.normpath(_path)  # 如是则规范化路径后返回
            return EMPTY_STR  # 如非则路径是无效的，返回空字符串
        # 传入的目录路径内有 python.exe 则进入此分支
        parent, scripts = os.path.split(_path)
        if parent and scripts:
            # 先判断是否是 venv 虚拟环境的 Scripts 目录
            if scripts.lower() == PYTHON_SCR.lower() and os.path.isfile(
                os.path.join(parent, VENV_CFG)
            ):
                self.__pyexe_is_in_scripts = True
                return os.path.normpath(parent)  # 如是则返回 Scripts 上级
        return os.path.normpath(_path)  # 如非则断定是常规目录结构的 Python 环境

    @property
    def env_path(self):
        """
        ### 代表该 Python 环境目录路径的属性，该属性在获取的时候进行实时检查。

        当 PyEnv 实例所指的 Python 环境无效(例如环境被卸载)时该属性值是空字符串，当环境恢复有效后，该属性值是该实例所指 Python 环境的路径(字符串)。
        """
        return self.__check(self.__designated_path)

    @property
    def env_is_valid(self):
        """### 返回代表环境是否有效的布尔值"""
        return bool(self.__check(self.__designated_path))

    @property
    def interpreter(self):
        """
        ### 属性值为 Python 解释器(python.exe)路径。

        PyEnv 实例所指 Python 环境无效(例如环境被卸载)时值是空字符串。
        """
        env_path = self.env_path
        if not env_path:
            return EMPTY_STR
        if self.__pyexe_is_in_scripts:
            return os.path.join(env_path, PYTHON_SCR, PYTHON_EXE)
        return os.path.join(env_path, PYTHON_EXE)

    def __str__(self):
        location = self.env_path or UNKNOWN_LOCATION
        return "{} {} {}".format(self.py_info(), PYENV_SEP_STR, location)

    @property
    def pip_is_ready(self):
        """
        ### 代表该 Python 环境中 pip 是否已安装的属性。

        值为 True 代表 pip 已安装，False 代表未安装，获取属性值时实时检查是否已安装。

        作用和结果与 pip_ready 属性完全一致。
        """
        if not self.env_is_valid:
            return False
        return os.path.isfile(
            os.path.join(self.site_packages_home(), PIP_INIT)
        ) or os.path.isfile(os.path.join(self.user_site_packages_home(), PIP_INIT))

    @property
    def pip_ready(self):
        """
        ### 代表该 Python 环境中 pip 是否已安装的属性。

        值为 True 代表 pip 已安装，False 代表未安装，获取属性值时实时检查是否已安装。

        作用和结果与 pip_is_ready 属性完全一致。
        """
        return self.pip_is_ready

    @staticmethod
    def __check_timeout_num(timeout):
        if isinstance(timeout, (int, float)):
            if timeout < 1:
                raise ValueError("超时参数 timeout 的值不能小于1。")
            return True
        if timeout is None:
            return True
        raise TypeError("参数 timeout 值应为 None、整数或浮点数。")

    def cleanup_old_scripts(self):
        """### 清理旧的脚本。"""
        try:
            files = os.listdir(self.FILE_DIR)
        except Exception:
            return False
        for name in files:
            _path = os.path.join(self.FILE_DIR, name)
            if (
                os.path.isfile(_path)
                and (name.startswith("ReadPyVER") or name.startswith("ReadSYSPB"))
                and not name.endswith(VERSION)
            ):
                try:
                    os.remove(_path)
                except Exception:
                    continue
        return True

    def py_info(self):
        """### 获取当前环境 Python 版本信息。"""
        self.cleanup_old_scripts()
        if self.__cached_python_info:
            return self.__cached_python_info
        if not self.env_path:
            return self.__string_pyinfo.format("0.0.0", "?")
        result, retcode = self.__execute(
            Command(self.interpreter, *CmdRead.PYVERS.value), False, None
        )
        if retcode or not result:
            return self.__string_pyinfo.format("0.0.0", "?")
        # '3.7.14+ (heads/3.7:xxx...) [MSC v.1900 32 bit (Intel)]' etc.
        m_obj = self.__pyinfo_pattern.search(result)
        if not m_obj:
            return self.__string_pyinfo.format("0.0.0", "?")
        self.__cached_python_info = self.__string_pyinfo.format(*m_obj.groups())
        return self.__cached_python_info

    def pip_path(self):
        """
        ### 根据 env_path 属性所指的 Python 安装目录获取 pip 可执行文件路径。

        如果 Scripts 目录不存在或无法打开则返回空字符串。

        如果在 Scripts 目录中没有找到 pip 可执行文件则返回空字符串。

        ```
        :return: str, 该 PyEnv 实例所指 Python 环境的 pip 可执行文件的完整路径或空字符。
        ```
        """
        env_path = self.env_path
        if not env_path:
            return EMPTY_STR
        dir_pip_exists = os.path.join(env_path, PYTHON_SCR)
        try:
            dirs_and_files = os.listdir(dir_pip_exists)
        except Exception:
            return EMPTY_STR
        for dir_or_file in dirs_and_files:
            if not os.path.isfile(os.path.join(dir_pip_exists, dir_or_file)):
                continue
            match_obj = re.match(r"^pip.*\.exe$", dir_or_file)
            if not match_obj:
                continue
            return os.path.join(dir_pip_exists, match_obj.group())
        return EMPTY_STR

    def pip_info(self):
        """
        ### 获取该目录的 pip 版本信息。

        如果获取到 pip 版本信息，则返回一个 PipInformation 实例，可以通过访问实例的 pipver、path、pyver 属性分别获取到 pip 版本号、pip 目录路径、该 pip 所在的 Python 环境版本号。

        如果没有获取到 pip 信息或获取到信息但未正确匹配到信息格式，则返回 None。

        直接打印 PipInfo 实例则显示概览：pip_info(pip 版本、pip 路径、相应 Python 版本)。

        ```
        :return: 匹配到 pip 版本信息：PipInformation 实例；未获取到 pip 版本信息：返回 None。
        ```
        """
        if not self.pip_ready:
            return
        result, retcode = self.__execute(
            Command(self.interpreter, *_PIPCMDS["INFO"]), False, None
        )
        if retcode or not result:
            return
        match_obj = re.match("pip (.+) from (.+) \(python (.+)\)", result.strip())
        if not match_obj:
            return
        res = match_obj.groups()
        if not (len(res) == 3):
            return
        return PipInformation(*res)

    @staticmethod
    def __cleanup_info(string):
        """清理 pip 包名列表命令的无关输出。"""
        preprocessed = re.search(
            r"Package\s+Version\s*\n[-\s]+\n(.+)",
            string,
            re.S,
        )
        if not preprocessed:
            return []
        return re.findall(r"^(\S+)\s+(\S+)\s*$", preprocessed.group(1), re.M)

    def pkgs_info(self, *, output=False, timeout=None):
        """
        ### 获取该 Python 目录下已安装的包列表，列表包含(包名, 版本)元组，没有获取到则返回空列表。

        请注意，如果 output 参数值为 True，则 timeout 参数不生效。

        ```
        :param output: bool, 在终端上显示命令输出，默认 False。

        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为 None 表示无限制，默认 None。

        :return: lsit[tuple[str, str]] or list[], 包含(第三方包名, 版本)元组的列表或空列表。
        ```

        `timeout 参数值小于1则抛出 ValueError 异常；`

        `timeout 参数数据类型不是 int 或 float 或 None 则抛出 TypeError 异常。`
        """
        if not self.pip_ready:
            return []
        self.__check_timeout_num(timeout)
        result, retcode = self.__execute(
            Command(self.interpreter, *_PIPCMDS["LIST"]), output, timeout
        )
        if retcode or not result:
            return []
        return self.__cleanup_info(result)

    def pkg_names(self, *, output=False, timeout=None):
        """
        ### 获取该 Python 目录下已安装的包名列表，没有获取到包名列表则返回空列表。

        请注意，如果 output 参数值为 True，则 timeout 参数不生效。

        ```
        :param output: bool, 在终端上显示命令输出，默认 False。

        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为 None 表示无限制，默认 None。

        :return: list[str...] or lsit[], 包含包名的列表或空列表。
        ```

        `timeout 参数值小于 1 则抛出 ValueError 异常。`

        `timeout 参数数据类型不是 int 或 float 或 None 则抛出 TypeError 异常。`
        """
        if not self.pip_ready:
            return []
        self.__check_timeout_num(timeout)
        result, retcode = self.__execute(
            Command(self.interpreter, *_PIPCMDS["LIST"]), output, timeout
        )
        if retcode or not result:
            return []
        return [n for n, _ in self.__cleanup_info(result)]

    def outdated(self, *, output=False, timeout=60):
        """
        ### 获取可更新的包列表。

        列表包含(包名, 已安装版本, 最新版本, 安装包类型)，如果没有获取到或者没有可更新的包，返回空列表。

        检查更新时，耗时多少与环境中已安装的包数量有关，也与 PyPi 镜像地址的连通流畅度有关，请耐心等待。

        请注意，如果 output 参数值为 True，则 timeout 参数不生效。

        ```
        :param output: bool, 在终端上显示命令输出，默认 False。

        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为 None 表示无限制，默认 None。

        :return: lsit[tuple[str, str, str, str]] or lsit[]，包含(包名, 已安装版本, 最新版本, 安装包类型)的列表或空列表。
        ```

        `timeout 参数值小于1则抛出 ValueError 异常。`

        `timeout 参数数据类型不是 int 或 float 或 None 则抛出 TypeError 异常。`
        """
        if not self.pip_ready:
            return []
        self.__check_timeout_num(timeout)
        outdated_pkgs_info = []
        result, retcode = self.__execute(
            Command(self.interpreter, *_PIPCMDS["OUTDATED"]), output, timeout
        )
        if retcode or not result:
            return outdated_pkgs_info
        result = result.strip().split("\n")
        pat_1 = r"^(\S+)\s+(\S+)\s+(\S+)\s+(sdist|wheel)$"
        pat_2 = r"^(\S+) \((\S+)\) - Latest: (\S+) \[(sdist|wheel)\]$"
        for pkg_ver_info in result:
            res = re.match(pat_1, pkg_ver_info)
            if res:
                outdated_pkgs_info.append(res.groups())
        if not outdated_pkgs_info:
            for pkg_ver_info in result:
                res = re.match(pat_2, pkg_ver_info)
                if res:
                    outdated_pkgs_info.append(res.groups())
        return outdated_pkgs_info

    def upgrade_pip(self, *, index_url="", output=False, timeout=None):
        """
        ### 升级 pip。

        请注意，如果 output 参数值为 True，则 timeout 参数不生效。

        ```
        :param index_url: str, 镜像源地址，可为空字符串，默认使用系统内设置的全局镜像源。

        :param output: bool, 在终端上显示命令输出，默认 False

        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为 None 表示无限制，默认 None。

        :return: tuple[tuple['pip'], bool], 返回(('pip',), 退出状态)元组，退出状态为 True 表示升级成功，False 表示失败。
        ```

        `timeout 参数值小于1则抛出 ValueError 异常。`

        `timeout 参数数据类型不是 int 或 float 或 None 则抛出 TypeError 异常。`
        """
        if not self.pip_ready:
            return False
        self.__check_timeout_num(timeout)
        cmds = Command(self.interpreter, *_PIPCMDS["PIPUP"])
        if index_url:
            cmds.extend(("-i", index_url))
        retcode = self.__execute(cmds, output, timeout)[1]
        return ("pip",), not retcode

    def set_global_index(self, index_url=index_urls["tencent"]):
        """
        ### 设置 pip 全局镜像源地址。

        ```
        :param index_url: str, 镜像源地址，参数可省略。
        :return: bool, 退出状态，True 表示设置成功，False 表示设置失败。
        ```

        `参数 index_url 类型不是 str 则抛出 TypeError 异常。`
        """
        if not self.pip_ready or not index_url:
            return False
        if not isinstance(index_url, str):
            raise TypeError("镜像源地址参数的数据类型应为字符串。")
        return not self.__execute(
            Command(self.interpreter, *_PIPCMDS["SETINDEX"], index_url), False, None
        )[1]

    def get_global_index(self):
        """
        ### 获取当前 pip 全局镜像源地址。

        ```
        :return: str, 当前系统 pip 全局镜像源地址。
        ```
        """
        if not self.pip_ready:
            return EMPTY_STR
        result, retcode = self.__execute(
            Command(self.interpreter, *_PIPCMDS["GETINDEX"]), False, None
        )
        if retcode:
            return EMPTY_STR
        match_res = re.match(r"^global.index-url='(.+)'$", result)
        if not match_res:
            return EMPTY_STR
        return match_res.group(1)

    def install(self, *names, **kwargs):
        """
        ### 安装 Python 第三方包。

        包名 names 必须提供，其他参数可以省略，但除了 names 参数，其他需要指定的参数需以关键字参数方式指定。

        注意：包名 names 中只要有一个不可安装(无资源等原因)，其他包也不会被安装。

        所以如果不能保证 names 中所有的包都能被安装，那最好每次只传入一个包名，循环调用 install 方法安装所有的包。

        请注意，如果 output 参数值为 True，则 timeout 参数不生效。

        ```
        :param names: str, 第三方包名(可变数量参数)。

        :param strategy: 'eager' or 'needed', 依赖库的升级策略，'eager'：总是升级依赖库，'needed'：仅当依赖库不满足要求时才升级。默认「仅在需要时」。

        :param index_url: str, pip 镜像源地址。

        :param upgrade: bool, 是否以升级模式安装。如果之前已安装该包，则升级模式会卸载旧版本安装新版本，反之会跳过安装，不安装新版本。

        :param force_reinstall: bool, 是否强制重装该包（包括强制重装该包的所有依赖）

        :param pre: bool, 查找目标是否包括预发行版和开发版，默认 False，即仅查找稳定版。

        :param user: bool, 是否安装到您平台的 Python 用户安装目录，通常是 '~/.local/' 或 '％APPDATA％Python'，默认 False。

        :param compile: bool or 'auto', 是否将 Python 源文件编译为字节码，默认 'auto'，由 pip 决定。

        :param output: bool, 在终端上显示命令输出，默认 False。

        :param timeout: int or float, 任务超时限制，单位为秒，可设为 None 表示无限制，默认 None。

        :return: tuple[tuple[str...], bool], 返回((包名...), 退出状态)元组。但包名 names 中只要有一个包不可安装，则所有传入的包名都不会被安装，且退出状态为 False。
        ```

        `所有包名中有非 str 类型数据则抛出 TypeError 异常;`

        `index_url 数据类型非 str 则抛出 TypeError 异常;`

        `timeout 参数值小于 1 则抛出 ValueError 异常;`

        `timeout 参数数据类型不是 int 或 float 或 None 则抛出 TypeError 异常；`
        """
        if not self.pip_ready or not names:
            return tuple()
        (
            install_pre,
            index_url,
            timeout,
            upgrade,
            output,
            install_user,
            compile_sc,
            upgrade_strategy,
            force_reinstall,
        ) = (
            kwargs.get("pre", False),
            kwargs.get("index_url", EMPTY_STR),
            kwargs.get("timeout", None),
            kwargs.get("upgrade", False),
            kwargs.get("output", False),
            kwargs.get("user", False),
            kwargs.get("compile", "auto"),
            kwargs.get("strategy", None),
            kwargs.get("force_reinstall", False),
        )
        if not all(isinstance(s, str) for s in names):
            raise TypeError("包名参数的数据类型应为字符串。")
        if not isinstance(index_url, str):
            raise TypeError("镜像源地址参数数据类型应为字符串。")
        self.__check_timeout_num(timeout)
        if upgrade_strategy not in (None, "eager", "needed"):
            raise ValueError("strategy 参数可选值为 'eager'、'needed' 或 None。")
        cmds = Command(self.interpreter, *_PIPCMDS["INSTALL"], *names)
        if install_pre:
            cmds.append("--pre")
        if upgrade:
            cmds.append("-U")
        if index_url:
            cmds.extend(("-i", index_url))
        if install_user:
            cmds.append("--user")
        if upgrade_strategy:
            cmds.extend(("--upgrade-strategy", upgrade_strategy))
        if force_reinstall:
            cmds.append("--force-reinstall")
        if compile_sc == "auto":
            pass
        elif compile_sc:
            cmds.append("--compile")
        else:
            cmds.append("--no-compile")
        return names, not self.__execute(cmds, output, timeout)[1]

    def uninstall(self, *names, **kwargs):
        """
        ### 卸载 Python 第三方包。

        请注意，如果 output 参数值为 True，则 timeout 参数不生效。

        ```
        param names: str, 不定长参数。要卸载的包名，可以传入多个包名，此参数必选。

        param output: bool, 在终端上显示命令输出，默认 False。

        param timeout: int or float, 任务超时限制，单位为秒，可设为 None 表示无限制，默认 None。

        return: tuple[tuple[str...], bool]。返回((包名...), 退出状态)元组，状态不为 True 则表示卸载失败。
        注意：如果 names 中包含未安装的包则跳过卸载，退出状态仍为 True。
        ```

        `所有包名中有非 str 类型数据则抛出 TypeError 异常;`

        `timeout 参数值小于1则抛出 ValueError 异常;`

        `timeout 参数数据类型不是 int 或 float 或 None 则抛出 TypeError 异常。`
        """
        if not self.pip_ready or not names:
            return tuple()
        output = kwargs.get("output", False)
        timeout = kwargs.get("timeout", None)
        if not all(isinstance(s, str) for s in names):
            raise TypeError("包名参数的数据类型应为字符串。")
        self.__check_timeout_num(timeout)
        cmds = Command(self.interpreter, *_PIPCMDS["UNINSTALL"], *names)
        return names, not self.__execute(cmds, output, timeout)[1]

    def download(self, *names, **kwargs):
        """
        ### 下载指定的包。

        提示：当使用 python_version、platform、abis 或 implementation 参数约束平台和解释器时，必须设置 no_deps 参数值为 True，不能设置 only_binary 参数，不能设置 no_binary 参数。

        请注意，如果 output 参数值为 True，则 timeout 参数不生效。

        ```
        :param names: str, 不定长参数。包名，可同时传入多个包名，此参数必选。

        :param no_deps: bool, 关键字参数。不下载依赖项，默认 False。

        :param no_binary: tuple|list[str...], 关键字参数。不使用二进制包，即只下载源代码包。参数值应为包含出现在 names 中的包名的列表或元组，默认 None。注意，某些软件包很难编译，下载的源代码包可能无法用来安装。

        :param only_binary: tuple|list[str...], 关键字参数。不使用源代码包，即只下载二进制包。参数值应为包含出现在 names 中的包名的列表或元组，默认 None。注意，如果该参数值列表中的包没有二进制分发版，则设置此参数后将无法下载。

        :param prefer_binary: bool, 关键字参数。与较新的源代码包相比，宁愿下载较旧版本的二进制包。默认 False。

        :param pre: bool, 关键字参数。包括预发行版本和开发版本，默认 False。

        :param ignore_require_python: bool , 关键字参数。忽略包的 Requires-Python 信息，默认 False。

        :param dest: str, 关键字参数，下载文件的保存目录路径。如果不指定此参数、参数值为 None 或值为磁盘根目录，则默认下载至 '/用户目录/Downloads/pip_downloads-xxx' 文件夹；如果 dest 的值不是完整路径，则下载至 '用户目录/Downloads/'+ dest' 文件夹；如果 dest 为完整路径：如果 dest 是文件路径，则下载至该文件所在的文件夹，否则下载至该文件夹。如果路径不存在，将会尝试创建文件夹。

        :param platform: tuple|list[str...], 关键字参数，仅下载与 platform 中列出的平台兼容的包，默认 None，即仅下载与当前系统兼容的安装包。

        :param python_version: str, 关键字参数，用于 wheel 和 'Requires-Python' 兼容性检查的 Python 解释器版本。默认为从当前环境的解释器派生的版本。最多可以使用三个以点号分隔的整数来指定版本(例如，'3' 代表 3.0.0，'3.7' 代表 3.7.0 或 3.7.3)。主次版本也可以不带点的字符串形式给出(例如，'37' 代表 3.7.0)。

        :param implementation: str, 关键字参数。仅下载与指定 Python 实现兼容的二进制包，例如 'pp'，'jy'，'cp' 或 'ip'。如果未指定，则使用当前环境的解释器实现。使用 'py' 强制指定与实现无关的二进制包。默认 None。

        :param abis: tuple|list[str...], 关键字参数。仅下载与指定 Python ABI 兼容的包，例如 'pypy_41'。如果未指定，则使用当前环境的解释器 abi 标签。通常，使用此参数时，需要同时指定 platform、python_version、implementation 3 个参数的值。

        :param index_url: str, 关键字参数，镜像源地址，默认 None。

        :param output: bool, 关键字参数，在终端上显示命令输出，默认 False。

        :param timeout: int or float, 关键字参数，任务超时时长限制，单位为秒，可设为 None 表示无限制，默认 None。

        :return: tuple(bool, str), 返回(是否下载成功, 文件保存路径)元组。如果下载失败(False)，则返回的元组中，文件保存路径为空字符串。
        ```
        """
        if not self.pip_ready or not names:
            return tuple()
        (
            no_deps,
            no_binary,
            only_binary,
            prefer_binary,
            pre,
            ignore_requires_python,
            dest,
            platform,
            python_version,
            implementation,
            abis,
            index_url,
            output,
            timeout,
        ) = (
            kwargs.get("no_deps", False),
            kwargs.get("no_binary", None),
            kwargs.get("only_binary", None),
            kwargs.get("prefer_binary", False),
            kwargs.get("pre", False),
            kwargs.get("ignore_requires_python", False),
            kwargs.get("dest", None),
            kwargs.get("platform", None),
            kwargs.get("python_version", None),
            kwargs.get("implementation", None),
            kwargs.get("abis", None),
            kwargs.get("index_url", None),
            kwargs.get("output", False),
            kwargs.get("timeout", None),
        )
        NoneType = type(None)
        if not all(isinstance(s, str) for s in names):
            raise TypeError("包名参数类型应为字符串。")
        clean_package_name = parse_package_names(names)
        if not isinstance(no_binary, (tuple, list, NoneType)):
            raise TypeError("no_binary 参数值的数据类型应为 'tuple'、'list' 或值为 'None'。")
        if not (
            isinstance(no_binary, NoneType)
            or all(n in clean_package_name for n in no_binary)
        ):
            raise ValueError("no_binary 参数值不应包含不在 names 中的包名(不包含版本限制符号)。")
        if not isinstance(only_binary, (tuple, list, NoneType)):
            raise TypeError("only_binary 参数值的数据类型应为 'tuple'、'list' 或值为 'None'。")
        if not (
            isinstance(only_binary, NoneType)
            or all(n in clean_package_name for n in only_binary)
        ):
            raise ValueError("only_binary 参数值不应包含不在 names 中的包名(不包含版本限制符号)。")
        if not isinstance(dest, (str, NoneType)):
            raise TypeError("dest 参数值的数据类型应为 'str' 或值应为 'None'。")
        if not isinstance(platform, (tuple, list, NoneType)):
            raise TypeError("参数 platform 值类型应为 'tuple'、'list' 或值为 'None'。")
        if not (
            isinstance(platform, NoneType) or all(isinstance(s, str) for s in platform)
        ):
            raise TypeError("参数 platform 值应为一个包含字符串的元组或列表。")
        if not isinstance(python_version, (str, NoneType)):
            raise TypeError("参数 python_version 值类型应为 'str' 或值为 'None'。")
        if not isinstance(implementation, (str, NoneType)):
            raise TypeError("参数 implementation 值类型应为 'str' 或值为 'None'。")
        if not isinstance(abis, (tuple, list, NoneType)):
            raise TypeError("参数 abi 值类型应为 'tuple'、'list' 或值为 'None'。")
        if not (isinstance(abis, NoneType) or all(isinstance(s, str) for s in abis)):
            raise TypeError("参数 abi 值应为一个包含字符串的元组或列表。")
        if not isinstance(index_url, (str, NoneType)):
            raise TypeError("参数 index_url 值类型应为 'str' 或值为 'None'。")
        self.__check_timeout_num(timeout)
        while True:
            download_dir_hash = os.path.join(
                self.USER_DOWNLOADS,
                "pip_downloads-{}".format(randint(0x10000000, 0xFFFFFFFF)),
            )
            if not os.path.exists(download_dir_hash):
                break
        if dest:
            dest = os.path.normpath(dest)
            drive, *_ = os.path.splitdrive(dest)
            if not drive:
                dest = os.path.join(self.USER_DOWNLOADS, dest)
            elif os.path.samefile(dest, os.path.dirname(dest)):
                dest = download_dir_hash
            elif os.path.isfile(dest):
                dest = os.path.dirname(dest)
                if os.path.samefile(dest, os.path.dirname(dest)):
                    dest = download_dir_hash
        else:
            dest = download_dir_hash
        if not os.path.exists(dest):
            try:
                os.makedirs(dest)
            except Exception:
                raise PermissionError("文件夹<{}>创建失败。".format(dest))
        cmds = Command(self.interpreter, *_PIPCMDS["DOWNLOAD"], *names)
        if no_deps:
            cmds.append("--no-deps")
        if no_binary:
            cmds.extend(("--no-binary", ",".join(no_binary)))
        if only_binary:
            cmds.extend(("--only-binary", ",".join(only_binary)))
        if prefer_binary:
            cmds.append("--prefer-binary")
        if pre:
            cmds.append("--pre")
        if ignore_requires_python:
            cmds.append("--ignore-requires-python")
        cmds.extend(("--dest", dest))
        if platform:
            for pf in platform:
                cmds.extend(("--platform", pf))
        if python_version:
            cmds.extend(("--python-version", python_version))
        if implementation:
            cmds.extend(("--implementation", implementation))
        if abis:
            for abi in abis:
                cmds.extend(("--abi", abi))
        if index_url:
            cmds.extend(("--index-url", index_url))
        retcode = not self.__execute(cmds, output, timeout)[1]
        return (retcode, dest) if retcode else (retcode, EMPTY_STR)

    def __read_sysinfo(self) -> Tuple[List[str], Tuple[str]]:
        """读取目标环境的 sys.path 和 sys.builtin_module_names 属性。"""
        self.cleanup_old_scripts()
        result, retcode = self.__execute(
            Command(self.interpreter, *CmdRead.SYSINFO.value), False, None
        )
        if retcode or not result:
            return [], ()
        try:
            paths, builtins = result.strip().split("\n")
            return eval(paths.strip()), eval(builtins.strip())
        except Exception:
            return [], ()

    @staticmethod
    def __prefixs_from_pth(fullpath: str) -> set:
        package_paths_relative_site = set()
        if not os.path.isfile(fullpath):
            return package_paths_relative_site
        try:
            with open(fullpath, "rt", encoding="utf-8") as f:
                for line in f:
                    if line.startswith(("#", "import ", "import\t")):
                        continue
                    line = os.path.normcase(line.rstrip())
                    if line:
                        package_paths_relative_site.add(line)
        except Exception:
            pass
        return package_paths_relative_site

    def __refresh_package_importable_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        ### 获取本环境下包名与导入名的映射表并在 PyEnv 实例内缓存。

        ```
        :return: dict[str: set[str...]...]
        ```
        """
        self.__cached_packages_imps.clear()
        if not self.env_path:
            return dict()
        hosts_in_sys_paths, builtin_imps = self.__read_sysinfo()
        for name in builtin_imps:
            self.__cached_packages_imps[name] = {name: EMPTY_STR}
        hosts_files_dirs: Dict[str, Set[str]] = dict()
        # {pth_host: (owner_host, owner_pkg)}
        attributed_hosts: Dict[str, Tuple[str, str]] = dict()
        for pkgs_host in hosts_in_sys_paths:
            if not os.path.isdir(pkgs_host):
                continue
            try:
                filedir_names_inhost = os.listdir(pkgs_host)
            except Exception:
                continue
            pkgs_host = os.path.normcase(pkgs_host)
            if pkgs_host not in hosts_files_dirs:
                hosts_files_dirs[pkgs_host] = set()
            hosts_files_dirs[pkgs_host].update(filedir_names_inhost)
            for fdname in filedir_names_inhost:
                fdpath = os.path.join(pkgs_host, fdname)
                if os.path.isfile(fdpath) and fdname.lower().endswith(".pth"):
                    each_pth_prefs = self.__prefixs_from_pth(fdpath)
                    if not each_pth_prefs:
                        continue
                    pthname_matched = self.__canonical_imp_pattern.match(fdname)
                    if not pthname_matched:
                        continue
                    owner_pkg = pthname_matched.group()
                    for suffix in each_pth_prefs:
                        suffix = os.path.normcase(suffix)
                        pth_host = os.path.join(pkgs_host, suffix)
                        attributed_hosts[pth_host] = (pkgs_host, owner_pkg)
        # {pkgs_host: {impname: (fullpath, filename)}}
        pkgsmods_perhost: Dict[str, Dict[str, Tuple[str, str]]] = dict()
        for pkgs_host, fdnames_inhost in hosts_files_dirs.items():
            if pkgs_host in attributed_hosts:
                main_host = attributed_hosts[pkgs_host][0]
            else:
                main_host = pkgs_host
            if main_host not in pkgsmods_perhost:
                pkgsmods_perhost[main_host] = dict()
            for fdname in fdnames_inhost:
                fdpath = os.path.join(pkgs_host, fdname)
                if os.path.isdir(fdpath):
                    if self.__full_canonical_imp_pattern.match(fdname):
                        pkgsmods_perhost[main_host][fdname] = (fdpath, fdname)
                elif os.path.isfile(fdpath) and fdname.lower().endswith(
                    (".py", ".pyc", ".pyd", "pyw")
                ):
                    module_matched = self.__module_pattern.match(fdname)
                    if not module_matched:
                        continue
                    module_name = module_matched.group(1)
                    pkgsmods_perhost[main_host][module_name] = (fdpath, fdname)
        proced_fdnames: Dict[str, Set[str]] = dict()
        for pkgs_host, fdnames_inhost in hosts_files_dirs.items():
            if pkgs_host in attributed_hosts:
                main_host = attributed_hosts[pkgs_host][0]
            else:
                main_host = pkgs_host
            pkgsmods_thishost = pkgsmods_perhost.get(main_host, dict())
            each_host_proced = proced_fdnames.setdefault(main_host, set())
            for fdname in fdnames_inhost:
                dir_fullpath = os.path.join(pkgs_host, fdname)
                if not os.path.isdir(dir_fullpath):
                    continue
                if fdname.endswith(".dist-info"):
                    info_file = "METADATA"
                elif fdname.endswith(".egg-info"):
                    info_file = "PKG-INFO"
                else:
                    continue
                each_host_proced.add(fdname)
                info_fullpath = os.path.join(dir_fullpath, info_file)
                if not os.path.exists(info_fullpath):
                    continue
                try:
                    with open(info_fullpath, "rt", encoding="utf-8") as f:
                        metadata_lines = f.readlines()
                except Exception:
                    continue
                name_pkginfo_matched = EMPTY_STR
                for line in metadata_lines[1:]:
                    name_pkginfo_matched = self.__info_pkgname_pattern.match(line)
                    if name_pkginfo_matched:
                        break
                if not name_pkginfo_matched:
                    continue
                pkg_importables: Dict[str, str] = dict()
                realname = name_pkginfo_matched.group(1)
                if PKG_SEPDOT in realname:
                    imppath = os.path.join(
                        pkgs_host, realname.replace(".", os.path.sep)
                    )
                    pkg_importables[realname] = imppath
                toplevel_txt = os.path.join(dir_fullpath, "top_level.txt")
                if not os.path.exists(toplevel_txt):
                    impname_matched = self.__canonical_imp_pattern.match(
                        realname.replace("-", "_")
                    )
                    if not impname_matched:
                        continue
                    impname = impname_matched.group()
                    if impname not in pkgsmods_thishost:
                        continue
                    pkgimppath = pkgsmods_thishost[impname]
                    if realname not in self.__cached_packages_imps:
                        self.__cached_packages_imps[realname] = dict()
                    self.__cached_packages_imps[realname][impname] = pkgimppath[0]
                    each_host_proced.add(pkgimppath[1])
                    continue
                try:
                    with open(toplevel_txt, "rt", encoding="utf-8") as tt:
                        toplevel_txt_lines = tt.readlines()
                    for line in toplevel_txt_lines:
                        prefix, suffix = os.path.split(line.rstrip())
                        toplevel_imp_matched = self.__canonical_imp_pattern.match(
                            suffix
                        )
                        if not toplevel_imp_matched:
                            continue
                        impname_in_toplevel = toplevel_imp_matched.group()
                        if impname_in_toplevel not in pkgsmods_thishost:
                            continue
                        pkgimppath = pkgsmods_thishost[impname_in_toplevel]
                        pkg_importables[impname_in_toplevel] = pkgimppath[0]
                        each_host_proced.add(pkgimppath[1])
                except Exception:
                    pass
                if realname not in self.__cached_packages_imps:
                    self.__cached_packages_imps[realname] = dict()
                self.__cached_packages_imps[realname].update(pkg_importables)
        for pkgs_host, fdnames_inhost in hosts_files_dirs.items():
            if pkgs_host in attributed_hosts:
                main_host, pkgname = attributed_hosts[pkgs_host]
            else:
                main_host, pkgname = pkgs_host, None
            pkgsmods_thishost = pkgsmods_perhost.get(main_host, dict())
            each_host_proced = proced_fdnames.setdefault(main_host, set())
            for fdname in fdnames_inhost:
                if fdname in each_host_proced:
                    continue
                fdpath = os.path.normcase(os.path.join(pkgs_host, fdname))
                if fdpath in attributed_hosts:
                    temp_host, temp_pkgname = attributed_hosts[fdpath]
                    temp_pkgsmods = pkgsmods_perhost.get(temp_host, dict())
                else:
                    temp_pkgname = pkgname
                    temp_pkgsmods = pkgsmods_thishost
                flag_fdname_canonical = False
                for canon_name, pathfile in temp_pkgsmods.items():
                    if fdname == pathfile[1]:
                        flag_fdname_canonical = True
                        break
                if not flag_fdname_canonical:
                    continue
                final_pkgname = temp_pkgname if temp_pkgname else canon_name
                if final_pkgname not in self.__cached_packages_imps:
                    self.__cached_packages_imps[final_pkgname] = dict()
                self.__cached_packages_imps[final_pkgname][canon_name] = pathfile[0]
        return self.__cached_packages_imps

    def __check_refresh_requirements(self, fresh):
        if fresh:
            self.__cached_packages_imps.clear()
        else:
            if (
                time.time() - self.__time_last_activity
                > PyEnv._cache_refresh_maximum_interval
            ):
                self.__cached_packages_imps.clear()
        self.__time_last_activity = time.time()
        if not self.__cached_packages_imps:
            self.__refresh_package_importable_mapping()

    def ensurepip(self, output=False):
        """
        ### 此方法用于当环境中没有 pip 模块时使用副本恢复 pip。

        是否能恢复成功取决于该环境是否缓存了 pip 副本。

        请注意，恢复的 pip 并不一定是最新版，如果想更新 pip，请接着调用 upgrade_pip 方法。
        """
        if not self.env_path:
            return False
        scripts_dir_path = self.scripts_path()
        pipexe_path = os.path.join(scripts_dir_path, PIP_EXE)
        pip3exe_path = os.path.join(scripts_dir_path, "pip3.exe")
        cmds = Command(self.interpreter, *_PIPCMDS["ENSUREPIP"])
        bool_result = not self.__execute(cmds, output, None)[1]
        if (
            bool_result
            and os.path.isfile(pip3exe_path)
            and (not os.path.isfile(pipexe_path))
        ):
            try:
                shutil.copy(pip3exe_path, pipexe_path)
            except Exception:
                pass
        return bool_result

    def scripts_home(self):
        """
        ### 返回 Python 环境的 Scripts 目录的路径，如果 Python 环境无效，则返回空字符串。
        此方法与 scripts_path 方法一模一样。
        """
        if not self.env_path:
            return EMPTY_STR
        return os.path.join(self.env_path, PYTHON_SCR)

    def scripts_path(self):
        """
        ### 返回 Python 环境的 Scripts 目录的路径，如果 Python 环境无效，则返回空字符串。
        此方法与 scripts_home 方法一模一样。
        """
        return self.scripts_home()

    def names_for_import(self, fresh=False):
        """
        ### 获取本 Python 环境下的包/模块可用于 import 语句的名称列表。

        此方法返回的名称列表中可能有重复项，且不保证列表中所有的名称用于 import 语句时都可以成功导入。

        ```
        :param fresh: bool, 控制是否刷新缓存再查询，如果为 False 则不主动刷新，如果缓存寿命(3s)超时或者没有缓存则会强制刷新。
        当需要循环调用这个方法时，将这个参数设为 False 以加快查询速度。

        return: set[str...]，可用于 import 语句的名称集合。
        ```
        """
        if not self.env_path:
            return set()
        self.__check_refresh_requirements(fresh)
        pkg_import_names = set()
        for imppath in self.__cached_packages_imps.values():
            pkg_import_names.update(imppath.keys())
        return pkg_import_names

    def query_for_import(self, module_or_pkg_name: str, *, case=True, fresh=False):
        """
        ### 通过包名称查询该包用于 import 语句的名称。

        例如 Windows API 包 pywin32，import 语句使用 win32api、win32con 等名称而非 import pywin32，

        此方法可以使用 'pywin32' 作为 module_or_pkg_name 参数，查询得到 ['win32api', 'win32con'...] 这样的结果。

        此方法不保证返回的名称列表中所有的名称用于 import 语句时都可以成功导入。

        ```
        :param module_or_pkg_name: str, 想要查询的包名、模块名。

        :param case: bool, 是否对 module_or_pkg_name 大小写敏感。

        :param fresh: bool, 控制是否刷新缓存再查询，如果为 False 则不主动刷新，如果缓存寿命(3s)超时或者没有缓存则会强制刷新。
        当你需要循环调用 query_for_import 方法查询大量 module_or_pkg_name 时，将此参数设为 False 可以使用缓存以加快查询速度。

        :return: List[str], 该包、模块的用于 import 语句的名称列表。
        ```

        包名非 str 则抛出 TypeError 异常。
        """
        if not self.env_path:
            return list()
        if not isinstance(module_or_pkg_name, str):
            raise TypeError("参数 1 数据类型错误，数据类型应为 str")
        self.__check_refresh_requirements(fresh)
        for publish_name, value in self.__cached_packages_imps.items():
            if case:
                cased_value = publish_name
            else:
                cased_value = publish_name.lower()
                module_or_pkg_name = module_or_pkg_name.lower()
            if module_or_pkg_name == cased_value:
                return list(value.keys())
        return list()

    def query_for_import_path(self, module_or_pkg_name: str, *, case=True, fresh=False):
        """
        ### 通过包名称查询该包用于 import 语句的名称和路径（文件或目录路径）字典。

        例如 Windows API 包 pywin32，import 语句使用 win32api、win32con 等名称而非 import pywin32，

        此方法可以使用 'pywin32' 作为 module_or_pkg_name 参数，查询得到 {'win32api': 路径, 'win32con': 路径...} 这样的结果。

        此方法不保证返回的(名称, 路径)列字典中所有的名称用于 import 语句时都可以成功导入，不保证路径都存在。

        ```
        :param module_or_pkg_name: str, 想要查询的包名、模块名。

        :param case: bool, 是否对 module_or_pkg_name 大小写敏感。

        :param fresh: bool, 控制是否刷新缓存再查询，如果为 False 则不主动刷新，如果缓存寿命(3s)超时或者没有缓存则会强制刷新。
        当你需要循环调用 query_for_import 方法查询大量 module_or_pkg_name 时，将此参数设为 False 可以使用缓存以加快查询速度。

        :return: Dict[str, str], 该包、模块的用于 import 语句的(名称, 路径)字典。
        ```

        包名非 str 则抛出 TypeError 异常。
        """
        if not self.env_path:
            return dict()
        if not isinstance(module_or_pkg_name, str):
            raise TypeError("参数 1 数据类型错误，数据类型应为 str")
        self.__check_refresh_requirements(fresh)
        for publish_name, value in self.__cached_packages_imps.items():
            if case:
                cased_value = publish_name
            else:
                cased_value = publish_name.lower()
                module_or_pkg_name = module_or_pkg_name.lower()
            if module_or_pkg_name == cased_value:
                return value.copy()
        return dict()

    def query_for_install(self, name_used_for_import, *, case=True, fresh=False):
        """
        ### 通过 import 语句所使用的名称反向查询该名称对应的包名。

        因为不是所有的包/模块的安装名称和用于导入的名称都是一样的，比如 pywin32，使用时就是 import win32api 等。

        此方法功能就像输入 'win32api' 或 'win32con' 作为 name_used_for_import 参数，反查得到 'pywin32'。

        此方法不保证查询的结果一定正确。

        ```
        :param name_used_for_import: str, import 语句所使用的模块名称。

        :param case: bool, 是否对 name_used_for_import 大小写敏感。

        :param fresh: bool, 控制是否刷新缓存后查询，如果为 False 则不主动刷新，如果缓存寿命(3s)超时或者没有缓存则会强制刷新。
        当你需要循环调用 query_for_install 方法查询大量 name_used_for_import 时，将此参数设为 False 可以使用缓存以加快查询。

        :return: str, 包的名称，该名称一般用于安装，比如用于 pip 命令安装等。
        ```
        """
        if not self.env_path:
            return EMPTY_STR
        if not isinstance(name_used_for_import, str):
            raise TypeError("参数 1 类型错误，类型应为 str")
        self.__check_refresh_requirements(fresh)
        for publish_name, value in self.__cached_packages_imps.items():
            if case:
                cased_value = value
            else:
                name_used_for_import = name_used_for_import.lower()
                cased_value = {i.lower() for i in value.keys()}
            if name_used_for_import in cased_value:
                return publish_name
        return EMPTY_STR

    def pkgimp_mapping(self, fresh=False):
        """
        ### 获取本环境下包名与导入名的映射表

        ```
        :param fresh: bool, 控制是否刷新缓存后查询，如果为 False 则不主动刷新，如果缓存寿命(3s)超时或者没有缓存则会强制刷新。
        如果需要在极短时间内循环调用这个方法且没有刷新需求，则把 fresh 参数设为 False 可以加快查询速度。

        :return: dict[pkg_name: str, imp_names: set[str]], 包名与导入名映射表
        ```
        """
        self.__check_refresh_requirements(fresh)
        return deepcopy(self.__cached_packages_imps)

    @staticmethod
    def __clear_freezed_info(string: str):
        if not string:
            return string
        clean_lines = list()
        for line in string.splitlines():
            if "@" not in line:
                clean_lines.append(line)
                continue
            line_matched = re.match(r"^.+(?= @ file:)", line)
            if not line_matched:
                continue
            clean_lines.append(line_matched.group())
        return "\n".join(clean_lines)

    def freeze(
        self,
        dir_path: str,
        file_name: str = None,
        no_path: bool = False,
        user: bool = False,
        all_pkg: bool = False,
    ):
        """
        ### 导出已安装的包信息到指定目录或文件

        注意：已存在的同名文件会被直接覆盖

        ```
        :param dir_path: str, 已安装的包信息文本文件要保存的目录路径
        :param file_name: str or None，要保存的文件名，默认 None
        :param no_path: bool, 是否过滤掉包信息中的路径信息（从本地文件安装的包，导出的信息中会带有安装时安装包的文件路径：'@ file:///...' ）
        :param user: bool, 是否只导出安装在用户目录中的包信息，默认 False
        :param all_pkg: bool, 不跳过这些包的信息：pip, setuptools, distribute, wheel，默认 False
        :return: bool, 本方法的执行结果，成功返回 True，失败返回 False
        ```
        """
        if not self.pip_ready:
            return False
        if not isinstance(dir_path, str):
            raise TypeError("参数 1 必须是 str 类型")
        if file_name is None:
            file_name = DEFAULT_REQNAME
        if not isinstance(file_name, str):
            raise TypeError("参数 2 必须是 None 或 str 类型")
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        elif not os.path.isdir(dir_path):
            raise ValueError("参数 1 不是一个文件夹路径")
        file_fullpath = os.path.join(
            os.path.normcase(dir_path), file_name or DEFAULT_REQNAME
        )
        command = Command(self.interpreter, *_PIPCMDS["FREEZE"])
        if all_pkg:
            command.append("--all")
        if user:
            command.append("--user")
        string, result = self.__execute(command, False, None)
        if result:
            return False
        if no_path:
            string = self.__clear_freezed_info(string)
        try:
            with open(file_fullpath, "wt", encoding="utf-8") as rfo:
                rfo.write(string)
            return True
        except Exception:
            return False

    def site_packages_home(self) -> str:
        """### 返回全局第三方包安装目录的完整路径"""
        if not self.env_is_valid:
            return EMPTY_STR
        command = Command(self.interpreter, *CmdRead.SITES.value)
        string, result = self.__execute(command, False, None)
        if not string or result:
            return EMPTY_STR
        str_matched = self.__sitepkg_pattern.search(string)
        if str_matched is None:
            return EMPTY_STR
        site_list: List[str] = eval(str_matched.group())
        if not isinstance(site_list, list):
            return EMPTY_STR
        for site_string in site_list:
            if site_string.lower().endswith(SITEPKG_NAME.lower()):
                return site_string
        return EMPTY_STR

    def user_site_packages_home(self) -> str:
        """### 返回用户侧第三方包安装目录的完整路径"""
        if not self.env_is_valid:
            return EMPTY_STR
        command = Command(self.interpreter, *CmdRead.USERSITE.value)
        string, result = self.__execute(command, False, None)
        if result:
            return EMPTY_STR
        return string.strip()
