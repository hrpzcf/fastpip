# coding: utf-8

__all__ = [
    "VENV_CFG",
    "PYTHON_SCR",
    "PYTHON_EXE",
    "PIP_INIT",
    "PIP_EXE",
    "EMPTY_STR",
    "UNKNOWN_LOCATION",
    "PYENV_SEP_STR",
    "CONDA_ENVS",
    "P_CONDA_EXE",
    "M_CONDA_EXE",
]


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
