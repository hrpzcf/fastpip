# -*- coding: utf-8 -*-

import os
import re

from psutil import disk_partitions


def _possible_location():
    '''生成各磁盘上的常见的Python安装目录列表。'''
    most_possible_path = []
    common_dir = (
        'Program Files',
        'Program Files (x86)',
        os.path.join('Anaconda3', 'envs'),
    )
    disk_parts = [dp.device for dp in disk_partitions()]
    for dp in disk_parts:
        for cd in common_dir:
            full_path = os.path.join(dp, cd)
            if os.path.exists(full_path):
                most_possible_path.append(full_path)
    most_possible_path.extend(disk_parts)
    most_possible_path.append(os.path.expanduser('~'))
    full_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Programs')
    if os.path.exists(full_path):
        most_possible_path.append(full_path)
    return most_possible_path


def _paths_in_PATH():
    '''
    查找系统环境变量PATH中的Python目录路径列表。
    仅根据"目录中是否存在python.exe文件且大小不为0"进行简单查找。
    '''
    paths_found = []
    PATH_paths = os.environ['PATH'].split(';')
    for PATH_path in PATH_paths:
        try:
            PATH_path_files = os.listdir(PATH_path)
        except Exception:
            continue
        try:
            file_size = os.path.getsize(os.path.join(PATH_path, 'python.exe'))
        except Exception:
            continue
        PATH_path = os.path.join(PATH_path, '')
        if (
            'python.exe' in PATH_path_files
            and PATH_path not in paths_found
            and file_size
        ):
            paths_found.append(PATH_path)
    return paths_found


def cur_py_path():
    '''默认Python目录路径（系统环境变量PATH中第一个Python目录路径）。'''
    PATH_paths = _paths_in_PATH()
    if not PATH_paths:
        return ''
    return PATH_paths[0]


def all_py_paths():
    '''
    返回存在Python解释器的目录。
    如果在可能的安装目录中的子文件夹里找不到解释器，那就再深入一层目录，到此为止。
    '''
    dirs_in_possible_location, deeper_location = [], []
    paths_py_exists = _paths_in_PATH()
    for path in _possible_location():
        try:
            dirs_and_files = os.listdir(path)
        except Exception:
            continue
        for item in dirs_and_files:
            possible_dir = os.path.join(path, item)
            if os.path.isdir(possible_dir):
                dirs_in_possible_location.append(possible_dir)
    for possible_dir in dirs_in_possible_location:
        try:
            dirs_and_files = os.listdir(possible_dir)
        except Exception:
            continue
        possible_dir = os.path.join(possible_dir, '')
        if 'python.exe' in dirs_and_files:
            if possible_dir not in paths_py_exists:
                paths_py_exists.append(possible_dir)
        else:
            for deeper in dirs_and_files:
                path_deeper = os.path.join(possible_dir, deeper)
                if os.path.isdir(path_deeper):
                    deeper_location.append(path_deeper)
    for deeper_path in deeper_location:
        try:
            dirs_and_files = os.listdir(deeper_path)
        except Exception:
            continue
        deeper_path = os.path.join(deeper_path, '')
        if (
            'python.exe' in dirs_and_files
            and deeper_path not in paths_py_exists
        ):
            paths_py_exists.append(deeper_path)
    return paths_py_exists
