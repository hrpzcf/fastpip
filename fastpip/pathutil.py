# coding: utf-8

import os

from .errors import *


class PathCombO:
    """被包装的路径类，主要是为了提供与Anaconda3路径相关的环境变量。"""

    def __init__(self, _path):
        """_path不要求是否是目录或文件路径，但最后会取其目录路径。"""
        if not isinstance(_path, str):
            raise ParamTypeError("类型错误，路径参数类型应为字符串。")
        if not os.path.exists(_path):
            raise PathParamError("参数_path值不是有效的文件或目录路径。")
        if not os.path.isdir(_path):
            _path = os.path.dirname(_path)
        self.__path = os.path.normpath(_path)

    @property
    def path(self):
        return self.__path

    @property
    def is_anaconda(self):
        _path = self.path
        while True:
            if os.path.isfile(os.path.join(_path, "_conda.exe")):
                return True
            temp_path = os.path.dirname(_path)
            if os.path.samefile(temp_path, _path):
                break
            _path = temp_path
        return False

    def __repr__(self):
        return self.__path

    @staticmethod
    def is_conda_venv(_path):
        if not os.path.isfile(os.path.join(_path, "python.exe")):
            return False
        if os.path.basename(os.path.dirname(_path)) == "envs":
            return True
        return False

    @staticmethod
    def anaconda_main(_path):
        if os.path.isfile(os.path.join(_path, "_conda.exe")):
            return _path
        if PathCombO.is_conda_venv(_path):
            return os.path.dirname(os.path.dirname(_path))
        return ""

    def environment_variable(self):
        if self.is_anaconda:
            _path = self.path
            if PathCombO.is_conda_venv(_path):
                name, shlvl = os.path.basename(_path), 2
            else:
                name, shlvl = "base", 1
            anaconda_main_path = self.anaconda_main(_path)
            preset_env_var = {
                "CONDA_DEFAULT_ENV": r"{}".format(name),
                "CONDA_EXE": os.path.join(
                    anaconda_main_path,
                    "Scripts",
                    "conda.exe",
                ),
                "CONDA_PREFIX": _path
                if PathCombO.is_conda_venv(_path)
                else anaconda_main_path,
                "CONDA_PREFIX_1": anaconda_main_path,
                "CONDA_PROMPT_MODIFIER": r"({}) ".format(name),
                "CONDA_PYTHON_EXE": os.path.join(anaconda_main_path, "python.exe"),
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
                os.path.join(anaconda_main_path, "condabin"),
            )
            preset_env_var["PATH"] = conda_PATH + preset_env_var.get("PATH", "")
            return preset_env_var
        return os.environ
