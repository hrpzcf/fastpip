# coding: utf-8

import os
from sys import winver

from psutil import disk_partitions

from ..common.common import *


class GetFd:
    """__list_fd 函数的 opt 参数所使用的枚举类型"""

    Dirs = 0
    Files = 1
    Both = 2


def __common_location():
    """生成各磁盘上的常见的Python安装目录路径列表。"""
    most_possible_path = list()
    cur_pyver = "Python" + winver.replace(".", "")  # 查询当前Python版本
    # 常用目录添加envs目录名称
    lst_common_dir = [
        "Program Files",
        "Program Files (x86)",
        "ProgramData",
        cur_pyver,
        os.path.join(cur_pyver, "envs"),
    ]
    most_possible_path.append(os.path.expanduser("~"))
    disk_parts = [dp.device for dp in disk_partitions()]
    most_possible_path.extend(disk_parts)
    for dp in disk_parts:
        for cd in lst_common_dir:
            full_path = os.path.join(dp, cd)
            if not os.path.isdir(full_path):
                continue
            most_possible_path.append(full_path)
    appd = os.path.join(os.getenv("LOCALAPPDATA"), "Programs")
    if os.path.exists(appd):
        most_possible_path.append(appd)
    return most_possible_path


def __fsize(*_fpath):
    """返回文件路径中文件的大小。"""
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


def __path_list(fd_name):
    """
    ### 判断指定路径是否为Python或Anaconda3目录。
    将确认为Python目录的路径或Anaconda3内Python目录路径添加到列表并返回。
    """
    fd_name = os.path.normpath(fd_name)
    python_env_paths = list()
    files = __list_fd(fd_name, GetFd.Files)
    if PYTHON_EXE in files and __fsize(fd_name, PYTHON_EXE):
        python_env_paths.append(fd_name)
    if P_CONDA_EXE in files and __fsize(fd_name, P_CONDA_EXE):
        env_d = os.path.join(fd_name, CONDA_ENVS)
        if not os.path.isdir(env_d):
            return python_env_paths
        for env_p in __list_fd(env_d, GetFd.Dirs):
            env_p = os.path.join(env_d, env_p)
            if PYTHON_EXE in __list_fd(env_p, GetFd.Files):
                python_env_paths.append(env_p)
    return python_env_paths


def all_py_paths():
    """
    ### 返回存在Python解释器的目录路径列表。
    只在常用安装位置深入搜索两层目录，不会过于深入。
    """
    paths_interpreter_exists = __paths_in_PATH()
    for common in __common_location():
        for level1 in __list_fd(common, GetFd.Dirs):
            l1f = os.path.join(common, level1)
            for _path in __path_list(l1f):
                if _path in paths_interpreter_exists:
                    continue
                paths_interpreter_exists.append(_path)
            for level2 in __list_fd(l1f, GetFd.Dirs):
                for _path in __path_list(os.path.join(l1f, level2)):
                    if _path in paths_interpreter_exists:
                        continue
                    paths_interpreter_exists.append(_path)
    return paths_interpreter_exists
