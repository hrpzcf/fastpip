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

import os
import re
import sys
from threading import Thread
from time import sleep

from .findpypath import all_py_paths, cur_py_path

if not os.name == 'nt':
    sys.stdout.write('程序运行于不受支持的系统，即将退出。')
    sleep(2)
    sys.exit(-1)

_show_running_tips = True

# 预设镜像源：
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
    'info': '"{}" -V',
    'list': '"{}" list',
    'outdated': '"{}" list --outdated',
    'update_pip': '"{}" install -i {} pip -U',
    'set_mirror': '"{}" config set global.index-url {}',
    'get_mirror': '"{}" config list',
    'install': '"{}" install {}{}{}',
    'uninstall': '"{}" uninstall -y {}',
    'search': '"{}" search {}',
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
    打印等待中提示信息。
    '''

    def _tips(msg):
        global _show_running_tips
        num, dot = 1, '.'
        while _show_running_tips:
            sys.stdout.write('\r')
            sys.stdout.write(f'{msg}{dot*num}{" "*5}')
            num = 1 if num == 6 else num + 1
            sleep(0.5)
        _show_running_tips = True
        sys.stdout.write(f'\r{"  " * (len(msg)+6)}\r')

    tips_thread = Thread(target=_tips, args=(msg,))
    # 在终端环境中进入Python交互模式，设置setDaemon(True)后主线程退出仍无法结束
    # tip_thread子线程，可能是因为终端环境成了主线程所以tip_thread不会被结束？遂
    # 用了_show_running_tip全局变量来控制子线程退出。
    tips_thread.setDaemon(True)
    tips_thread.start()
    return tips_thread


def _execute_cmd(cmd, tips, no_output, no_tips):
    '''执行命令，输出等待提示语、输出命令执行结果并返回。'''
    if not no_tips:
        tips_thread = _msg_wait(tips)
    execution_result = os.popen(cmd).read()
    global _show_running_tips
    if not no_tips:
        _show_running_tips = False
        tips_thread.join()
    if not no_output:
        sys.stdout.write(execution_result)
    return execution_result


def get_pip_path(py_path, *, auto_search):
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
                if res := re.match(r'^pip.*\.exe$', file):
                    return os.path.join(pip_dir, res.group())
            raise FileNotFoundError(f'Scripts目录({pip_dir})中没有找到pip可执行文件。')
        except Exception:
            raise PermissionError(f'目录({pip_dir})无法打开。')

    if not isinstance(py_path, str):
        raise TypeError('Python路径参数数据类型应为"str"。')
    if not py_path:
        if not auto_search:
            raise Exception('没有提供Python目录路径且禁止自动查找(auto_search=False)。')
        if not (py_path := cur_py_path()):
            if not (py_path := all_py_paths()):
                raise FileNotFoundError('自动查找没有找到任何Python安装目录。')
            py_path = py_path[0]
    return match_pip(os.path.join(py_path, 'Scripts'))


def pip_info(*, py_path=''):
    '''
    获取该目录的pip版本信息。
    如果获取到pip版本信息，则返回一个PipInfo实例，可以通过访问实例的
    pipver、path、pyver属性分别获取到pip版本号、pip目录路径、该pip所在的Python版本号；
    如果没有获取到信息，则返回'没有获取到 pip 版本信息。'字符串。
    直接打印PipInfo实例则显示概览：pip_info(pip版本、pip路径、相应Python版本)。
    '''
    pip_path = get_pip_path(py_path, auto_search=True)
    result = os.popen(_pipcmds['info'].format(pip_path)).read()
    if not result:
        return '没有获取到pip版本信息。'
    result = re.match('pip (.+) from (.+) \(python (.+)\)', result.strip())
    if result and len(res := result.groups()) == 3:
        return _PipInfo(*res)
    raise Exception('未期望的错误导致没有匹配到pip版本信息。')


def pkgs_info(py_path='', *, no_output=True, no_tips=True):
    '''
    获取该Python目录下包含(第三方包名, 版本)元组的列表。
    没有获取到则返回空列表。
    '''
    pip_path = get_pip_path(py_path, auto_search=True)
    info_list = []
    tips = '正在获取(包名, 版本)列表'
    command = _pipcmds['list'].format(pip_path)
    result = _execute_cmd(command, tips, no_output, no_tips)
    if not result:
        return info_list
    pkgs = result.strip().split('\n')[2:]
    for pkg in pkgs:
        pkg = pkg.split(' ')
        info_list.append((pkg[0], pkg[-1]))
    return info_list


def pkgs_name(py_path='', *, no_output=True, no_tips=True):
    '''
    获取该Python目录下安装的第三方包名列表。
    没有获取到包名列表则返回空列表。
    '''
    pip_path = get_pip_path(py_path, auto_search=True)
    name_list = []
    tips = '正在获取包名列表'
    command = _pipcmds['list'].format(pip_path)
    result = _execute_cmd(command, tips, no_output, no_tips)
    if not result:
        return name_list
    pkgs = result.strip().split('\n')[2:]
    for pkg in pkgs:
        pkg = pkg.split(' ')
        name_list.append(pkg[0])
    return name_list


def outdated(py_path='', *, no_output=True, no_tips=True):
    '''
    获取可更新的包列表，列表包含(包名, 目前版本, 最新版本, 安装包类型)元组。
    如果没有获取到或者没有可更新的包，返回空列表。
    因为检查更新源为国外服务器，环境中已安装的包越多耗费时间越多，请耐心等待。
    '''
    pip_path = get_pip_path(py_path, auto_search=True)
    outdated_pkgs_info = []
    command = _pipcmds['outdated'].format(pip_path)
    tips = 'PIP正在检查更新，请耐心等待'
    result = _execute_cmd(command, tips, no_output, no_tips)
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
    pip_path = get_pip_path(py_path, auto_search=True)
    result = os.popen(_pipcmds['update_pip'].format(pip_path, url))
    return result.read()


def set_mirror(py_path='', url=mirrors['opentuna']):
    '''
    设置pip镜像源地址。
    '''
    if not isinstance(url, str):
        raise TypeError('镜像源地址参数的数据类型应为"str"。')
    pip_path = get_pip_path(py_path, auto_search=True)
    result = os.popen(_pipcmds['set_mirror'].format(pip_path, url))
    return result.read()


def get_mirror(py_path=''):
    '''
    获取pip当前镜像源地址。
    '''
    pip_path = get_pip_path(py_path, auto_search=True)
    result = os.popen(_pipcmds['get_mirror'].format(pip_path))
    pattern = r"^global.index-url='(.+)'$"
    if not (res := re.match(pattern, result.read())):
        return ''
    return res.group(1)


def install(
    name, py_path='', *, mirror='', update=False, no_output=True, no_tips=True
):
    '''
    安装Python第三方库、包。
    包名name必须提供，其他参数可以省略，但除了name参数，其他要指定的参数需以关
    键字参数方式指定。
    '''
    if not isinstance(name, str):
        raise TypeError('包名参数的数据类型应为"str"。')
    if not isinstance(mirror, str):
        raise TypeError('镜像源地址参数数据类型应为"str"。')
    update_cmd = '' if not update else ' -U'
    url_cmd = '' if not mirror else f'-i {mirror} '
    pip_path = get_pip_path(py_path, auto_search=True)
    tips = f'正在安装{name}，请耐心等待'
    command = _pipcmds['install'].format(pip_path, url_cmd, name, update_cmd)
    result = _execute_cmd(command, tips, no_output, no_tips)
    return result


def bat_install(
    pkg_names,
    py_path='',
    *,
    mirror='',
    update=False,
    no_output=True,
    no_tips=True,
):
    '''批量安装第三方包。待完善。'''
    if not isinstance(pkg_names, (tuple, list, set)):
        raise TypeError('包名清单pkg_names数据类型应为"tuple"、"list"或"set"。')
    if not all(isinstance(s, str) for s in pkg_names):
        raise ValueError('包名清单pkg_names中包含的数据类型应为"str"。')
    install_info = []
    for pkg_name in pkg_names:
        install_info.append(
            install(
                pkg_name,
                py_path,
                mirror=mirror,
                update=update,
                no_output=no_output,
                no_tips=no_tips,
            )
        )
    return install_info


def uninstall(name, py_path='', *, no_output=True, no_tips=True):
    '''
    卸载Python第三方库、包。
    '''
    if not isinstance(name, str):
        raise TypeError('包名参数的数据类型应为"str"。')
    pip_path = get_pip_path(py_path, auto_search=True)
    tips = f'正在卸载{name}，请稍等'
    command = _pipcmds['uninstall'].format(pip_path, name)
    result = _execute_cmd(command, tips, no_output, no_tips)
    return result


def search(keywords, py_path='', no_output=True, no_tips=True):
    '''
    以关键字搜索包名。
    参数keywords应为包含关键字(str)的元组、列表或集合。
    返回包含(包名, 版本, 简短描述)元组的列表。
    '''
    if not isinstance(keywords, (tuple, list, set)):
        raise TypeError('搜索关键字的数据类型应为包含str的tuple、lsit或set。')
    if not all(isinstance(s, str) for s in keywords):
        raise TypeError('搜索关键字的数据类型应为包含str的tuple、lsit或set。')
    pip_path = get_pip_path(py_path, auto_search=True)
    keywords = ' '.join(keywords)
    tips = f'正在搜索{keywords}，请稍后'
    command = _pipcmds['search'].format(pip_path, keywords)
    result = _execute_cmd(command, tips, no_output, no_tips)
    result = result.split('\n')
    search_results = []
    pattern = re.compile(r'^(.+) \((.+)\)\s+\- (.+)$')
    for search_result in result:
        if res := pattern.match(search_result):
            search_results.append(res.groups())
    return search_results
