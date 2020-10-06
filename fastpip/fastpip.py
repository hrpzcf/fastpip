# -*- coding: utf-8 -*-

################################################################################
# MIT License

# Copyright (c) 2020 hrpzcf / hrp < hrpzcf@foxmail.com >

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################

# TODO 在IDLE运行输出异常

import os
import sys
from re import match
from threading import Thread
from time import sleep

from .findpypath import all_py_paths, cur_py_path

_show_running_tip = True

# 镜像源：
mirrors = {
    'opentuna': 'https://opentuna.cn/pypi/web/simple',  # 清华源
    'tsinghua': 'https://pypi.tuna.tsinghua.edu.cn/simple',  # 清华源
    'tencent': 'https://mirrors.cloud.tencent.com/pypi/simple',  # 腾讯源
    'aliyun': 'https://mirrors.aliyun.com/pypi/simple/',  # 阿里源
    'douban': 'https://pypi.doubanio.com/simple/',  # 豆瓣源
    'huawei': 'https://mirrors.huaweicloud.com/repository/pypi/simple',  # 华为源
    'netease': 'https://mirrors.163.com/pypi/simple/',  # 网易源
}

# pip 命令
_pipcmds = {
    'INFO': '"{}" -V',
    'LIST': '"{}" list',
    'OUTDATED': '"{}" list --outdated',
    'UPDATE_PIP': '"{}" install -i {} pip -U',
    'SET_MIRROR': '"{}" config set global.index-url {}',
    'GET_MIRROR': '"{}" config list',
    'INSTALL': '"{}" install {}{}{}',
    'UNINSTALL': '"{}" uninstall -y {}',
}


class _PipInfo(object):
    '''
    PipInfo类，提供内部使用。
    '''

    def __init__(self, pipver, path, pyver):
        self.path = path
        self.pyver = pyver
        self.pipver = pipver

    def __str__(self):
        return f'pip_info(pipver={self.pipver}, path={self.path}, pyver={self.pyver})'

    __repr__ = __str__


def _msg_wait(msg):
    '''
    打印等待提示信息。
    '''

    def show_msg(msg):
        global _show_running_tip
        num, dot = 1, '.'
        while _show_running_tip:
            sys.stdout.write(f'\r')
            sys.stdout.write(f'{msg}{dot*num}{" "*5}')
            num = 1 if num == 6 else num + 1
            sleep(0.5)
        sleep(0.1)
        _show_running_tip = True

    tip_thread = Thread(target=show_msg, args=(msg,))
    # 在终端环境中进入Python交互模式，设置setDaemon(True)后主线程退出仍无法结束
    # tip_thread子线程，可能是因为终端环境成了主线程所以tip_thread不会被结束？遂
    # 用了_show_running_tip全局变量来控制子线程退出。
    tip_thread.setDaemon(True)
    tip_thread.start()


def _start_cmd(command, tips, to_screen):
    '''
    执行命令并返回输出结果。
    '''

    def cmd_func(command):
        nonlocal result
        result = os.popen(command).read()

    _msg_wait(tips)
    result = ''
    cmd_thread = Thread(target=cmd_func, args=(command,))
    cmd_thread.start()
    cmd_thread.join()
    global _show_running_tip
    _show_running_tip = False
    sys.stdout.write(f'\r{"  " * (len(tips)+6)}\r')
    if to_screen:
        sys.stdout.write(result)
    return result


def get_pip_path(py_path, *, auto):
    '''
    根据参数py_path的Python路径获取pip可执行文件路径。
    如果Python路径为空字符串，则先查找系统环境变量PATH中的Python路径，找不到则
    继续查找全部磁盘中常用的Python安装目录，再找不到则抛出FileNotFoundError异常。
    如果传入参数py_path不是字符串类型，抛出TypeError异常。
    :参数 py_path: str, Python目录路径（非pip目录路径）。
    :返回值: str, 该Pyhton目录下的pip完整路径。
    '''

    def match_pip(pip_dir):
        try:
            for file in os.listdir(pip_dir):
                if res := match(r'^pip.*\.exe$', file):
                    return os.path.join(pip_dir, res.group())
            raise FileNotFoundError(f'Scripts目录({pip_dir})中没有找到pip可执行文件。')
        except Exception:
            raise PermissionError(f'目录({pip_dir})无法打开。')

    if not isinstance(py_path, str):
        raise TypeError('Python路径参数数据类型应为"str"。')
    if not py_path:
        if not auto:
            raise Exception('没有提供Python目录路径且禁止自动选择(auto=False)。')
        if not (py_path := cur_py_path()):
            if not (py_path := all_py_paths()):
                raise FileNotFoundError('自动查找没有找到任何Python安装目录。')
            py_path = py_path[0]
    return match_pip(os.path.join(py_path, 'Scripts'))


