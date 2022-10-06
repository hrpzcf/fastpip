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
from subprocess import PIPE, STARTF_USESHOWWINDOW, STARTUPINFO, STDOUT, SW_HIDE, Popen
from threading import Thread
from typing import Callable

from ..__version__ import VERSION
from ..common.common import *  # 一些常用量
from ..errors.errors import *
from ..utils.cmdutil import Command
from ..utils.findpath import cur_py_path

if os.name != "nt":
    raise UnsupportedPlatform("此模块不支持您当前正在使用的操作系统。")

_INIT_WK_DIR = os.getcwd()
_SHOW_RUNNING_TIPS = True
_STARTUP = STARTUPINFO()
_STARTUP.dwFlags = STARTF_USESHOWWINDOW
_STARTUP.wShowWindow = SW_HIDE


# 预设的PYPI官方源及国内镜像源：
index_urls = {
    "pypi": "https://pypi.org/simple",  # PYPI官方源（国外）
    "tsinghua": "https://pypi.tuna.tsinghua.edu.cn/simple",  # 清华源
    "tencent": "https://mirrors.cloud.tencent.com/pypi/simple",  # 腾讯源
    "aliyun": "https://mirrors.aliyun.com/pypi/simple",  # 阿里源
    "bfsu": "https://mirrors.bfsu.edu.cn/pypi/web/simple",  # 北京外国语大学源
    "opentuna": "https://opentuna.cn/pypi/web/simple",  # 清华源
    "douban": "https://pypi.doubanio.com/simple",  # 豆瓣源
    "huawei": "https://mirrors.huaweicloud.com/repository/pypi/simple",  # 华为源
    "netease": "https://mirrors.163.com/pypi/simple",  # 网易源
}

