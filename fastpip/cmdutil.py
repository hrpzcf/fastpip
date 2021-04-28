# coding: utf-8

import os

from .errors import *


class Command(list):
    """经包装的命令类，主要是为了提供与Anaconda3路径相关的环境变量。"""

    def __init__(self, *args, **kwargs):
        """第一个参数要求是一个可执行文件的绝对路径。"""
        if not args:
            raise ValueError("参数数量不能少于一个。")
        super().__init__()
        self.extend(self.initialize(args))
        self.__executable = os.path.normpath(self[0])

    @staticmethod
    def initialize(args):
        if not all(isinstance(s, str) for s in args):
            raise ParamTypeError("参数数据类型应为字符串。")
        if not os.path.isabs(args[0]):
            raise PathParamError("第一个参数不是一个绝对路径。")
        if not os.path.isfile(args[0]):
            raise PathParamError("第一个参数不是文件路径。")
        return args

    @property
    def executable(self):
        return self.__executable

    @property
    def commands(self):
        return self.copy()

    def __repr__(self):
        return "execute: {}\noptions: {}".format(self.__executable, " ".join(self[1:]))

    def isconda(self):
        dir_path = os.path.dirname(self.executable)
        while True:
            conda = os.path.join(dir_path, "_conda.exe")
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
        temp = os.path.join(_path, "python.exe")
        if not (os.path.isfile(temp) and os.access(temp, os.X_OK)):
            return False
        if os.path.basename(os.path.dirname(_path)) == "envs":
            return True
        return False

    def condamain(self):
        _path = os.path.dirname(self.executable)
        if os.path.isfile(os.path.join(_path, "_conda.exe")):
            return _path
        if self.issubconda():
            return os.path.dirname(os.path.dirname(_path))
        return ""

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
                    "conda.exe",
                ),
                "CONDA_PREFIX": _path if self.issubconda() else conda_main_path,
                "CONDA_PREFIX_1": conda_main_path,
                "CONDA_PROMPT_MODIFIER": r"({}) ".format(name),
                "CONDA_PYTHON_EXE": os.path.join(conda_main_path, "python.exe"),
                "CONDA_SHLVL": r"{}".format(shlvl),
            }
            if shlvl == 1:
                del preset_env_var["CONDA_PREFIX_1"]
            preset_env_var.update(os.environ)
            conda_PATH = "{};{};{};{};{};{};{};".format(
                _path,
                os.path.join(_path, "Library", "mingw-w64", "bin"),
                os.path.join(_path, "Library", "usr", "bin"),
                os.path.join(_path, "Library", "bin"),
                os.path.join(_path, "Scripts"),
                os.path.join(_path, "bin"),
                os.path.join(conda_main_path, "condabin"),
            )
            preset_env_var["PATH"] = conda_PATH + preset_env_var.get("PATH", "")
            return preset_env_var
        return os.environ
