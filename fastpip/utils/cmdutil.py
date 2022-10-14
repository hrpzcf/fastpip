# coding: utf-8

import os

from ..com.common import *


class Command(list):
    """
    ### 继承自 list 的命令类，主要是为了提供与 Anaconda3 路径相关的环境变量。
    """

    def __init__(self, *args, **kwargs):
        """
        ### Command 类的初始化方法

        Command 以不定长参数方式初始化，要求第一个参数是一个可执行文件的绝对路径

        例子：假如程序 python.exe 在 C:\abc 目录内，命令行参数是 python -m pip install x

        那么应该这样初始化一个 Command 类实例：cmd = Command("C:\\abc\\python.exe", "-m", "pip", "install", "x")
        """
        super(Command, self).__init__()
        self.initialize(args)
        self[0] = os.path.normpath(self[0])

    def initialize(self, args):
        if not args:
            raise ValueError("参数数量不能少于一个。")
        if not all(isinstance(s, str) for s in args):
            raise TypeError("参数数据类型应为字符串。")
        if not os.path.isabs(args[0]):
            raise ValueError("第一个参数不是一个绝对路径。")
        if not os.path.isfile(args[0]):
            raise ValueError("第一个参数不是文件路径。")
        if not os.access(args[0], os.X_OK):
            raise ValueError("第一个参数文件不可执行。")
        self.extend(args)

    @property
    def executable(self):
        return self[0]

    @property
    def commands(self):
        return self.copy()

    def isconda(self):
        dir_path = os.path.dirname(self.executable)
        while True:
            conda = os.path.join(dir_path, P_CONDA_EXE)
            if os.path.isfile(conda):
                return True
            uplevel = os.path.dirname(dir_path)
            if os.path.samefile(uplevel, dir_path):
                break
            dir_path = uplevel
        return False

    def issubconda(self):
        if not self.isconda():
            return False
        _path = os.path.dirname(self.executable)
        temp = os.path.join(_path, PYTHON_EXE)
        if not (os.path.isfile(temp) and os.access(temp, os.X_OK)):
            return False
        if os.path.basename(os.path.dirname(_path)) == CONDA_ENVS:
            return True
        return False

    def condamain(self):
        _path = os.path.dirname(self.executable)
        if os.path.isfile(os.path.join(_path, P_CONDA_EXE)):
            return _path
        if self.issubconda():
            return os.path.dirname(os.path.dirname(_path))
        return EMPTY_STR

    def environment(self):
        if self.isconda():
            _path = os.path.dirname(self.executable)
            if self.issubconda():
                name, shlvl = os.path.basename(_path), 2
            else:
                name, shlvl = "base", 1
            conda_main_path = self.condamain()
            preset_env_var = {
                "CONDA_DEFAULT_ENV": r"{}".format(name),
                "CONDA_EXE": os.path.join(
                    conda_main_path,
                    "Scripts",
                    M_CONDA_EXE,
                ),
                "CONDA_PREFIX": _path if self.issubconda() else conda_main_path,
                "CONDA_PREFIX_1": conda_main_path,
                "CONDA_PROMPT_MODIFIER": r"({}) ".format(name),
                "CONDA_PYTHON_EXE": os.path.join(conda_main_path, PYTHON_EXE),
                "CONDA_SHLVL": r"{}".format(shlvl),
            }
            if shlvl == 1:
                del preset_env_var["CONDA_PREFIX_1"]
            preset_env_var.update(os.environ)
            conda_PATH = os.pathsep.join(
                (
                    _path,
                    os.path.join(_path, "Library", "mingw-w64", "bin"),
                    os.path.join(_path, "Library", "usr", "bin"),
                    os.path.join(_path, "Library", "bin"),
                    os.path.join(_path, "Scripts"),
                    os.path.join(_path, "bin"),
                    os.path.join(conda_main_path, "condabin"),
                )
            )
            preset_env_var["PATH"] = os.pathsep.join(
                (conda_PATH, preset_env_var.get("PATH", ""))
            )
            return preset_env_var
        return os.environ

    def __repr__(self):
        return "Command(exec: {}, opts: {})".format(self[0], " ".join(self[1:]))
