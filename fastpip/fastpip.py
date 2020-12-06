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
from subprocess import (
    PIPE,
    STARTF_USESHOWWINDOW,
    STARTUPINFO,
    STDOUT,
    SW_HIDE,
    Popen,
    TimeoutExpired,
)
from threading import Thread
from time import sleep

from .errors import *
from .findpypath import all_py_paths, cur_py_path

if os.name != 'nt':
    raise 适用平台异常('运行于不支持的操作系统。')

_SHOW_RUNNING_TIPS = True
_startupinfo = STARTUPINFO()
_startupinfo.dwFlags = STARTF_USESHOWWINDOW
_startupinfo.wShowWindow = SW_HIDE

# 预设镜像源：
index_urls = {
    'aliyun': 'https://mirrors.aliyun.com/pypi/simple/',  # 阿里源
    'tencent': 'https://mirrors.cloud.tencent.com/pypi/simple',  # 腾讯源
    'douban': 'https://pypi.doubanio.com/simple/',  # 豆瓣源
    'huawei': 'https://mirrors.huaweicloud.com/repository/pypi/simple',  # 华为源
    'opentuna': 'https://opentuna.cn/pypi/web/simple',  # 清华源
    'tsinghua': 'https://pypi.tuna.tsinghua.edu.cn/simple',  # 清华源
    'netease': 'https://mirrors.163.com/pypi/simple/',  # 网易源
}

# pip 部分命令
_pipcmds = {
    'info': ('-V',),
    'list': ('list',),
    'outdated': ('list', '--outdated'),
    'pip-upgrade': ('install', 'pip', '-U'),
    'set_index': ('config', 'set', 'global.index-url'),
    'get_index': ('config', 'list'),
    'install': ('install',),
    'uninstall': ('uninstall', '-y'),
    'search': ('search',),
}


class _PipInfo:
    '''PipInfo类，提供内部使用。'''

    def __init__(self, pipver, path, pyver):
        self.path = path
        self.pyver = pyver
        self.pipver = pipver

    def __str__(self):
        return 'pip_info(pipver={}, path={}, pyver={})'.format(
            self.pipver, self.path, self.pyver
        )

    __repr__ = __str__


def _tips_and_wait(tips):
    '''打印等待中提示信息，返回线程实例。'''

    def _print_tips(tips):
        global _SHOW_RUNNING_TIPS
        num, dot = 0, '.'
        while _SHOW_RUNNING_TIPS:
            print('{}{}{}'.format(tips, dot * num, '   '), end='\r')
            num = 0 if num == 3 else num + 1
            sleep(0.5)
        _SHOW_RUNNING_TIPS = True
        print('{}'.format("  " * (len(tips) + 3)), end='\r')

    tips_thread = Thread(target=_print_tips, args=(tips,))
    tips_thread.start()
    return tips_thread


def _execute_cmd(cmds, tips, no_output, no_tips, timeout):
    '''执行命令，输出等待提示语、输出命令执行结果并返回。'''
    global _SHOW_RUNNING_TIPS
    if not no_tips:
        tips_thread = _tips_and_wait(tips)
    exec_f = Popen(
        cmds,
        stdout=PIPE,
        stderr=STDOUT,
        universal_newlines=True,
        startupinfo=_startupinfo,
    )
    try:
        exec_out = exec_f.communicate(timeout=timeout)
    except TimeoutExpired:
        exec_out = '', -1
    if not no_tips:
        _SHOW_RUNNING_TIPS = False
        tips_thread.join()
    if not no_output:
        print(exec_out[0], end='')
    return exec_out[0], exec_f.returncode


def _fix_bad_code(string):
    '''将pip search返回的文字中的乱码(#&1234;之类的字符)转换成正确的文字。'''
    for badcode in re.findall(r'(?:#&|&#)\d+?;', string):
        try:
            string = string.replace(badcode, chr(int(badcode[2:-1])))
        except Exception:
            pass
    return string