def pip_info(*, py_path=''):
    '''
    获取该目录的pip版本信息（包括pip版本、pip路径、相应Python版本）。
    如果获取到pip版本信息，则返回一个PipInfo实例，可以通过访问实例的
    pipver、path、pyver属性分别获取到pip版本号、pip所在目录、该pip所在的Python版本号；
    如果没有获取到信息，则返回'没有获取到 pip 版本信息。'字符串。
    直接打印PipInfo实例则显示概览。
    '''
    pip_path = get_pip_path(py_path, auto=True)
    result = os.popen(_pipcmds['INFO'].format(pip_path)).read()
    if not result:
        return '没有获取到 pip 版本信息。'
    result = match('pip (.+) from (.+) \(python (.+)\)', result.strip())
    if result and len(res := result.groups()) == 3:
        return _PipInfo(*res)
    raise Exception('未期望的错误导致没有匹配到pip版本信息。')


def pkgs_info(py_path='', *, to_screen=False):
    '''
    获取该Python目录下包含(第三方包名, 版本)元组的列表。
    没有获取到则返回空列表。
    '''
    pip_path = get_pip_path(py_path, auto=True)
    info_list = []
    tips = '正在获取(包名, 版本)列表'
    command = _pipcmds['LIST'].format(pip_path)
    result = _start_cmd(command, tips, to_screen)
    if not result:
        return info_list
    pkgs = result.strip().split('\n')[2:]
    for pkg in pkgs:
        pkg = pkg.split(' ')
        info_list.append((pkg[0], pkg[-1]))
    return info_list


def pkgs_name(py_path='', *, to_screen=False):
    '''
    获取该Python目录下安装的第三方包名列表。
    没有获取到包名列表则返回空列表。
    '''
    pip_path = get_pip_path(py_path, auto=True)
    name_list = []
    tips = '正在获取包名列表'
    command = _pipcmds['LIST'].format(pip_path)
    result = _start_cmd(command, tips, to_screen)
    if not result:
        return name_list
    pkgs = result.strip().split('\n')[2:]
    for pkg in pkgs:
        pkg = pkg.split(' ')
        name_list.append(pkg[0])
    return name_list


def outdated(py_path='', *, to_screen=False):
    '''
    获取可更新的包列表，列表包含(包名, 目前版本, 最新版本, 安装包类型)元组。
    如果没有获取到或者没有可更新的包，返回空列表。
    因为检查更新源为国外服务器，环境中已安装的包越多耗费时间越多，所以请耐心等待。
    '''
    pip_path = get_pip_path(py_path, auto=True)
    outdated_pkgs_info = []
    command = _pipcmds['OUTDATED'].format(pip_path)
    tips = 'PIP正在检查更新，请耐心等待'
    result = _start_cmd(command, tips, to_screen)
    if not result:
        return outdated_pkgs_info
    result = result.strip().split('\n')[2:]
    for pkg in result:
        outdated_pkgs_info.append(tuple(s for s in pkg.split(' ') if s))
    return outdated_pkgs_info


def update_pip(py_path='', url=mirrors['opentuna']):
    '''
    升级pip本身。
    '''
    pip_path = get_pip_path(py_path, auto=True)
    result = os.popen(_pipcmds['UPDATE_PIP'].format(pip_path, url))
    return result.read()


def set_mirror(py_path='', url=mirrors['opentuna']):
    '''
    设置pip镜像源地址。
    '''
    if not isinstance(url, str):
        raise TypeError('镜像源地址参数的数据类型应为"str"。')
    pip_path = get_pip_path(py_path, auto=True)
    result = os.popen(_pipcmds['SET_MIRROR'].format(pip_path, url))
    return result.read()


def get_mirror(py_path=''):
    '''
    获取pip当前镜像源地址。
    '''
    pip_path = get_pip_path(py_path, auto=True)
    result = os.popen(_pipcmds['GET_MIRROR'].format(pip_path))
    pattern = r"^global.index-url='(.+)'$"
    if not (res := match(pattern, result.read())):
        return ''
    return res.group(1)


def install(name, py_path='', *, mirror='', update=False, to_screen=False):
    '''
    安装Python第三方库、包。
    包名name必须提供，其他参数可以省略，但除了name参数，其他要指定的参数需以关
    键字参数方式指定。
    '''
    if not isinstance(name, str):
        raise TypeError(f'包名参数的数据类型应为"str"。')
    if not isinstance(mirror, str):
        raise TypeError('镜像源地址参数数据类型应为"str"。')
    update_cmd = '' if not update else ' -U'
    url_cmd = '' if not mirror else f'-i {mirror} '
    pip_path = get_pip_path(py_path, auto=True)
    tips = f'正在安装{name}，请耐心等待'
    command = _pipcmds['INSTALL'].format(pip_path, url_cmd, name, update_cmd)
    result = _start_cmd(command, tips, to_screen)
    return result


def uninstall(name, py_path='', *, to_screen=False):
    '''
    卸载Python第三方库、包。
    '''
    if not isinstance(name, str):
        raise TypeError(f'包名参数的数据类型应为"str"。')
    pip_path = get_pip_path(py_path, auto=True)
    tips = f'正在卸载{name}，请稍等'
    command = _pipcmds['UNINSTALL'].format(pip_path, name)
    result = _start_cmd(command, tips, to_screen)
    return result
