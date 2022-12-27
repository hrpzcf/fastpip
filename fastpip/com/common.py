# coding: utf-8

from enum import Enum
from locale import getpreferredencoding
from os import path
from sys import getdefaultencoding

from chardet import detect

__all__ = [
    "CmdRead",
    "CONDA_ENVS",
    "DEFAULT_REQNAME",
    "decode_bytes",
    "EMPTY_STR",
    "LIB_DIR_NAME",
    "M_CONDA_EXE",
    "PKG_SEPDOT",
    "PYTHON_SCR",
    "PYTHON_EXE",
    "PIP_INIT",
    "PIP_EXE",
    "PYENV_SEP_STR",
    "P_CONDA_EXE",
    "SITEPKG_NAME",
    "UNKNOWN_LOCATION",
    "VENV_CFG",
]

__pdc = getdefaultencoding()
__lpc = getpreferredencoding(False)

LIB_DIR_NAME: str = "Lib"  # site-packages 所在目录名称（Windows 系统）
SITEPKG_NAME: str = "site-packages"  # 第三方包的安装位置文件夹名称
DEFAULT_REQNAME: str = "requirements.txt"  # 导出环境已安装的包信息时的默认文件名
PKG_SEPDOT: str = "."  # 导入语句所使用的导入路径分隔符
VENV_CFG: str = "pyvenv.cfg"  # venv 创建的虚拟环境的配置文件
PYTHON_SCR: str = "Scripts"  # WIN 平台上 Python 的 Scripts 目录
PYTHON_EXE: str = "python.exe"  # WIN 平台上 Python 的解释器名称
PIP_INIT: str = path.join("pip", "__init__.py")  # pip 目录及 init 文件名
PIP_EXE: str = "pip.exe"  # pip 模块的可执行文件名称
EMPTY_STR: str = ""  # 空字符串
UNKNOWN_LOCATION: str = "unknown location"  # Python 环境位置未知时的显示名
PYENV_SEP_STR: str = "@"  # PyEnv 类实例的字符串形式中 Python 版本号与位置之间的分隔符
CONDA_ENVS: str = "envs"  # Anaconda 的虚拟环境目录名
M_CONDA_EXE: str = "conda.exe"  # conda 的可执行文件名
P_CONDA_EXE: str = "_conda.exe"  # conda 的可执行文件名


def decode_bytes(__bytes: bytes):
    if not __bytes:
        return EMPTY_STR
    try:
        return __bytes.decode(__pdc)
    except UnicodeDecodeError as exc:
        string = f"fastpip:\n\t{exc.reason}\n"
    try:
        return __bytes.decode(__lpc)
    except UnicodeDecodeError as exc:
        string = f"{string}\t{exc.reason}\n"
    encoding = detect(__bytes)
    if encoding is None:
        return string
    try:
        return __bytes.decode(encoding)
    except UnicodeDecodeError as exc:
        string = f"{string}\t{exc.reason}\n"
    return string


class CmdRead(Enum):
    # 读取目标 Python 解释器的版本信息
    PYVERS = (
        "-c",
        "import sys;print(sys.version)",
    )
    # 读取 sys.path 和 builtin_module_names 信息
    SYSINFO = (
        "-c",
        "import sys;print(sys.path[1:]);print(sys.builtin_module_names)",
    )
    # 读取目标 Python 环境的 site-packaes 路径
    SITES = (
        "-c",
        "import site;print(site.getsitepackages())",
    )
    # 读取目标 Python 环境的用户 site-packaes 路径
    USERSITE = (
        "-c",
        "import site;print(site.getusersitepackages())",
    )
