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
from subprocess import PIPE, STDOUT, Popen, TimeoutExpired
from threading import Thread
from time import sleep

from .errors import Pip未找到异常, 参数值异常, 参数数据类型异常, 目录查找异常, 适用平台异常
from .findpypath import all_py_paths, cur_py_path

if os.name != 'nt':
    raise 适用平台异常('运行于不支持的操作系统。')

_SHOW_RUNNING_TIPS = True

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
    'info': ('-V',),
    'list': ('list',),
    'outdated': ('list', '--outdated'),
    'update_pip': ('install', 'pip', '-U'),
    'set_mirror': ('config', 'set', 'global.index-url'),
    'get_mirror': ('config', 'list'),
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
    exec_fd = Popen(cmds, stdout=PIPE, stderr=STDOUT, universal_newlines=True)
    try:
        exec_result = exec_fd.communicate(timeout=timeout)
    except TimeoutExpired:
        exec_result = '', -1
    if not no_tips:
        _SHOW_RUNNING_TIPS = False
        tips_thread.join()
    if not no_output:
        print(exec_result[0], end='')
    return exec_result[0], exec_fd.returncode


def _fix_bad_code(string):
    for badcode in re.findall(r'(?:#&|&#)\d+?;', string):
        string = string.replace(badcode, chr(int(badcode[2:-1])))
    return string


