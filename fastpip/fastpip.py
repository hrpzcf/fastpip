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
from warnings import warn

from .errors import 参数值异常, 数据类型异常, 文件查找异常, 目录查找异常, 适用平台异常
from .findpypath import all_py_paths, cur_py_path

if os.name != 'nt':
    raise 适用平台异常('运行于不支持的操作系统。')

_SHOW_RUNNING_TIPS = True
_startupinfo = STARTUPINFO()
_startupinfo.dwFlags = STARTF_USESHOWWINDOW
_startupinfo.wShowWindow = SW_HIDE

# 预设镜像源：
index_urls = {
    'opentuna': 'https://opentuna.cn/pypi/web/simple',  # 清华源
    'tsinghua': 'https://pypi.tuna.tsinghua.edu.cn/simple',  # 清华源
    'tencent': 'https://mirrors.cloud.tencent.com/pypi/simple',  # 腾讯源
    'aliyun': 'https://mirrors.aliyun.com/pypi/simple/',  # 阿里源
    'douban': 'https://pypi.doubanio.com/simple/',  # 豆瓣源
    'huawei': 'https://mirrors.huaweicloud.com/repository/pypi/simple',  # 华为源
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


class _PipInfo(object):
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
    for badcode in re.findall(r'(?:#&|&#)\d+?;', string):
        string = string.replace(badcode, chr(int(badcode[2:-1])))
    return string


class PyEnv(object):
    '''
    Python环境类，此类接受一个指向Python解释器所在目录的路径参数（字符串）。
    此类实例的所有pip操作方法都将基于该路径参数所指的Python环境，不会对系统中其他
    Python环境产生影响。
    PyEnv无路径参数实例化时，默认使用cur_py_path函数自动选取Python目录路径，您可以
    调用cur_py_path函数获取该Python目录路径用以确认当前操作的是哪个Python环境。
    '''

    def __init__(self, path=''):
        self.__path = self._check_path(path)

    def __str__(self):
        return '{} 位于 {}'.format(self.py_info(), self.__path)

    def _find_path(self, seek):
        if not seek:
            raise 目录查找异常('没有提供有效Python目录路径且未允许自动查找。')
        py_path = cur_py_path()
        if not py_path:
            py_path = all_py_paths()
            if not py_path:
                raise 目录查找异常('自动查找没有找到任何Python安装目录。')
            py_path = py_path[0]
        return py_path

    def _check_path(self, path):
        '''检查初始化参数path是否是一个有效的路径。'''
        if not isinstance(path, str):
            raise 数据类型异常('参数path类型应为字符串。')
        if not os.path.exists(path):
            if path == '':
                return self._find_path(True)
            raise 目录查找异常('参数path所指路径不存在。')
        if not os.path.isdir(path):
            raise 目录查找异常('参数path所指路径不是一个文件夹。')
        return os.path.join(path, '')

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
        cur_dir_path = os.path.dirname(os.path.abspath(__file__))
        result, retcode = _execute_cmd(
            (
                os.path.join(self.__path, 'python.exe'),
                os.path.join(cur_dir_path, 'pyinfo.py'),
            ),
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
        根据__path属性所指的Python安装目录获取pip可执行文件路径。
        如果Scripts目录不存在或无法打开则抛出"目录查找异常"。
        如果在Scripts目录中没有找到pip可执行文件则抛出"文件查找异常"。
        :return: str, 该PyEnv实例的pip可执行文件的完整路径。
        '''
        if not self.__path:
            raise FileNotFoundError('本PyEnv实例Python安装目录信息丢失。')
        dir_pip_exists = os.path.join(self.__path, 'Scripts')
        try:
            dirs_and_files = os.listdir(dir_pip_exists)
        except Exception:
            raise 目录查找异常('目录{}不存在或无法打开。'.format(dir_pip_exists))
        for dir_or_file in dirs_and_files:
            if os.path.isdir(os.path.join(dir_pip_exists, dir_or_file)):
                continue
            result = re.match(r'^pip.*\.exe$', dir_or_file)
            if result:
                return os.path.join(dir_pip_exists, result.group())
        raise 文件查找异常('目录{}中没有找到pip可执行文件。'.format(dir_pip_exists))

    def pip_info(self):
        '''
        获取该目录的pip版本信息。
        如果获取到pip版本信息，则返回一个PipInfo实例，可以通过访问实例的
        pipver、path、pyver属性分别获取到pip版本号、pip目录路径、该pip所在的Python
        版本号；
        如果没有获取到信息或获取到信息但未正确匹配到信息格式，则返回None。
        直接打印PipInfo实例则显示概览：pip_info(pip版本、pip路径、相应Python版本)。
        :返回值: 匹配到pip版本信息：_PipInfo实例；未获取到pip版本信息：返回None。
        '''
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
            return ''
        return result.group(1).strip().split('\n')

    def pkgs_info(self, *, no_output=True, no_tips=True, timeout=None):
        '''
        获取该Python目录下已安装的包列表，列表包含(包名, 版本)元组，没有获取到则返回
        空列表。
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 命令执行超时时长，单位为秒，可设置为None。
        :返回值: lsit[tuple[str, str]] or list[], 包含(第三方包名, 版本)元组的列表
        或空列表。
        '''
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

    def pkgs_name(self, *, no_output=True, no_tips=True, timeout=None):
        '''旧方法，即将被移除。'''
        warn(
            '\nPyEnv 类 pkgs_name 方法现已被 pkg_names 方法'
            '代替，旧方法即将在 0.3.0 版本时移除，请及时更新你的源代码。',
            DeprecationWarning,
            stacklevel=2,
        )
        return self.pkg_names(
            no_output=no_output, no_tips=no_tips, timeout=timeout
        )

    def pkg_names(self, *, no_output=True, no_tips=True, timeout=None):
        '''
        获取该Python目录下已安装的包名列表，没有获取到包名列表则返回空列表。
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: float, 命令执行超时时长，单位为秒。
        :返回值: list[str...] or lsit[], 包含包名的列表或空列表。
        '''
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
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 命令执行超时时长，单位为秒，可设置为None。
        :返回值: lsit[tuple[str, str, str, str]] or lsit[],
        包含(包名, 已安装版本, 最新版本, 安装包类型)的列表或空列表。
        '''
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

    def update_pip(
        self, *, index_url='', no_output=True, no_tips=True, timeout=None,
    ):
        '''旧方法，即将被移除。'''
        warn(
            '\nPyEnv 类 update_pip 方法现已被 upgrade_pip 方法'
            '代替，旧方法即将在 0.3.0 版本时移除，请及时更新你的源代码。',
            DeprecationWarning,
            stacklevel=2,
        )
        return self.upgrade_pip(
            index_url=index_url,
            no_output=no_output,
            no_tips=no_tips,
            timeout=timeout,
        )

    def upgrade_pip(
        self, *, index_url='', no_output=True, no_tips=True, timeout=None,
    ):
        '''
        升级pip自己。
        :参数 index_url: str, 镜像源地址，可为空字符串，默认使用系统内设置的全局镜像源。
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 命令执行超时时长，单位为秒，可设置为None。
        :返回值: bool, 命令退出状态，True表示升级成功，False表示设置失败。
        '''
        self._check_timeout(timeout)
        tips = '正在升级pip'
        cmds = [self.pip_path(), *_pipcmds['pip-upgrade']]
        if index_url:
            cmds.extend(('-i', index_url))
        return not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1]

    def set_mirror(self, index_url=index_urls['opentuna']):
        '''旧方法，即将被移除。'''
        warn(
            '\nPyEnv 类 set_mirror 方法现已被 set_global_index 方法'
            '代替，旧方法即将在 0.3.0 版本时移除，请及时更新你的源代码。',
            DeprecationWarning,
            stacklevel=2,
        )
        return self.set_global_index(index_url)

    def set_global_index(self, index_url=index_urls['opentuna']):
        '''
        设置pip全局镜像源地址。
        :参数 index_url: str, 镜像源地址，参数可省略。
        :返回值: bool, 退出状态，True表示设置成功，False表示设置失败。
        '''
        if not isinstance(index_url, str):
            raise 数据类型异常('镜像源地址参数的数据类型应为字符串。')
        cmds = [self.pip_path(), *_pipcmds['set_index'], index_url]
        return not _execute_cmd(
            cmds, tips='', no_output=True, no_tips=True, timeout=None
        )[1]

    def show_mirror(self):
        '''旧方法，即将被移除。'''
        warn(
            '\nPyEnv 类 show_mirror 方法现已被 get_global_index 方法'
            '代替，旧方法即将在 0.3.0 版本时移除，请及时更新你的源代码。',
            DeprecationWarning,
            stacklevel=2,
        )
        return self.get_global_index()

    def get_global_index(self):
        '''
        显示当前pip全局镜像源地址。
        :返回值: str, 当前系统pip全局镜像源地址。
        '''
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

    def install(
        self,
        name,
        *,
        index_url='',
        update=False,
        upgrade=False,
        no_output=True,
        no_tips=True,
        timeout=None,
    ):
        '''
        安装Python第三方包。
        包名name必须提供，其他参数可以省略，但除了name参数，其他需要指定的参数需以关键
        字参数方式指定。
        :参数 name: str, 第三方包名。
        :参数 index_url: str, 镜像源地址。
        :参数 upgrade: bool, 是否以升级模式安装（如果之前已安装该包，则以升级模式安
        装会卸载旧版本安装新版本，反之会跳过安装，不会安装新版本）
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 任务超时时长，单位为秒，可设为None。
        :返回值: tuple[str, bool], 返回(包名, 退出状态)元组，状态不为True则表示安装失败。
        '''
        if not isinstance(name, str):
            raise 数据类型异常('包名参数的数据类型应为字符串。')
        if not isinstance(index_url, str):
            raise 数据类型异常('镜像源地址参数数据类型应为字符串。')
        self._check_timeout(timeout)
        tips = '正在安装{}'.format(name)
        cmds = [self.pip_path(), *_pipcmds['install'], name]
        if index_url:
            cmds.extend(('-i', index_url))
        if upgrade or update:
            # update 参数即将弃用提醒
            if update:
                warn(
                    '\nPyEnv类install方法 update 参数已由 upgrade '
                    '参数代替并即将在 0.3.0 版本弃用，请及时更新您的源代码。',
                    DeprecationWarning,
                    stacklevel=2,
                )
            cmds.append('-U')
        return (
            name,
            not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1],
        )

    def uninstall(self, name, *, no_output=True, no_tips=True, timeout=None):
        '''
        卸载Python第三方包。
        :参数 name: str, 第三方包名。
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 任务超时时长，单位为秒，可设为None。
        :返回值: tuple[str, bool], 返回(包名, 退出状态)元组，状态不为True则表示卸载失败。
        '''
        if not isinstance(name, str):
            raise 数据类型异常('包名参数的数据类型应为"str"。')
        self._check_timeout(timeout)
        tips = '正在卸载{}'.format(name)
        cmds = [self.pip_path(), *_pipcmds['uninstall'], name]
        return (
            name,
            not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1],
        )

    def search(
        self, keywords, *, no_output=True, no_tips=True, timeout=None,
    ):
        '''
        以关键字搜索包名。
        参数keywords应为包含关键字(str)的元组、列表或集合。
        返回包含(包名, 最新版本, 概述)元组的列表。
        :参数 keywords: tuple or lsit or set, 关键字集合。
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 任务超时时长，单位为秒，可设为None。
        :返回值: list[tuple[str, str, str]], 包含(包名, 最新版本, 概述)元组的列表。
        '''
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
                name, version, summary = res.groups()
                summary = _fix_bad_code(summary)
                search_results.append((name, version, summary))
        return search_results
