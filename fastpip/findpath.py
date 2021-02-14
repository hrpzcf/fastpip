# -*- coding: utf-8 -*-

import os

from psutil import disk_partitions


def _common_location():
    """生成各磁盘上的常见的Python安装目录列表。"""
    most_possible_path = []
    common_dir = (
        'Program Files',
        'Program Files (x86)',
        os.path.join('Anaconda3', 'envs'),
    )
    most_possible_path.append(os.path.expanduser('~'))
    disk_parts = [dp.device for dp in disk_partitions()]
    most_possible_path.extend(disk_parts)
    for dp in disk_parts:
        for cd in common_dir:
            full_path = os.path.join(dp, cd)
            if not os.path.isdir(full_path):
                continue
            most_possible_path.append(full_path)
    appd = os.path.join(os.getenv('LOCALAPPDATA'), 'Programs')
    if os.path.exists(appd):
        most_possible_path.append(appd)
    return most_possible_path


def _paths_in_PATH():
    """
    查找系统环境变量PATH中的Python目录路径列表。
    仅根据"目录中是否存在python.exe文件且大小不为0"进行简单查找。
    """
    paths_found = []
    PATH_paths = os.getenv('PATH', '').split(';')
    for PATH_path in PATH_paths:
        try:
            PATH_path_files = os.listdir(PATH_path)
        except Exception:
            continue
        try:
            file_size = os.path.getsize(os.path.join(PATH_path, 'python.exe'))
        except Exception:
            continue
        PATH_path = os.path.normpath(PATH_path)
        if (
            'python.exe' in PATH_path_files
            and PATH_path not in paths_found
            and file_size
        ):
            paths_found.append(PATH_path)
    return paths_found


def cur_py_path():
    """
    返回系统环境变量PATH中第一个Python目录路径。
    如果环境变量PATH中没有Python目录路径则返回空字符串。
    """
    PATH_paths = _paths_in_PATH()
    if not PATH_paths:
        return ''
    return PATH_paths[0]


def all_py_paths():
    """
    返回存在Python解释器的目录。
    如果在可能的安装目录中的子文件夹里找不到解释器，只再深入一层目录寻找。
    """
    common_location, deeper_location = [], []
    interpreter_exists = _paths_in_PATH()
    for _path in _common_location():
        try:
            dirs_and_files = os.listdir(_path)
        except Exception:
            continue
        for item in dirs_and_files:
            possible_d = os.path.join(_path, item)
            if os.path.isdir(possible_d):
                common_location.append(possible_d)
    for possible_d in common_location:
        try:
            dirs_and_files = os.listdir(possible_d)
        except Exception:
            continue
        possible_d = os.path.normpath(possible_d)
        if 'python.exe' in dirs_and_files:
            if possible_d in interpreter_exists:
                continue
            interpreter_exists.append(possible_d)
        else:
            for deep in dirs_and_files:
                path_deeper = os.path.join(possible_d, deep)
                if not os.path.isdir(path_deeper):
                    continue
                deeper_location.append(path_deeper)
    for deeper_path in deeper_location:
        try:
            dirs_and_files = os.listdir(deeper_path)
        except Exception:
            continue
        deeper_path = os.path.normpath(deeper_path)
        if (
            'python.exe' in dirs_and_files
            and deeper_path not in interpreter_exists
        ):
            interpreter_exists.append(deeper_path)
    return interpreter_exists