# 预置部分pip命令字符串元组格式
_PREFIX = ("-m", "pip")
_PIPCMDS = {
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


def _tips_and_wait(tips):
    """### 打印等待中提示信息，返回线程实例。"""

    def _print_tips(tips):
        global _SHOW_RUNNING_TIPS
        num, dot = 0, "."
        while _SHOW_RUNNING_TIPS:
            print("{}{}{}".format(tips, dot * num, "   "), end="\r")
            num = 0 if num == 3 else num + 1
            time.sleep(0.5)
        _SHOW_RUNNING_TIPS = True
        print("{}".format("  " * (len(tips) + 3)), end="\r")

    tips_thread = Thread(target=_print_tips, args=(tips,))
    tips_thread.start()
    return tips_thread


def _execute_cmd(cmds, tips, no_output, no_tips, timeout):
    """### 执行命令，输出等待提示语、输出命令执行结果并返回。"""
    global _SHOW_RUNNING_TIPS
    if not no_tips:
        tips_thread = _tips_and_wait(tips)
    env = cmds.environment()
    cwd = os.path.dirname(cmds.executable)
    try:
        process = Popen(
            cmds,
            stdout=PIPE,
            stderr=STDOUT,
            text=True,
            startupinfo=_STARTUP,
            cwd=cwd,
            env=env,
        )
        out_put = process.communicate(timeout=timeout)[0]
        return_code = process.returncode
    except Exception:
        out_put, return_code = "", 1
    if not no_tips:
        _SHOW_RUNNING_TIPS = False
        tips_thread.join()
    if not no_output:
        print(out_put, end="")
    return out_put, return_code


def parse_package_names(names):
    """
    ### 排除列表中包名的版本号限制符。

    例如传入['fastpip>=0.5,<0.8']，返回['fastpip']。
    """
    package_names = list()
    pt = re.compile(r"[^\<\>\=\,]+")
    for n in names:
        m_obj = pt.match(n)
        if not m_obj:
            continue
        package_names.append(m_obj.group())
    return package_names


class PyEnv:
    """
    ### Python环境类。

    此类实例的绝大多数方法效果都将作用于该实例所指的Python环境，不对其他环境产生影响。

    只有一个例外：使用set_global_index方法设置本机pip全局镜像源地址，对所有环境产生作用。
    """

    __OUTPUT_CALLBACK = None
    _HOME = os.path.join(
        os.getenv("HOMEDRIVE", EMPTY_STR), os.getenv("HOMEPATH", EMPTY_STR)
    )
    USER_DOWNLOADS = os.path.join(_HOME or _INIT_WK_DIR, "Downloads")
    FILE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_refresh_maximum_interval = 3

    def __init__(self, path=None):
        """
        ### PyEnv类初始化方法。

        ```
        :param path: str or None, 一个指向Python解释器所在目录的路径，如果是venv创建的虚拟环境，该路径即可以是前者，也可以是Scripts目录的父目录。
        ```

        PyEnv类有参数实例化时，如果参数path数据类型不是"str"或"None"则抛出PathParamError异常。

        PyEnv类无参数实例化时或参数值为None实例化时，使用cur_py_path函数选取系统环境变量PATH中的首个Python目录路径，如果系统环境变量PATH中没有找到Python目录路径，则将路径属性path及env_path设置为空字符串。
        """
        self.__time_last_activity = time.time()
        # 解释器是否在Scripts目录的标识
        self.__pyexe_in_scripts = False
        self.__designated_path = self.__init_path(path)
        self.__cache_pkgs_importables = dict()

    @staticmethod
    def __init_path(_path):
        """
        ### 初始化Python路径。

        `如果路径参数不是字符串，则抛出PathParamError异常。`

        该异常可从fastpip.errors模块导入。
        """
        if isinstance(_path, str):
            return os.path.normpath(_path)
        if _path is None:
            return cur_py_path()
        raise PathParamError("路径参数类型错误。")

    @property
    def path(self):
        """
        ### 代表PyEnv类实例化时所传入的Python环境的绝对路径。

        可重新赋值一个路径(字符串)以改变PyEnv类实例所指的Python环境。

        赋值类型非str则抛出PathParamError异常，该异常可从fastpip.errors模块导入。
        """
        return os.path.abspath(self.__designated_path)

    @path.setter
    def path(self, _path):
        if not isinstance(_path, str):
            raise PathParamError("路径参数类型错误。")
        self.__designated_path = os.path.normpath(_path)

    def __check(self, _path):
        """### 检查参数path在当前是否是一个有效的Python目录路径。"""
        _path = os.path.abspath(_path)
        # 传入的目录内没有python.exe可执行文件则进入此分支
        if not os.path.isfile(os.path.join(_path, PYTHON_EXE)):
            # 检查是否是venv虚拟环境的Scripts的上级目录
            if os.path.isfile(os.path.join(_path, VENV_CFG)) and os.path.isfile(
                os.path.join(_path, PYTHON_SCR, PYTHON_EXE)
            ):
                self.__pyexe_in_scripts = True
                return os.path.normpath(_path)  # 如是则规范化路径后返回
            return EMPTY_STR  # 如非则路径是无效的，返回空字符串
        # 传入的目录路径内有python.exe则进入此分支
        parent, scripts = os.path.split(_path)
        if parent and scripts:
            # 先判断是否是venv虚拟环境的Scripts目录
            if scripts.lower() == PYTHON_SCR.lower() and os.path.isfile(
                os.path.join(parent, VENV_CFG)
            ):
                self.__pyexe_in_scripts = True
                return os.path.normpath(parent)  # 如是则返回Scripts上级
        return os.path.normpath(_path)  # 如非则可断定非特殊Python环境（？）

    @property
    def env_path(self):
        """
        ### 代表该Python环境目录路径的属性，该属性在获取的时候进行实时检查。

        当PyEnv实例所指的Python环境无效(例如环境被卸载)时该属性值是空字符串，当环境恢复有效后，该属性值是该实例所指Python环境的路径(字符串)。
        """
        return self.__check(self.__designated_path)

    @property
    def interpreter(self):
        """
        ### 属性值为Python解释器(python.exe)路径。

        PyEnv实例所指Python环境无效(例如环境被卸载)时值是空字符串。
        """
        env_path = self.env_path
        if not env_path:
            return EMPTY_STR
        if self.__pyexe_in_scripts:
            return os.path.join(env_path, PYTHON_SCR, PYTHON_EXE)
        return os.path.join(env_path, PYTHON_EXE)

    def __str__(self):
        location = self.env_path or UNKNOWN_LOCATION
        return "{} {} {}".format(self.py_info(), PYENV_SEP_STR, location)

    @property
    def pip_ready(self):
        """
        ### 代表该Python环境中pip是否已安装的属性。

        值为True代表pip已安装，False代表未安装，获取属性值时实时检查是否已安装。
        """
        env_path = self.env_path
        if not env_path:
            return False
        return os.path.isfile(os.path.join(env_path, PIP_INIT))

    @staticmethod
    def __check_timeout_num(timeout):
        if isinstance(timeout, (int, float)):
            if timeout < 1:
                raise ParamValueError("超时参数timeout的值不能小于1。")
            return True
        if timeout is None:
            return True
        raise ParamTypeError("参数timeout值应为None、整数或浮点数。")

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
        """### 获取当前环境Python版本信息。"""
        self.cleanup_old_scripts()
        info = "Python {} :: {} bit"
        if not self.env_path:
            return info.format("0.0.0", "?")
        source_code = "import sys;print(sys.version)"
        _path = os.path.join(self.FILE_DIR, f"ReadPyVER.{VERSION}")
        if not os.path.isfile(_path):
            if not os.path.exists(self.FILE_DIR):
                try:
                    os.makedirs(self.FILE_DIR)
                except Exception:
                    return info.format("0.0.0", "?")
            try:
                with open(_path, "wt", encoding="utf-8") as py_file:
                    py_file.write(source_code)
            except Exception:
                return info.format("0.0.0", "?")
        result, retcode = _execute_cmd(
            Command(self.interpreter, _path), "", True, True, None
        )
        if retcode or not result:
            return info.format("0.0.0", "?")
        # 3.7.14+ (heads/3.7:xxx...) [MSC v.1900 32 bit (Intel)]
        m_obj = re.match(
            r"(\d+\.\d+\.\d+)\+? (?:\(|\|).+(32|64) bit \(.+\)", result, re.S
        )
        if not m_obj:
            return info.format("0.0.0", "?")
        return info.format(*m_obj.groups())

    def pip_path(self):
        """
        ### 根据env_path属性所指的Python安装目录获取pip可执行文件路径。

        如果Scripts目录不存在或无法打开则返回空字符串。

        如果在Scripts目录中没有找到pip可执行文件则返回空字符串。

        ```
        :return: str, 该PyEnv实例所指Python环境的pip可执行文件的完整路径或空字符。
        ```
        """
        env_path = self.env_path
        if not env_path:
            return EMPTY_STR
        dir_pip_exists = os.path.join(env_path, "Scripts")
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
        ### 获取该目录的pip版本信息。

        如果获取到pip版本信息，则返回一个PipInformation实例，可以通过访问实例的pipver、path、pyver属性分别获取到pip版本号、pip目录路径、该pip所在的Python环境版本号。

        如果没有获取到pip信息或获取到信息但未正确匹配到信息格式，则返回None。

        直接打印PipInfo实例则显示概览：pip_info(pip版本、pip路径、相应Python版本)。

        ```
        :return: 匹配到pip版本信息：PipInformation实例；未获取到pip版本信息：返回None。
        ```
        """
        if not self.pip_ready:
            return
        result, retcode = _execute_cmd(
            Command(self.interpreter, *_PIPCMDS["INFO"]),
            tips="",
            no_output=True,
            no_tips=True,
            timeout=None,
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
        """清理pip包名列表命令的无关输出。"""
        preprocessed = re.search(
            r"Package\s+Version\s*\n[-\s]+\n(.+)",
            string,
            re.S,
        )
        if not preprocessed:
            return []
        return re.findall(r"^(\S+)\s+(\S+)\s*$", preprocessed.group(1), re.M)

    def pkgs_info(self, *, no_output=True, no_tips=True, timeout=None):
        """
        ### 获取该Python目录下已安装的包列表，列表包含(包名, 版本)元组，没有获取到则返回空列表。

        ```
        :param no_output: bool, 不在终端上显示命令输出，默认True。

        :param no_tips: bool, 不在终端上显示等待提示信息，默认True。

        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None表示无限制，默认None。

        :return: lsit[tuple[str, str]] or list[], 包含(第三方包名, 版本)元组的列表或空列表。
        ```

        `timeout参数值小于1则抛出ParamValueError异常；`

        `timeout参数数据类型不是int或float或None则抛出ParamTypeError异常。`

        以上异常类可从fastpip.errors模块导入。
        """
        if not self.pip_ready:
            return []
        self.__check_timeout_num(timeout)
        result, retcode = _execute_cmd(
            Command(self.interpreter, *_PIPCMDS["LIST"]),
            "正在获取(包名, 版本)列表",
            no_output,
            no_tips,
            timeout,
        )
        if retcode or not result:
            return []
        return self.__cleanup_info(result)

    def pkg_names(self, *, no_output=True, no_tips=True, timeout=None):
        """
        ### 获取该Python目录下已安装的包名列表，没有获取到包名列表则返回空列表。

        ```
        :param no_output: bool, 不在终端上显示命令输出，默认True。

        :param no_tips: bool, 不在终端上显示等待提示信息，默认True。

        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None表示无限制，默认None。

        :return: list[str...] or lsit[], 包含包名的列表或空列表。
        ```

        `timeout参数值小于1则抛出ParamValueError异常。`

        `timeout参数数据类型不是int或float或None则抛出ParamTypeError异常。`

        以上异常类可从fastpip.errors模块导入。
        """
        if not self.pip_ready:
            return []
        self.__check_timeout_num(timeout)
        result, retcode = _execute_cmd(
            Command(self.interpreter, *_PIPCMDS["LIST"]),
            "正在获取包名列表",
            no_output,
            no_tips,
            timeout,
        )
        if retcode or not result:
            return []
        return [n for n, _ in self.__cleanup_info(result)]

    def outdated(self, *, no_output=True, no_tips=True, timeout=60):
        """
        ### 获取可更新的包列表。
        列表包含(包名, 已安装版本, 最新版本, 安装包类型)元组，如果没有获取到或者没有可更新的包，返回空列表。

        检查更新时，环境中已安装的包越多耗费时间越多，请耐心等待。

        ```
        :param no_output: bool, 不在终端上显示命令输出，默认True。

        :param no_tips: bool, 不在终端上显示等待提示信息，默认True。

        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None表示无限制，默认None。

        :return: lsit[tuple[str, str, str, str]] or lsit[]，包含(包名, 已安装版本, 最新版本, 安装包类型)的列表或空列表。
        ```

        `timeout参数值小于1则抛出ParamValueError异常。`

        `timeout参数数据类型不是int或float或None则抛出ParamTypeError异常。`

        以上异常类可从fastpip.errors模块导入
        """
        if not self.pip_ready:
            return []
        self.__check_timeout_num(timeout)
        outdated_pkgs_info = []
        result, retcode = _execute_cmd(
            Command(self.interpreter, *_PIPCMDS["OUTDATED"]),
            "正在检查更新",
            no_output,
            no_tips,
            timeout,
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

    def upgrade_pip(
        self,
        *,
        index_url="",
        no_output=True,
        no_tips=True,
        timeout=None,
    ):
        """
        ### 升级pip自身。

        ```
        :param index_url: str, 镜像源地址，可为空字符串，默认使用系统内设置的全局镜像源。

        :param no_output: bool, 不在终端上显示命令输出，默认True。

        :param no_tips: bool, 不在终端上显示等待提示信息，默认True。

        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None表示无限制，默认None。

        :return: tuple[tuple['pip'], bool], 返回(('pip',), 退出状态)元组，退出状态为True表示升级成功，False表示失败。
        ```

        `timeout参数值小于1则抛出ParamValueError异常。`

        `timeout参数数据类型不是int或float或None则抛出ParamTypeError异常。`

        以上异常类可从fastpip.errors模块导入。
        """
        if not self.pip_ready:
            return False
        self.__check_timeout_num(timeout)
        cmds = Command(self.interpreter, *_PIPCMDS["PIPUP"])
        if index_url:
            cmds.extend(("-i", index_url))
        retcode = _execute_cmd(cmds, "正在升级pip", no_output, no_tips, timeout)[1]
        return (("pip",), not retcode)

    def set_global_index(self, index_url=index_urls["tencent"]):
        """
        ### 设置pip全局镜像源地址。

        ```
        :param index_url: str, 镜像源地址，参数可省略。
        :return: bool, 退出状态，True 表示设置成功，False 表示设置失败。
        ```

        `参数index_url类型不是str则抛出ParamTypeError异常，该异常类可从fastpip.errors模块导入。`
        """
        if not self.pip_ready or not index_url:
            return False
        if not isinstance(index_url, str):
            raise ParamTypeError("镜像源地址参数的数据类型应为字符串。")
        return not _execute_cmd(
            Command(self.interpreter, *_PIPCMDS["SETINDEX"], index_url),
            tips="",
            no_output=True,
            no_tips=True,
            timeout=None,
        )[1]

    def get_global_index(self):
        """
        ### 显示当前pip全局镜像源地址。

        ```
        :return: str, 当前系统pip全局镜像源地址。
        ```
        """
        if not self.pip_ready:
            return EMPTY_STR
        result, retcode = _execute_cmd(
            Command(self.interpreter, *_PIPCMDS["GETINDEX"]),
            EMPTY_STR,
            no_output=True,
            no_tips=True,
            timeout=None,
        )
        if retcode:
            return EMPTY_STR
        match_res = re.match(r"^global.index-url='(.+)'$", result)
        if not match_res:
            return EMPTY_STR
        return match_res.group(1)

    def install(self, *names, **kwargs):
        """
        ### 安装Python第三方包。

        包名names必须提供，其他参数可以省略，但除了names参数，其他需要指定的参数需以关键字参数方式指定。

        注意：包名names中只要有一个不可安装(无资源等原因)，其他包也不会被安装。

        所以如果不能保证names中所有的包都能被安装，那最好每次只传入一个包名，循环调用install方法安装所有的包。

        ```
        :param names: str, 第三方包名(可变数量参数)。

        :param strategy: 'eager' or 'needed', 依赖库的升级策略，'eager'：总是升级依赖库，'needed'：仅当依赖库不满足要求时才升级。默认「仅在需要时」。

        :param index_url: str, pip镜像源地址。

        :param upgrade: bool, 是否以升级模式安装。如果之前已安装该包，则升级模式会卸载旧版本安装新版本，反之会跳过安装，不安装新版本。

        :param pre: bool, 查找目标是否包括预发行版和开发版，默认False，即仅查找稳定版。

        :param user: bool, 是否安装到您平台的Python用户安装目录，通常是 ~/.local/或％APPDATA％Python，默认False。

        :param compile: bool or 'auto', 是否将Python源文件编译为字节码，默认'auto'，由pip决定。

        :param no_output: bool, 不在终端上显示命令输出，默认True。

        :param no_tips: bool, 不在终端上显示等待提示信息，默认True。

        :param timeout: int or float, 任务超时限制，单位为秒，可设为None表示无限制，默认None。

        :return: tuple[tuple[str...], bool], 返回((包名...), 退出状态)元组。但包名names中只要有一个包不可安装，则所有传入的包名都不会被安装，且退出状态为False。
        ```

        `所有包名中有非str类型数据则抛出ParamTypeError异常;`

        `index_url数据类型非str则抛出ParamTypeError异常;`

        `timeout参数值小于1则抛出ParamValueError异常;`

        `timeout参数数据类型不是int或float或None则抛出ParamTypeError异常；`

        以上所有异常可从fastpip.errors模块导入。
        """
        if not self.pip_ready or not names:
            return tuple()
        (
            install_pre,
            index_url,
            timeout,
            upgrade,
            no_tips,
            no_output,
            install_user,
            compile_sc,
            upgrade_strategy,
        ) = (
            kwargs.get("pre", False),
            kwargs.get("index_url", EMPTY_STR),
            kwargs.get("timeout", None),
            kwargs.get("upgrade", False),
            kwargs.get("no_tips", True),
            kwargs.get("no_output", True),
            kwargs.get("user", False),
            kwargs.get("compile", "auto"),
            kwargs.get("strategy", None),
        )
        if not all(isinstance(s, str) for s in names):
            raise ParamTypeError("包名参数的数据类型应为字符串。")
        if not isinstance(index_url, str):
            raise ParamTypeError("镜像源地址参数数据类型应为字符串。")
        self.__check_timeout_num(timeout)
        if upgrade_strategy not in (None, "eager", "needed"):
            raise ParamValueError("strategy参数可选值为'eager'、'needed'或None。")
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
        if compile_sc == "auto":
            pass
        elif compile_sc:
            cmds.append("--compile")
        else:
            cmds.append("--no-compile")
        tips = "正在安装{}".format(", ".join(names))
        return (
            names,
            not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1],
        )

    def uninstall(self, *names, **kwargs):
        """
        ### 卸载Python第三方包。

        ```
        param names: str, 不定长参数。要卸载的包名，可以传入多个包名，此参数必选。

        param no_output: bool, 不在终端上显示命令输出，默认True。

        param no_tips: bool, 不在终端上显示等待提示信息，默认True。

        param timeout: int or float, 任务超时限制，单位为秒，可设为None表示无限制，默认None。

        return: tuple[tuple[str...], bool]。返回((包名...), 退出状态)元组，状态不为True则表示卸载失败。注意：如果names中包含未安装的包则跳过卸载，退出状态仍为True。
        ```

        `所有包名中有非str类型数据则抛出ParamTypeError异常;`

        `timeout参数值小于1则抛出ParamValueError异常;`

        `timeout参数数据类型不是int或float或None则抛出ParamTypeError异常。`

        以上异常类可以从fastpip.errors模块导入。
        """
        if not self.pip_ready or not names:
            return tuple()
        timeout, no_tips, no_output = (
            kwargs.get("timeout", None),
            kwargs.get("no_tips", True),
            kwargs.get("no_output", True),
        )
        if not all(isinstance(s, str) for s in names):
            raise ParamTypeError("包名参数的数据类型应为字符串。")
        self.__check_timeout_num(timeout)
        tips = "正在卸载{}".format(", ".join(names))
        cmds = Command(self.interpreter, *_PIPCMDS["UNINSTALL"], *names)
        return (
            names,
            not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1],
        )

    def download(self, *names, **kwargs):
        """
        ### 下载指定的包。

        提示：当使用python_version、platform、abis或implementation参数约束平台和解释器时，必须设置no_deps参数值为True，不能设置only_binary参数，不能设置no_binary参数。

        ```
        :param names: str, 不定长参数。包名，可同时传入多个包名，此参数必选。

        :param no_deps: bool, 关键字参数。不下载依赖项，默认False。

        :param no_binary: tuple|list[str...], 关键字参数。不使用二进制包，即只下载源代码包。参数值应为包含出现在names中的包名的列表或元组，默认None。注意，某些软件包很难编译，下载的源代码包可能无法用来安装。

        :param only_binary: tuple|list[str...], 关键字参数。不使用源代码包，即只下载二进制包。参数值应为包含出现在names中的包名的列表或元组，默认None。注意，如果该参数值列表中的包没有二进制分发版，则设置此参数后将无法下载。

        :param prefer_binary: bool, 关键字参数。与较新的源代码包相比，宁愿下载较旧版本的二进制包。默认False。

        :param pre: bool, 关键字参数。包括预发行版本和开发版本，默认False。

        :param ignore_require_python: bool , 关键字参数。忽略包的Requires-Python信息，默认False。

        :param dest: str, 关键字参数，下载文件的保存目录路径。如果不指定此参数、参数值为None或值为磁盘根目录，则默认下载至'/用户目录/Downloads/pip_downloads-xxx'文件夹；如果dest的值不是完整路径，则下载至'用户目录/Downloads/'+ dest文件夹；如果dest为完整路径：如果dest是文件路径，则下载至该文件所在的文件夹，否则下载至该文件夹。如果路径不存在，将会尝试创建文件夹，创建失败则抛出PermissionError异常。

        :param platform: tuple|list[str...], 关键字参数，仅下载与platform中列出的平台兼容的包，默认None，即仅下载与当前系统兼容的安装包。

        :param python_version: str, 关键字参数，用于wheel和'Requires-Python'兼容性检查的Python解释器版本。默认为从当前环境的解释器派生的版本。最多可以使用三个以点号分隔的整数来指定版本(例如，'3'代表3.0.0，'3.7'代表3.7.0或3.7.3)。主次版本也可以不带点的字符串形式给出(例如，'37'代表3.7.0)。

        :param implementation: str, 关键字参数。仅下载与指定Python实现兼容的二进制包，例如'pp'，'jy'，'cp'或'ip'。如果未指定，则使用当前环境的解释器实现。使用'py'强制指定与实现无关的二进制包。默认None。

        :param abis: tuple|list[str...], 关键字参数。仅下载与指定Python ABI兼容的包，例如 'pypy_41'。如果未指定，则使用当前环境的解释器abi标签。通常，使用此参数时，需要同时指定platform、python_version、implementation 3个参数的值。

        :param index_url: str, 关键字参数，镜像源地址，默认None。

        :param no_output: bool, 关键字参数，不在终端上显示命令输出，默认True。

        :param no_tips: bool, 关键字参数，不在终端上显示等待提示信息，默认True。

        :param timeout: int or float, 关键字参数，任务超时时长限制，单位为秒，可设为None表示无限制，默认None。

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
            no_tips,
            no_output,
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
            kwargs.get("no_tips", True),
            kwargs.get("no_output", True),
            kwargs.get("timeout", None),
        )
        NoneType = type(None)
        if not all(isinstance(s, str) for s in names):
            raise ParamTypeError("包名参数类型应为字符串。")
        clean_package_name = parse_package_names(names)
        if not isinstance(no_binary, (tuple, list, NoneType)):
            raise ParamTypeError("no_binary参数值的数据类型应为'tuple'、'list'或值为'None'。")
        if not (
            isinstance(no_binary, NoneType)
            or all(n in clean_package_name for n in no_binary)
        ):
            raise ParamValueError("no_binary参数值不应包含不在names中的包名(不包含版本限制符号)。")
        if not isinstance(only_binary, (tuple, list, NoneType)):
            raise ParamTypeError("only_binary参数值的数据类型应为'tuple'、'list'或值为'None'。")
        if not (
            isinstance(only_binary, NoneType)
            or all(n in clean_package_name for n in only_binary)
        ):
            raise ParamValueError("only_binary参数值不应包含不在names中的包名(不包含版本限制符号)。")
        if not isinstance(dest, (str, NoneType)):
            raise ParamTypeError("dest参数值的数据类型应为'str'或值应为'None'。")
        if not isinstance(platform, (tuple, list, NoneType)):
            raise ParamTypeError("参数platform值类型应为'tuple'、'list'或值为'None'。")
        if not (
            isinstance(platform, NoneType) or all(isinstance(s, str) for s in platform)
        ):
            raise ParamTypeError("参数platform值应为一个包含字符串的元组或列表。")
        if not isinstance(python_version, (str, NoneType)):
            raise ParamTypeError("参数python_version值类型应为'str'或值为'None'。")
        if not isinstance(implementation, (str, NoneType)):
            raise ParamTypeError("参数implementation值类型应为'str'或值为'None'。")
        if not isinstance(abis, (tuple, list, NoneType)):
            raise ParamTypeError("参数abi值类型应为'tuple'、'list'或值为'None'。")
        if not (isinstance(abis, NoneType) or all(isinstance(s, str) for s in abis)):
            raise ParamTypeError("参数abi值应为一个包含字符串的元组或列表。")
        if not isinstance(index_url, (str, NoneType)):
            raise ParamTypeError("参数index_url值类型应为'str'或值为'None'。")
        self.__check_timeout_num(timeout)
        tips = "正在下载{}".format(", ".join(names))
        download_dir_hash = os.path.join(
            self.USER_DOWNLOADS, "pip_downloads-{}".format(abs(hash(tips)))
        )
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
        retcode = not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1]
        return (retcode, dest) if retcode else (retcode, EMPTY_STR)

    def names_for_import(self):
        """
        ### 获取本Python环境下的包/模块可用于import语句的名称列表。

        此方法返回的名称列表中可能有重复项，且不保证列表中所有的名称用于import语句时都可以成功导入。

        ```
        return: set[str...]，可用于import语句的名称集合。
        ```
        """
        pkg_import_names = set()
        if not self.env_path:
            return pkg_import_names
        sys_paths, builtins = self.__read_syspath_builtins()
        for sys_path in sys_paths:
            for names in self.__pkgs_importables_from(sys_path).values():
                pkg_import_names.update(names)
        pkg_import_names.update(builtins)
        return pkg_import_names

    def imports(self):
        """
        ### 获取本Python环境下的包/模块可用于import语句的名称列表。

        此方法返回的名称列表中可能有重复项，且不保证列表中所有的名称用于import语句时都可以成功导入。

        ```
        return: list[str...]，可用于import语句的名称列表。
        ```
        """
        # XXX 弃用方法
        from warnings import warn

        warn("此方法名即将弃用，请使用'names_for_import'代替。", stacklevel=2)
        return self.names_for_import()

    def query(self, module_or_pkg_name: str, *, case=True):
        """
        ### 通过包名/模块的发布名称查询该包/模块用于import语句的名称。

        例如，pywin32是一个Windows API库的发布名称，使用时是import win32api、import win32con等，

        此方法可以输入pywin32作为module_or_pkg_name参数，查询得到['win32api', 'win32con'...]这样的结果。

        此方法不保证返回的名称列表中所有的名称用于import语句时都可以成功导入。

        ```
        :param module_or_pkg_name: str, 想要查询的包名、模块名。

        :param case: bool, 是否对module_or_pkg_name大小写敏感。

        :return: list[str...], 该包、模块的用于import语句的名称列表。
        ```

        包名非str则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        """
        # XXX 弃用方法
        from warnings import warn

        warn("此方法名即将弃用，请使用'query_for_import'代替。", stacklevel=2)
        return self.query_for_import(module_or_pkg_name, case)

    def query_for_import(self, module_or_pkg_name: str, *, case=True, fresh=False):
        """
        ### 通过包名/模块的发布名称查询该包/模块用于import语句的名称。

        例如，pywin32是一个Windows API库的发布名称，使用时是import win32api、import win32con等，

        此方法可以输入pywin32作为module_or_pkg_name参数，查询得到['win32api', 'win32con'...]这样的结果。

        此方法不保证返回的名称列表中所有的名称用于import语句时都可以成功导入。

        ```
        :param module_or_pkg_name: str, 想要查询的包名、模块名。

        :param case: bool, 是否对module_or_pkg_name大小写敏感。

        :param fresh: bool, 是否刷新缓存再查询。当你需要循环调用query_for_import方法查询大量module_or_pkg_name时，将此参数置为False可以使用缓存以加快查询。

        :return: list[str...], 该包、模块的用于import语句的名称列表。
        ```

        包名非str则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        """
        if not isinstance(module_or_pkg_name, str):
            raise ParamTypeError("参数name数据类型错误，数据类型应为str。")
        if fresh:
            self.__cache_pkgs_importables.clear()
        else:
            if (
                time.time() - self.__time_last_activity
                > PyEnv.cache_refresh_maximum_interval
            ):
                self.__cache_pkgs_importables.clear()
        self.__time_last_activity = time.time()
        if not self.__cache_pkgs_importables:
            self.get_map_packages_importables()
        for publish_name, value in self.__cache_pkgs_importables.items():
            if case:
                cased_value = publish_name
            else:
                cased_value = publish_name.lower()
                module_or_pkg_name = module_or_pkg_name.lower()
            if module_or_pkg_name == cased_value:
                return list(value)
        return list()

    def __read_syspath_builtins(self):
        """读取目标Python环境的sys.path和sys.builtin_module_names属性。"""
        self.cleanup_old_scripts()
        if not self.env_path:
            return []
        source_code = """import sys
print(sys.path[1:], "\\n", sys.builtin_module_names)"""
        _path = os.path.join(self.FILE_DIR, f"ReadSYSPB.{VERSION}")
        if not os.path.isfile(_path):
            if not os.path.exists(self.FILE_DIR):
                try:
                    os.makedirs(self.FILE_DIR)
                except Exception:
                    return [], ()
            try:
                with open(_path, "wt", encoding="utf-8") as py_file:
                    py_file.write(source_code)
            except Exception:
                return [], ()
        result, retcode = _execute_cmd(
            Command(self.interpreter, _path), EMPTY_STR, True, True, None
        )
        if retcode or not result:
            return [], ()
        try:
            paths, builtins = result.strip().split("\n")
            return eval(paths.strip()), eval(builtins.strip())
        except Exception:
            return [], ()

    @staticmethod
    def __pkgs_importables_from(pkgs_host):
        """
        从(sys.path)中的一个路径(pkgs_host)生成模块/包发布名-import名映射表。

        :return: dict[str: set[str...]...], 即：{模块发布名: {import名, ...}, ...}
        """
        toplevel_pattern = re.compile(r"^[A-Za-z_]?[A-Za-z0-9_]+")
        metadata_name_pattern = re.compile(r"^Name: ([A-Za-z0-9_\-]+)$")
        module_pattern = re.compile(r"^([A-Za-z0-9_]+).*(?<!_d)\.py[cdw]?$", re.I)
        publish_importable_names = dict()
        try:
            modules_packages_path = os.listdir(pkgs_host)
        except Exception:
            return publish_importable_names
        dist_dirs = list()
        nodist_dirs = list()
        mod_files = list()
        for pkg_path in modules_packages_path:
            fullpath = os.path.join(pkgs_host, pkg_path)
            if os.path.isdir(fullpath):
                if pkg_path.endswith(".dist-info") or pkg_path.endswith(".egg-info"):
                    dist_dirs.append(pkg_path)
                else:
                    nodist_dirs.append(pkg_path)
            elif os.path.isfile(fullpath):
                mod_files.append(pkg_path)
        for dist_dir in dist_dirs:
            dir_fullpath = os.path.join(pkgs_host, dist_dir)
            toplevel_txt = os.path.join(dir_fullpath, "top_level.txt")
            metadata = os.path.join(dir_fullpath, "METADATA")
            if not os.path.exists(metadata):
                continue
            try:
                with open(metadata, "rt", encoding="utf-8") as md:
                    metadata_lines = md.readlines()
            except Exception:
                continue
            for line in metadata_lines[1:]:
                name_metadata_matched = metadata_name_pattern.match(line)
                if name_metadata_matched:
                    break
            if not name_metadata_matched:
                continue
            pkg_published_name = name_metadata_matched.group(1)
            if not os.path.exists(toplevel_txt):
                if pkg_published_name not in publish_importable_names:
                    publish_importable_names[pkg_published_name] = set()
                continue
            pkg_importables = set()
            try:
                with open(toplevel_txt, "rt", encoding="utf-8") as tt:
                    toplevel_txt_lines = tt.readlines()
                for line in toplevel_txt_lines:
                    toplevel_importable_matched = toplevel_pattern.match(
                        os.path.basename(line).strip()
                    )
                    if not toplevel_importable_matched:
                        continue
                    pkg_importables.add(toplevel_importable_matched.group())
            except Exception:
                pass
            if pkg_published_name not in publish_importable_names:
                publish_importable_names[pkg_published_name] = pkg_importables
            else:
                publish_importable_names[pkg_published_name].update(pkg_importables)
        for nodist_dir in nodist_dirs:
            if os.path.isfile(os.path.join(pkgs_host, nodist_dir, "__init__.py")):
                if nodist_dir not in publish_importable_names:
                    publish_importable_names[nodist_dir] = {nodist_dir}
                else:
                    publish_importable_names[nodist_dir].add(nodist_dir)
        for mod_file in mod_files:
            mod_file_matched = module_pattern.match(mod_file)
            if not mod_file_matched:
                continue
            module_importable = mod_file_matched.group(1)
            if module_importable not in publish_importable_names:
                publish_importable_names[module_importable] = {module_importable}
            else:
                publish_importable_names[module_importable].add(module_importable)
        return publish_importable_names

    @staticmethod
    def __names_from_syspath(packages_dir):
        """
        从sys.path列表中的一个路径获取可用于导入的模块/包名。

        返回值：dict[模块发布名: [导入名...]...]
        """
        modules_and_pkgs_path, names_used_for_import = list(), dict()
        try:
            modules_and_pkgs_path.extend(os.listdir(packages_dir))
        except Exception:
            return names_used_for_import
        py_modules, py_packages = list(), list()
        pattern_module = re.compile(r"^([0-9a-zA-Z_]+).*(?<!_d)\.py[cdw]?$")
        pattern_package = re.compile(r"^([0-9a-zA-Z_.]+)-.+(?:\.dist-info|\.egg-info)$")
        pattern_toplevel = re.compile(r"^[a-zA-Z_]?[0-9a-zA-Z_]+")
        for mod_pkg in modules_and_pkgs_path:
            _path = os.path.join(packages_dir, mod_pkg)
            if os.path.isfile(_path):
                py_modules.append(mod_pkg)
            elif os.path.isdir(_path):
                py_packages.append(mod_pkg)
        for package in py_packages:
            try:
                file_list = os.listdir(os.path.join(packages_dir, package))
            except Exception:
                continue
            if "__init__.py" in file_list:
                if package not in names_used_for_import:
                    # 有__init__.py文件的目录，其导入名即为目录名
                    names_used_for_import[package] = [package]
                continue
            matched_obj_package = pattern_package.match(package)
            if not matched_obj_package:
                continue
            top_level = os.path.join(packages_dir, package, "top_level.txt")
            if not os.path.isfile(top_level):
                continue
            try:
                with open(top_level, "rt") as top_level:
                    lines = top_level.readlines()
            except Exception:
                continue
            names_for_importing_toplevel = list()
            for l in lines:
                matched_obj_toplevel = pattern_toplevel.match(
                    os.path.basename(l.strip())
                )
                if not matched_obj_toplevel:
                    continue
                names_for_importing_toplevel.append(matched_obj_toplevel.group())
            pkg_name = matched_obj_package.group(1)
            if pkg_name not in names_used_for_import:
                names_used_for_import[pkg_name] = names_for_importing_toplevel
            else:
                names_used_for_import[pkg_name].extend(names_for_importing_toplevel)
        for module in py_modules:
            matched_obj_module = pattern_module.match(module)
            if not matched_obj_module:
                continue
            for_importing = matched_obj_module.group(1)
            # 单文件模块形式下，导入名和剔除后缀后的模块名相同(后缀不仅指扩展名)
            if for_importing in names_used_for_import:
                continue
            names_used_for_import[for_importing] = [for_importing]
        return names_used_for_import

    def ensurepip(self, no_output=True, no_tips=True):
        """
        ### 此方法用于当环境中没有pip模块时使用副本恢复pip。

        是否能恢复成功取决于该环境是否保存了pip副本。

        请注意，恢复的pip并不一定是最新版，如果想更新'pip'，请接着调用'upgrade_pip'方法。
        """
        if not self.env_path:
            return False
        tips = "正在确认或恢复pip模块"
        scripts_dir_path = self.scripts_path()
        pipexe_path = os.path.join(scripts_dir_path, PIP_EXE)
        pip3exe_path = os.path.join(scripts_dir_path, "pip3.exe")
        cmds = Command(self.interpreter, *_PIPCMDS["ENSUREPIP"])
        bool_res = not _execute_cmd(cmds, tips, no_output, no_tips, None)[1]
        if (
            bool_res
            and os.path.isfile(pip3exe_path)
            and (not os.path.isfile(pipexe_path))
        ):
            try:
                shutil.copy(pip3exe_path, pipexe_path)
            except Exception:
                pass
        return bool_res

    def scripts_path(self):
        """
        ### 返回Python环境的Scripts目录的路径。

        如果Python环境无效，则返回空字符串。
        #"""
        if not self.env_path:
            return EMPTY_STR
        return os.path.join(self.env_path, PYTHON_SCR)

    def get_map_packages_importables(self):
        """
        ### 获取本环境下包/模块的发布名与导入名的映射表并在PyEnv实例内缓存。

        ```
        :return: dict[str: set[str...]...]
        ```
        """
        self.__cache_pkgs_importables.clear()
        sys_paths, builtins = self.__read_syspath_builtins()
        for name in builtins:
            self.__cache_pkgs_importables[name] = {name}
        for sys_path in sys_paths:
            pkgs_importables_map = self.__pkgs_importables_from(sys_path)
            for name, importables in pkgs_importables_map.items():
                if name not in self.__cache_pkgs_importables:
                    self.__cache_pkgs_importables[name] = importables
                else:
                    self.__cache_pkgs_importables[name].update(importables)
        return self.__cache_pkgs_importables

    def query_for_install(self, import_name, *, case=True, fresh=False):
        """
        ### 通过import语句所使用的模块名称反向查询该名称对应的包/模块的发布名称。

        因为不是所有的包/模块的安装名称和用于导入的名称都是一样的，比如pywin32，使用时就是import win32api等。

        此方法功能就像输入'win32api'或'win32con'作为import_name参数，反查得到'pywin32'。

        此方法不保证查询的结果一定正确。

        ```
        :param import_name: str, import语句所使用的模块名称。

        :param case: bool, 是否对import_name大小写敏感。

        :param fresh: bool, 是否刷新缓存后查询。当你需要循环调用query_for_install方法查询大量import_name时，将此参数置为False可以使用缓存以加快查询。

        :return: str, 包的名称，该名称一般用于安装，比如用于pip命令安装等。
        ```
        """
        if not isinstance(import_name, str):
            raise ParamTypeError("参数import_name类型错误，类型应为str。")
        if fresh:
            self.__cache_pkgs_importables.clear()
        else:
            if (
                time.time() - self.__time_last_activity
                > PyEnv.cache_refresh_maximum_interval
            ):
                self.__cache_pkgs_importables.clear()
        self.__time_last_activity = time.time()
        if not self.__cache_pkgs_importables:
            self.get_map_packages_importables()
        for publish_name, value in self.__cache_pkgs_importables.items():
            if case:
                cased_value = value
            else:
                import_name = import_name.lower()
                cased_value = {i.lower() for i in value}
            if import_name in cased_value:
                return publish_name
        return EMPTY_STR