class PyEnv(object):
    def __init__(self, path=''):
        self.__path = self._check_path(path)

    @staticmethod
    def _check_path(path):
        '''检查初始化参数path是否是一个有效的路径。'''
        if not isinstance(path, str):
            raise 参数数据类型异常('参数path类型应为字符串')
        if not os.path.exists(path):
            if path == '':
                return path
            raise 目录查找异常('参数path所指目录路径不存在。')
        if not os.path.isdir(path):
            raise 目录查找异常('参数path所指路径不是一个文件夹。')
        return path

    @staticmethod
    def _check_timeout(timeout):
        if not isinstance(timeout, (int, float)):
            if timeout is None:
                return True
            raise 参数数据类型异常('参数timeout数据类型应为整数、浮点数或None。')
        return True

    def pip_path(self, *, seek=True):
        '''
        根据path属性所指的Python路径获取pip可执行文件路径。
        a).如果Python路径path属性为空字符串：1.如果参数seek为真，则优先查找系统环境
        变量PATH中的Python路径，找不到则继续查找全部磁盘中常用的Python安装目录位置，
        再找不到则抛出<目录查找异常>；2.如果参数seek为假，则直接抛出<目录查找异常>。
        b).如果Python目录中Scripts目录不存在、无法打开、Scripts目录中没有pip*.exe文
        件则抛出<Pip未找到异常>。
        :参数 seek: bool, 系统环境变量中没找到Python安装目录时是否自动搜索(有限搜索)。
        :返回值: str, 该Pyhton目录下的pip完整路径。
        '''

        def match_pip(pip_dir):
            try:
                dirs_and_files = os.listdir(pip_dir)
            except Exception:
                raise Pip未找到异常('目录{}不存在或无法打开。'.format(pip_dir))
            for possible_file in dirs_and_files:
                result = re.match(r'^pip.*\.exe$', possible_file)
                if result:
                    return os.path.join(pip_dir, result.group())
            raise Pip未找到异常('目录{}中没有找到pip可执行文件。'.format(pip_dir))

        if not self.__path:
            if not seek:
                raise 目录查找异常('没有提供有效Python目录路径且未允许自动查找。')
            self.__path = cur_py_path()
            if not self.__path:
                py_path = all_py_paths()
                if not py_path:
                    raise 目录查找异常('自动查找没有找到任何Python安装目录。')
                self.__path = py_path[0]
        return match_pip(os.path.join(self.__path, 'Scripts'))

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
        cmds = [self.pip_path(seek=True), *_pipcmds['info']]
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
        cmds = [self.pip_path(seek=True), *_pipcmds['list']]
        result, retcode = _execute_cmd(cmds, tips, no_output, no_tips, timeout)
        if retcode or not result:
            return info_list
        pkgs = result.strip().split('\n')[2:]
        for pkg in pkgs:
            pkg = pkg.split(' ')
            info_list.append((pkg[0], pkg[-1]))
        return info_list

    def pkgs_name(self, *, no_output=True, no_tips=True, timeout=None):
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
        cmds = [self.pip_path(seek=True), *_pipcmds['list']]
        result, retcode = _execute_cmd(cmds, tips, no_output, no_tips, timeout)
        if retcode or not result:
            return name_list
        pkgs = result.strip().split('\n')[2:]
        for pkg in pkgs:
            pkg = pkg.split(' ')
            name_list.append(pkg[0])
        return name_list

    def outdated(self, *, no_output=True, no_tips=True, timeout=30):
        '''
        获取可更新的包列表，列表包含(包名, 已安装版本, 最新版本, 安装包类型)元组。
        如果没有获取到或者没有可更新的包，返回空列表。
        因为检查更新源为国外服务器，环境中已安装的包越多耗费时间越多，请耐心等待。
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 命令执行超时时长，单位为秒，可设置为None。
        :返回值: lsit[tuple[str, str, str, str]] or lsit[],
        包含(包名, 已安装版本, 最新版本, 安装包类型)的列表或空列表。
        '''
        self._check_timeout(timeout)
        cmds = [self.pip_path(seek=True), *_pipcmds['outdated']]
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
        self, *, mirror='', no_output=True, no_tips=True, timeout=None,
    ):
        '''
        升级pip自己。
        :参数 mirror: str, 镜像源地址，可为空字符串，默认使用系统内设置的全局镜像源。
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 命令执行超时时长，单位为秒，可设置为None。
        :返回值: int, 命令退出状态码，0表示正常结束，负数表示执行被中断，正数表示执行
        异常退出。
        '''
        self._check_timeout(timeout)
        tips = '正在升级pip'
        cmds = [self.pip_path(seek=True), *_pipcmds['update_pip']]
        if mirror:
            cmds.extend(('-i', mirror))
        return _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1]

    def set_mirror(self, *, mirror=mirrors['opentuna']):
        '''
        设置pip全局镜像源地址。
        :参数 mirror: str, 镜像源地址，参数可省略。
        :返回值: int, 命令退出状态码，0表示正常结束，负数表示执行被中断，正数表示执行
        异常退出。
        '''
        if not isinstance(mirror, str):
            raise 参数数据类型异常('镜像源地址参数的数据类型应为字符串。')
        cmds = [self.pip_path(seek=True), *_pipcmds['set_mirror'], mirror]
        return _execute_cmd(
            cmds, tips='', no_output=True, no_tips=True, timeout=None
        )[1]

    def get_mirror(self):
        '''
        获取pip当前镜像源地址。
        :返回值: str, 当前系统pip全局镜像源地址。
        '''
        cmds = [self.pip_path(seek=True), *_pipcmds['get_mirror']]
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
        mirror='',
        update=False,
        no_output=True,
        no_tips=True,
        timeout=None,
    ):
        '''
        安装Python第三方包。
        包名name必须提供，其他参数可以省略，但除了name参数，其他需要指定的参数需以关键
        字参数方式指定。
        :参数 name: str, 第三方包名。
        :参数 mirror: str, 镜像源地址。
        :参数 update: bool, 是否以升级模式安装（如果之前已安装该包，则以升级模式安
        装会卸载旧版本安装新版本，反之会跳过安装，不会安装新版本）
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 任务超时时长，单位为秒，可设为None。
        :返回值: tuple[str, int], 返回(包名, 退出状态码)元组，状态码不为0则表示安装失败。
        '''
        if not isinstance(name, str):
            raise 参数数据类型异常('包名参数的数据类型应为字符串。')
        if not isinstance(mirror, str):
            raise 参数数据类型异常('镜像源地址参数数据类型应为字符串。')
        self._check_timeout(timeout)
        tips = '正在安装{}'.format(name)
        cmds = [self.pip_path(seek=True), *_pipcmds['install'], name]
        if mirror:
            cmds.extend(('-i', mirror))
        if update:
            cmds.append('-U')
        _, retcode = _execute_cmd(cmds, tips, no_output, no_tips, timeout)
        return name, retcode

    def uninstall(self, name, *, no_output=True, no_tips=True, timeout=None):
        '''
        卸载Python第三方包。
        :参数 name: str, 第三方包名。
        :参数 no_output: bool, 是否在终端上显示命令输出（使用GUI时请将此参数设置为
        False）。
        :参数 no_tips: bool, 是否在终端上显示等待提示信息（使用GUI时请将此参数设置为
        False）。
        :参数 timeout: int or float, 任务超时时长，单位为秒，可设为None。
        :返回值: tuple[str, int], 返回(包名, 退出状态码)元组，状态码不为0则表示卸载失败。
        '''
        if not isinstance(name, str):
            raise 参数数据类型异常('包名参数的数据类型应为"str"。')
        self._check_timeout(timeout)
        tips = '正在卸载{}'.format(name)
        cmds = [self.pip_path(seek=True), *_pipcmds['uninstall'], name]
        _, retcode = _execute_cmd(cmds, tips, no_output, no_tips, timeout)
        return name, retcode

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
            raise 参数数据类型异常('搜索关键字的数据类型应为包含str的tuple、lsit或set。')
        if not all(isinstance(s, str) for s in keywords):
            raise 参数数据类型异常('搜索关键字的数据类型应为包含str的tuple、lsit或set。')
        self._check_timeout(timeout)
        search_results, tips = [], '正在搜索{}'.format('、'.join(keywords))
        cmds = [self.pip_path(seek=True), *_pipcmds['search'], *keywords]
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
