# coding: utf-8

from enum import Enum

__all__ = [
    "CmdRead",
    "CONDA_ENVS",
    "DEFAULT_REQNAME",
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

LIB_DIR_NAME = "Lib"  # site-packages 所在目录名称（Windows 系统）
SITEPKG_NAME = "site-packages"  # 安装第三包目的文件夹名称
DEFAULT_REQNAME = "requirements.txt"  # 导出环境已安装的包信息时的默认文件名
PKG_SEPDOT = "."  # 导入语句所使用的导入路径分隔符
VENV_CFG = "pyvenv.cfg"  # venv 创建的虚拟环境的配置文件
PYTHON_SCR = "Scripts"  # WIN 平台上 Python 的 Scripts 目录
PYTHON_EXE = "python.exe"  # WIN 平台上 Python 的解释器名称
PIP_INIT = "Lib/site-packages/pip/__init__.py"  # win 上 pip 目录及 init 文件名
PIP_EXE = "pip.exe"  # pip 模块的可执行文件名称
EMPTY_STR = ""  # 空字符串
UNKNOWN_LOCATION = "unknown location"  # Python 环境位置未知时的显示名
PYENV_SEP_STR = "@"  # PyEnv 类实例的字符串形式中 Python 版本号与位置之间的分隔符
CONDA_ENVS = "envs"  # Anaconda 的虚拟环境目录名
P_CONDA_EXE = "_conda.exe"  # conda 的可执行文件名
M_CONDA_EXE = "conda.exe"  # conda 的可执行文件名


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
