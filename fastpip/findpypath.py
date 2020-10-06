# -*- coding: utf-8 -*-

import os

import psutil


def find_most_likely():
    '''
    生成各磁盘上的常见的Python安装目录列表。
    '''
    disk_parts = [dp.device for dp in psutil.disk_partitions()]
    common_dir = 'Program Files', 'Program Files (x86)'
    most_likely_path = [
        full_path
        for dp in disk_parts
        for cd in common_dir
        if os.path.exists(full_path := os.path.join(dp, cd))
    ]
    most_likely_path.extend(disk_parts)
    most_likely_path.append(os.path.expanduser('~'))
    if os.path.exists(
        full_path := os.path.join(os.getenv('LOCALAPPDATA'), 'Programs')
    ):
        most_likely_path.append(full_path)
    return most_likely_path


def py_env_paths():
    '''
    系统环境变量PATH中的Python目录路径列表。
    '''
    environ_paths = os.environ['PATH'].split(';')
    cur_py_paths, final_py_paths, exclude = [], [], []
    for ukn_path in environ_paths:
        if 'python' in ukn_path.lower() and os.path.exists(ukn_path):
            cur_py_paths.append(os.path.join(ukn_path, ''))
    for ind1, cur1 in enumerate(cur_py_paths):
        cur_py_paths_cp = cur_py_paths[:]
        cur_py_paths_cp.pop(ind1)
        for cur2 in cur_py_paths_cp:
            if cur1.lower() != cur2.lower() and cur1.lower().startswith(
                cur2.lower()
            ):
                exclude.append(cur1)
                cur1 = cur2
        if cur1 not in final_py_paths and cur1 not in exclude:
            final_py_paths.append(cur1)
    for ind, shorter_py_path in enumerate(final_py_paths):
        shorter_py_path = os.path.split(shorter_py_path.strip(os.sep))
        if 'scripts' == shorter_py_path[-1].lower():
            final_py_paths[ind] = shorter_py_path[0]
    return final_py_paths


def cur_py_path():
    '''
    当前Python路径（系统环境变量PATH中第一个Python目录路径）。
    '''
    env_paths = py_env_paths()
    if not env_paths:
        return
    return env_paths[0]


def all_py_paths():
    '''
    返回存在Python解释器的目录。
    如果在可能的安装目录中的子文件夹里找不到解释器，那就再深入一层目录，再找不到就算了，
    毕竟没那么多时间去全盘搜索。
    '''
    exist_py_paths, deeper_paths = [], []
    for most_likely in find_most_likely():
        try:
            for py_path in os.listdir(most_likely):
                full_path = os.path.join(most_likely, py_path, '')
                if os.path.isdir(full_path):
                    if os.path.exists(os.path.join(full_path, 'python.exe')):
                        exist_py_paths.append(full_path)
                    else:
                        deeper_paths.append(full_path)
        except Exception:
            pass
    for deeper_path in deeper_paths:
        try:
            for sub_deeper_path in os.listdir(deeper_path):
                full_path = os.path.join(deeper_path, sub_deeper_path)
                if os.path.isdir(full_path) and os.path.exists(
                    os.path.join(full_path, 'python.exe')
                ):
                    exist_py_paths.append(full_path)
        except Exception:
            pass
    for env_path in py_env_paths():
        if env_path not in exist_py_paths:
            exist_py_paths.append(env_path)
    return exist_py_paths
