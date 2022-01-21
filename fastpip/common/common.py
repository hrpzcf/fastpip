# coding: utf-8

__all__ = [
    "VENV_CFG",
    "PYTHON_SCR",
    "PYTHON_EXE",
    "PIP_INIT",
    "EMPTY_STR",
    "UNKNOWN_LOCATION",
    "PYENV_SEP_STR",
    "CONDA_ENVS",
    "P_CONDA_EXE",
    "M_CONDA_EXE",
]


VENV_CFG = "pyvenv.cfg"  # venv创建的虚拟环境的配置文件
PYTHON_SCR = "Scripts"  # WIN平台上Python的Scripts目录
PYTHON_EXE = "python.exe"  # WIN平台上Python的解释器名称
PIP_INIT = "Lib/site-packages/pip/__init__.py"  # WIN平台上pip目录及init文件名
EMPTY_STR = ""  # 空字符串
UNKNOWN_LOCATION = "unknown location"  # Python环境位置未知时的显示名
PYENV_SEP_STR = "@"  # PyEnv类实例的字符串形式中Python版本号与位置之间的分隔符
CONDA_ENVS = "envs"  # Anaconda的虚拟环境目录名
P_CONDA_EXE = "_conda.exe"  # conda的可执行文件名
M_CONDA_EXE = "conda.exe"  # conda的可执行文件名