class PyEnv:
    '''
    Python环境类，此类接受一个指向Python解释器所在目录的路径参数（字符串）。
    此类实例的所有pip操作方法都将基于该路径参数所指的Python环境，不会对系统中其他
    Python环境产生影响。
    PyEnv类无参数实例化时，默认使用cur_py_path函数选取系统环境变量PATH中的
    首个Python目录路径，如果系统环境变量PATH中没有找到Python目录路径，则调用
    all_py_paths函数自动在本地硬盘常用安装位置查找Python目录，如果仍未找到，则抛出
    "目录查找异常"。
    PyEnv类有参数实例化时，如果参数path数据类型不是"str"或所指的路径中没找到Python
    解释器，则抛出"PyEnvNotFound"异常。
    '''

    def __init__(self, path=''):
        if path == '':
            self.env_path = PyEnv._find_py_dir()
        elif PyEnv._check_path(path):
            self.env_path = os.path.join(path, '')
        else:
            raise PyEnvNotFound('"{}"不是有效的Python目录路径。'.format(path))

    def __str__(self):
        return '{} @ {}'.format(self.py_info(), self.env_path)

    def __setattr__(self, name, value):
        if name == 'env_path' and hasattr(self, name):
            print('PyEnv实例的env_path属性不可修改。')
        elif name == 'pip_readied':
            print('PyEnv实例的pip_readied属性不可修改。')
        else:
            super().__setattr__(name, value)

    @property
    def pip_readied(self):
        return bool(self.pip_path())

    @staticmethod
    def _find_py_dir():
        py_path = cur_py_path()
        if not py_path:
            py_path = all_py_paths()
            if not py_path:
                raise 目录查找异常('没有找到Python安装目录。')
            py_path = py_path[0]
        return py_path

    @staticmethod
    def _check_path(path):
        '''检查参数path是否是一个有效的Python目录路径。'''
        if not isinstance(path, str) or not os.path.exists(
            os.path.join(path, 'python.exe')
        ):
            return False
        return True

    @staticmethod
    def _check_timeout(timeout):
        if not isinstance(timeout, (int, float)):
            if timeout is None:
                return True
            raise 数据类型异常('参数timeout值应为None、整数或浮点数。')
        if timeout < 1:
            raise 参数值异常('超时参数timeout的值不能小于1。')
        return True

    def py_info(self):
        '''获取Python版本信息。'''
        source_code = 'import sys;sys.stdout.write(sys.version)'
        cur_dir_path = os.path.dirname(os.path.abspath(__file__))
        py_file_path = os.path.join(cur_dir_path, 'pyinfo.py')
        if not os.path.isfile(py_file_path):
            if not os.path.exists(cur_dir_path):
                try:
                    os.makedirs(cur_dir_path)
                except Exception:
                    pass
            try:
                with open(py_file_path, 'wt', encoding='utf-8') as py_file:
                    py_file.write(source_code)
            except Exception:
                pass
        result, retcode = _execute_cmd(
            (os.path.join(self.env_path, 'python.exe'), py_file_path),
            '',
            True,
            True,
            None,
        )
        ver_info = 'Python {} :: {} bit'
        if retcode or not result:
            return ver_info.format('0.0.0', '?')
        info = re.match(
            r'(\d+\.\d+\.\d+) (?:\(|\|).+(32|64) bit \(.+\)', result
        )
        if not info:
            return ver_info.format('0.0.0', '?')
        return ver_info.format(*info.groups())

    def pip_path(self):
        '''
        根据env_path属性所指的Python安装目录获取pip可执行文件路径。
        如果Scripts目录不存在或无法打开则抛出"目录查找异常"。
        如果在Scripts目录中没有找到pip可执行文件则抛出"文件查找异常"。
        :return: str, 该PyEnv实例的pip可执行文件的完整路径或空字符。
        '''
        dir_pip_exists = os.path.join(self.env_path, 'Scripts')
        try:
            dirs_and_files = os.listdir(dir_pip_exists)
        except Exception:
            return ''
        for dir_or_file in dirs_and_files:
            if os.path.isdir(os.path.join(dir_pip_exists, dir_or_file)):
                continue
            result = re.match(r'^pip.*\.exe$', dir_or_file)
            if result:
                return os.path.join(dir_pip_exists, result.group())
        return ''

    def pip_info(self):
        '''
        获取该目录的pip版本信息。
        如果获取到pip版本信息，则返回一个PipInfo实例，可以通过访问实例的
        pipver、path、pyver属性分别获取到pip版本号、pip目录路径、该pip所在的Python
        版本号；
        如果没有获取到信息或获取到信息但未正确匹配到信息格式，则返回None。
        直接打印PipInfo实例则显示概览：pip_info(pip版本、pip路径、相应Python版本)。
        :return: 匹配到pip版本信息：_PipInfo实例；未获取到pip版本信息：返回None。
        '''
        if not self.pip_readied:
            return
        cmds = [self.pip_path(), *_pipcmds['info']]
        result, retcode = _execute_cmd(
            cmds, tips='', no_output=True, no_tips=True, timeout=None
        )
        if retcode or not result:
            return
        result = re.match('pip (.+) from (.+) \(python (.+)\)', result.strip())
        if result:
            res = result.groups()
            if len(res) == 3:
                return _PipInfo(*res)
        return None

    @staticmethod
    def _clean_info(string):
        '''清理pip包名列表命令的无关输出。'''
        result = re.search(r'Package\s+Version\n[-\s]+\n(.+)', string, re.S)
        if not result:
            return []
        return re.findall(r'^\S+\s+\S+$', result.group(1), re.M)

    def pkgs_info(self, *, no_output=True, no_tips=True, timeout=None):
        '''
        获取该Python目录下已安装的包列表，列表包含(包名, 版本)元组，没有获取到则返回
        空列表。
        :param no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :param no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None。
        :return: lsit[tuple[str, str]] or list[], 包含(第三方包名, 版本)元组的列表
        或空列表。
        '''
        if not self.pip_readied:
            return []
        self._check_timeout(timeout)
        info_list, tips = [], '正在获取(包名, 版本)列表'
        cmds = [self.pip_path(), *_pipcmds['list']]
        result, retcode = _execute_cmd(cmds, tips, no_output, no_tips, timeout)
        if retcode or not result:
            return info_list
        info = self._clean_info(result)
        for pkg in info:
            pkg = pkg.split(' ')
            info_list.append((pkg[0], pkg[-1]))
        return info_list

    def pkg_names(self, *, no_output=True, no_tips=True, timeout=None):
        '''
        获取该Python目录下已安装的包名列表，没有获取到包名列表则返回空列表。
        :param no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :param no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :param timeout: float, 命令执行超时时长，单位为秒。
        :return: list[str...] or lsit[], 包含包名的列表或空列表。
        '''
        if not self.pip_readied:
            return []
        self._check_timeout(timeout)
        name_list, tips = [], '正在获取包名列表'
        cmds = [self.pip_path(), *_pipcmds['list']]
        result, retcode = _execute_cmd(cmds, tips, no_output, no_tips, timeout)
        if retcode or not result:
            return name_list
        info = self._clean_info(result)
        for pkg in info:
            pkg = pkg.split(' ')
            name_list.append(pkg[0])
        return name_list

    def outdated(self, *, no_output=True, no_tips=True, timeout=30):
        '''
        获取可更新的包列表，列表包含(包名, 已安装版本, 最新版本, 安装包类型)元组。
        如果没有获取到或者没有可更新的包，返回空列表。
        检查更新时，环境中已安装的包越多耗费时间越多，请耐心等待。
        :param no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :param no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None。
        :return: lsit[tuple[str, str, str, str]] or lsit[],
        包含(包名, 已安装版本, 最新版本, 安装包类型)的列表或空列表。
        '''
        if not self.pip_readied:
            return []
        self._check_timeout(timeout)
        cmds = [self.pip_path(), *_pipcmds['outdated']]
        outdated_pkgs_info, tips = [], '正在检查更新'
        result, retcode = _execute_cmd(cmds, tips, no_output, no_tips, timeout)
        if retcode or not result:
            return outdated_pkgs_info
        result = result.strip().split('\n')
        pattern1 = r'^(\S+)\s+(\S+)\s+(\S+)\s+(sdist|wheel)$'
        pattern2 = r'^(\S+) \((\S+)\) - Latest: (\S+) \[(sdist|wheel)\]$'
        for pkg_ver_info in result:
            res = re.match(pattern1, pkg_ver_info,)
            if res:
                outdated_pkgs_info.append(res.groups())
        if not outdated_pkgs_info:
            for pkg_ver_info in result:
                res = re.match(pattern2, pkg_ver_info,)
                if res:
                    outdated_pkgs_info.append(res.groups())
        return outdated_pkgs_info

    def upgrade_pip(
        self, *, index_url='', no_output=True, no_tips=True, timeout=None,
    ):
        '''
        升级pip自己。
        :param index_url: str, 镜像源地址，可为空字符串，默认使用系统内设置的
        全局镜像源。
        :param no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数
        设置为False）。
        :param no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参
        数设置为False）。
        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None。
        :return: bool, 命令退出状态，True表示升级成功，False表示设置失败。
        '''
        if not self.pip_readied:
            return False
        self._check_timeout(timeout)
        tips = '正在升级pip'
        cmds = [self.pip_path(), *_pipcmds['pip-upgrade']]
        if index_url:
            cmds.extend(('-i', index_url))
        return not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1]

    def set_global_index(self, index_url=index_urls['opentuna']):
        '''
        设置pip全局镜像源地址。
        :param index_url: str, 镜像源地址，参数可省略。
        :return: bool, 退出状态，True表示设置成功，False表示设置失败。
        '''
        if not self.pip_readied:
            return False
        if not isinstance(index_url, str):
            raise 数据类型异常('镜像源地址参数的数据类型应为字符串。')
        cmds = [self.pip_path(), *_pipcmds['set_index'], index_url]
        return not _execute_cmd(
            cmds, tips='', no_output=True, no_tips=True, timeout=None
        )[1]

    def get_global_index(self):
        '''
        显示当前pip全局镜像源地址。
        :return: str, 当前系统pip全局镜像源地址。
        '''
        if not self.pip_readied:
            return ''
        cmds = [self.pip_path(), *_pipcmds['get_index']]
        result, retcode = _execute_cmd(
            cmds, '', no_output=True, no_tips=True, timeout=None
        )
        if retcode:
            return ''
        match_res = re.match(r"^global.index-url='(.+)'$", result)
        if not match_res:
            return ''
        return match_res.group(1)

    def install(self, *names, **kwargs):
        '''
        安装Python第三方包。
        包名names必须提供，其他参数可以省略，但除了names参数，其他需要指定的参数需以
        关键字参数方式指定。
        注意：包名names中只要有一个不可安装（无资源等），其他包也不会被安装。所以如果
        你不能保证names中所有的包都能被安装，那最好只传一个包名参数给install，在外部
        循环调用install方法安装所有的包。
        :param names: str, 第三方包名（可变数量参数）。
        :param index_url: str, 镜像源地址。
        :param upgrade: bool, 是否以升级模式安装（如果之前已安装该包，则以升级模式
        安装会卸载旧版本安装新版本，反之会跳过安装，不会安装新版本）
        :param no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :param no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置
        为False）。
        :param timeout: int or float, 任务超时限制，单位为秒，可设为None表示无限制。
        :return: tuple[tuple[str...], bool], 返回((包名...), 退出状态)元组，包名names
        中只要有一个不可安装则所有传入的包名都不会被安装，退出状态为False。
        '''
        if not self.pip_readied:
            return tuple()
        index_url = kwargs.get('index_url', '')
        timeout = kwargs.get('timeout', None)
        upgrade = kwargs.get('upgrade', False)
        no_tips = kwargs.get('no_tips', True)
        no_output = kwargs.get('no_output', True)
        if not all(isinstance(s, str) for s in names):
            raise 数据类型异常('包名参数的数据类型应为字符串。')
        if not isinstance(index_url, str):
            raise 数据类型异常('镜像源地址参数数据类型应为字符串。')
        self._check_timeout(timeout)
        tips = '正在安装{}'.format(','.join(names))
        cmds = [self.pip_path(), *_pipcmds['install'], *names]
        if index_url:
            cmds.extend(('-i', index_url))
        if upgrade:
            cmds.append('-U')
        return (
            names,
            not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1],
        )

    def uninstall(self, *names, **kwargs):
        '''
        卸载Python第三方包。
        注意：如果names中包含未安装的包名则跳过卸载，以下的退出状态仍为True。
        :param names: str, 第三方包名。
        :param no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :param no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置
        为False）。
        :param timeout: int or float, 任务超时限制，单位为秒，可设为None表示无限制。
        :return: tuple[tuple[str...], bool], 返回((包名...), 退出状态)元组，状态不
        为True则表示卸载失败。
        '''
        if not self.pip_readied:
            return tuple()
        timeout = kwargs.get('timeout', None)
        no_tips = kwargs.get('no_tips', True)
        no_output = kwargs.get('no_output', True)
        if not all(isinstance(s, str) for s in names):
            raise 数据类型异常('包名参数的数据类型应为字符串。')
        self._check_timeout(timeout)
        tips = '正在卸载{}'.format(','.join(names))
        cmds = [self.pip_path(), *_pipcmds['uninstall'], *names]
        return (
            names,
            not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1],
        )

    def search(
        self, keywords, *, no_output=True, no_tips=True, timeout=None,
    ):
        '''
        以关键字搜索包名。
        参数keywords应为包含关键字(str)的元组、列表或集合。
        返回包含(包名, 最新版本, 概述)元组的列表。
        :param keywords: tuple or lsit or set, 关键字集合。
        :param no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :param no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :param timeout: int or float, 任务超时时长，单位为秒，可设为None。
        :return: list[tuple[str, str, str]], 包含(包名, 最新版本, 概述)元组的列表。
        '''
        if not self.pip_readied:
            return []
        if not isinstance(keywords, (tuple, list, set)):
            raise 数据类型异常('搜索关键字的数据类型应为包含str的tuple、lsit或set。')
        if not all(isinstance(s, str) for s in keywords):
            raise 数据类型异常('搜索关键字的数据类型应为包含str的tuple、lsit或set。')
        self._check_timeout(timeout)
        search_results, tips = [], '正在搜索{}'.format('、'.join(keywords))
        cmds = [self.pip_path(), *_pipcmds['search'], *keywords]
        result, retcode = _execute_cmd(cmds, tips, no_output, no_tips, timeout)
        if retcode:
            return search_results
        result = result.split('\n')
        pattern = re.compile(r'^(.+) \((.+)\)\s+\- (.+)$')
        for search_result in result:
            res = pattern.match(search_result)
            if res:
                *name_and_version, summary = res.groups()
                summary = _fix_bad_code(summary)
                search_results.append((*name_and_version, summary))
        return search_results
