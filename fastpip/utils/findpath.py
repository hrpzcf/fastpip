# coding: utf-8

import os
from sys import winver

from psutil import disk_partitions

from ..common.common import *


class GetFd:
    """__list_fd 函数的 opt 参数所使用的枚举"""

    Dirs = 0
    Files = 1
    Both = 2


class Level:
    """
    __common_location 函数之：

    局部参数 common_location_classification 的键

    函数返回值 common_location_classification 的键
    """

    level_1 = "level_1"
    level_2 = "level_2"


def __common_location():
    """生成各磁盘上的常见的Python安装目录路径列表。"""
    com_location_classification = {
        # 只需获取其直接子目录的目录
        Level.level_1: list(),
        # 需要获取其两层深度子目录的目录
        Level.level_2: list(),
    }
    # 查询当前Python版本（对于打包后的程序，获取此值似乎意义不大？）
    cur_pyver = "Python" + winver.replace(".", "")
    # 常用目录添加envs目录名称
    lst_common_dir = [
        "Program Files",  # Python "All Users"
        "Program Files (x86)",  # Python "All Users"
        "ProgramData",  # Anaconda3 "All Users"
        cur_pyver,
        os.path.join(cur_pyver, "envs"),
    ]
    # Anaconda3 "Just Me"
    com_location_classification[Level.level_1].append(os.path.expanduser("~"))
    disk_parts = [dp.device for dp in disk_partitions()]
    com_location_classification[Level.level_1].extend(disk_parts)
    for dp in disk_parts:
        for cd in lst_common_dir:
            full_path = os.path.join(dp, cd)
            if not os.path.isdir(full_path):
                continue
            com_location_classification[Level.level_1].append(full_path)
    # Python "Just Me"
    user_programs_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Programs")
    if os.path.exists(user_programs_dir):
        com_location_classification[Level.level_2].append(user_programs_dir)
    return com_location_classification


def __fsize(*_fpath):
    """验证文件路径中的文件是否有大小"""
    try:
        return os.path.getsize(os.path.join(*_fpath))
    except Exception:
        return False


def __paths_in_PATH():
    """
    ### 查找系统环境变量PATH中的Python目录路径列表。
    仅根据"目录中是否存在python.exe文件"进行简单查找。
    """
    python_paths_in_PATH = list()
    PATH_paths = os.getenv("PATH", "").split(";")
    for PATH_path in PATH_paths:
        try:
            PATH_path_files = os.listdir(PATH_path)
        except Exception:
            continue
        PATH_path = os.path.normpath(PATH_path)
        if (
            PYTHON_EXE in PATH_path_files
            and __fsize(PATH_path, PYTHON_EXE)
            and PATH_path not in python_paths_in_PATH
        ):
            python_paths_in_PATH.append(PATH_path)
    return python_paths_in_PATH


def cur_py_path():
    """
    ### 返回系统环境变量PATH中第一个Python目录路径。
    如果环境变量PATH中没有Python目录路径则返回空字符串。
    """
    PATH_paths = __paths_in_PATH()
    if not PATH_paths:
        return ""
    return PATH_paths[0]


def __list_fd(_path, opt=GetFd.Both):
    """列出给定目录下的文件或文件夹，返回文件或文件夹列表。"""
    results = list()
    if os.path.isfile(_path):
        return results
    if opt == GetFd.Files:
        condi = os.path.isfile
    elif opt == GetFd.Dirs:
        condi = os.path.isdir
    elif opt == GetFd.Both:
        condi = lambda p: os.path.isfile(p) or os.path.isdir(p)
    else:
        return results
    try:
        files_dirs = os.listdir(_path)
    except Exception:
        return results
    for item in files_dirs:
        if condi(os.path.join(_path, item)):
            results.append(item)
    return results


def __valid_path_list(dir):
    """
    ### 判断指定路径是否为Python或Anaconda3目录。
    将确认为Python目录的路径或Anaconda3内Python目录路径添加到列表并返回。
    """
    dir = os.path.normpath(dir)
    python_env_paths = list()
    files = __list_fd(dir, GetFd.Files)
    if PYTHON_EXE in files and __fsize(dir, PYTHON_EXE):
        python_env_paths.append(dir)
    if P_CONDA_EXE in files and __fsize(dir, P_CONDA_EXE):
        env_d = os.path.join(dir, CONDA_ENVS)
        if not os.path.isdir(env_d):
            return python_env_paths
        for env_p in __list_fd(env_d, GetFd.Dirs):
            env_p = os.path.join(env_d, env_p)
            if PYTHON_EXE in __list_fd(env_p, GetFd.Files):
                python_env_paths.append(env_p)
    return python_env_paths


def all_py_paths():
    """
    ### 返回存在 Python 解释器的目录路径列表

    只在常用安装位置的直接子目录内搜索 Python 可执行文件

    例外：对于 AppData\Local\Programs 目录，此函数在其直接子目录的子目录内搜索
    """
    common_locations = __common_location()
    dirs_interpreter_in = __paths_in_PATH()
    for level_1_common in common_locations[Level.level_1]:
        for dir in __list_fd(level_1_common, GetFd.Dirs):
            level_1_full = os.path.join(level_1_common, dir)
            for path in __valid_path_list(level_1_full):
                if path in dirs_interpreter_in:
                    continue
                dirs_interpreter_in.append(path)
    for level_2_common in common_locations[Level.level_2]:
        for sub_dir in __list_fd(level_2_common, GetFd.Dirs):
            sub_dir_full = os.path.join(level_2_common, sub_dir)
            for sub_dir_sub in __list_fd(sub_dir_full, GetFd.Dirs):
                for _path in __valid_path_list(os.path.join(sub_dir_full, sub_dir_sub)):
                    if _path in dirs_interpreter_in:
                        continue
                    dirs_interpreter_in.append(_path)
    return dirs_interpreter_in
