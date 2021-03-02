# coding: utf-8

################################################################################
# MIT License

# Copyright (c) 2020 hrp/hrpzcf <hrpzcf@foxmail.com>

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
# Formatted with black 20.8b1.
################################################################################

import os
import re
import sys
from subprocess import (
    PIPE,
    STARTF_USESHOWWINDOW,
    STARTUPINFO,
    STDOUT,
    SW_HIDE,
    Popen,
)
from threading import Thread
from time import sleep

from .versions import VERSION
from .errors import *
from .findpath import all_py_paths, cur_py_path

if os.name != 'nt':
    raise UnsupportedPlatform('运行在不支持的平台上。')

_SHOW_RUNNING_TIPS = True
_STARTUP = STARTUPINFO()
_STARTUP.dwFlags = STARTF_USESHOWWINDOW
_STARTUP.wShowWindow = SW_HIDE

# 预设镜像源：
index_urls = {
    'aliyun': 'https://mirrors.aliyun.com/pypi/simple/',  # 阿里源
    'tencent': 'https://mirrors.cloud.tencent.com/pypi/simple',  # 腾讯源
    'douban': 'https://pypi.doubanio.com/simple/',  # 豆瓣源
    'opentuna': 'https://opentuna.cn/pypi/web/simple',  # 清华源
    'tsinghua': 'https://pypi.tuna.tsinghua.edu.cn/simple',  # 清华源
    'huawei': 'https://mirrors.huaweicloud.com/repository/pypi/simple',  # 华为源
    'netease': 'https://mirrors.163.com/pypi/simple/',  # 网易源
    'pypi': 'https://pypi.org/simple/',  # 官方源
}

# 部分pip命令
_PREFIX = ('-m', 'pip')
_PIPCMDS = {
    'INSTALL': (*_PREFIX, 'install'),
    'UNINSTALL': (*_PREFIX, 'uninstall', '-y'),
    'LIST': (*_PREFIX, 'list'),
    'INFO': (*_PREFIX, '-V'),
    'OUTDATED': (*_PREFIX, 'list', '--outdated'),
    'PIPUP': (*_PREFIX, 'install', '-U', 'pip'),
    'SETINDEX': (*_PREFIX, 'config', 'set', 'global.index-url'),
    'GETINDEX': (*_PREFIX, 'config', 'list'),
}


class PipInformation:
    """PipInformation类仅供内部使用。"""

    def __init__(self, pipver, path, pyver):
        self.__path = path
        self.__pyver = pyver
        self.__pipver = pipver

    def __str__(self):
        return 'pip_info(pipver={}, path={}, pyver={})'.format(
            self.__pipver, self.__path, self.__pyver
        )

    __repr__ = __str__

    @property
    def path(self):
        return self.__path

    @property
    def pyver(self):
        return self.__pyver

    @property
    def pipver(self):
        return self.__pipver


def _tips_and_wait(tips):
    """打印等待中提示信息，返回线程实例。"""

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
    """执行命令，输出等待提示语、输出命令执行结果并返回。"""
    global _SHOW_RUNNING_TIPS
    if not no_tips:
        tips_thread = _tips_and_wait(tips)
    try:
        process = Popen(
            cmds,
            stdout=PIPE,
            stderr=STDOUT,
            universal_newlines=True,
            startupinfo=_STARTUP,
        )
        out_put = process.communicate(timeout=timeout)[0]
        return_code = process.returncode
    except Exception:
        out_put, return_code = '', 1
    if not no_tips:
        _SHOW_RUNNING_TIPS = False
        tips_thread.join()
    if not no_output:
        print(out_put, end='')
    return out_put, return_code


class PyEnv:
    """
    Python环境类。
    此类实例的绝大多数方法效果都将作用于该实例所指的Python环境，不对其他环境产生影响。
    只有一个例外：使用set_global_index方法设置本机pip全局镜像源地址，对所有环境产生作用。
    """

    cur_d = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, path=None):
        """
        PyEnv类初始化方法。
        :param path: str or None, 一个指向Python解释器所在目录的路径。
        PyEnv类无参数实例化时或参数值为None实例化时，使用cur_py_path函数选取系统环境变量PATH中的首个Python目录路径，-
        如果系统环境变量PATH中没有找到Python目录路径，则将路径属性env_path设置为空字符串。
        PyEnv类有参数实例化时，如果参数path数据类型不是"str"或"None"则抛出PathParamError异常。
        """
        self.__env_path = self.__init_path(path)

    @staticmethod
    def __init_path(_path):
        """
        初始化Python路径。
        如果路径参数不是字符串，则抛出PathParamError异常。
        该异常可从fastpip.errors模块导入。
        """
        if isinstance(_path, str):
            return os.path.normpath(_path)
        if _path is None:
            return cur_py_path()
        raise PathParamError('路径参数类型错误。')

    @property
    def path(self):
        """
        代表PyEnv类实例化时所传入的Python环境的绝对路径。
        可重新赋值一个路径(字符串)以改变PyEnv类实例所指的Python环境。
        赋值类型非str则抛出PathParamError异常，该异常可从fastpip.errors模块导入。
        """
        return os.path.abspath(self.__env_path)

    @path.setter
    def path(self, _path):
        if not isinstance(_path, str):
            raise PathParamError('路径参数类型错误。')
        self.__env_path = os.path.normpath(_path)

    @property
    def env_path(self):
        """
        代表该Python环境目录路径的属性，该属性在获取的时候进行实时检查。
        当PyEnv实例所指的Python环境无效(例如环境被卸载)时该属性值是空字符串，
        当环境恢复有效后，该属性值是该实例所指Python环境的路径(字符串)。
        """
        return self.__check(self.__env_path)

    @property
    def interpreter(self):
        """
        代表当前环境的Python解释器(python.exe)路径的属性。
        PyEnv实例所指Python环境无效(例如环境被卸载)时值是空字符串。
        """
        env_path = self.env_path
        if not env_path:
            return ''
        return os.path.join(env_path, 'python.exe')

    def __str__(self):
        location = self.env_path or 'unknown location'
        return '{} @ {}'.format(self.py_info(), location)

    @property
    def pip_ready(self):
        """
        代表该Python环境中pip是否已安装的属性。
        值为True代表pip已安装，False代表未安装。
        """
        env_path = self.env_path
        if not env_path:
            return False
        return os.path.isfile(
            os.path.join(
                env_path, 'Lib', 'site-packages', 'pip', '__init__.py'
            )
        )

    @staticmethod
    def __check(_path):
        """检查参数path在当前是否是一个有效的Python目录路径。"""
        if not os.path.isfile(os.path.join(_path, 'python.exe')):
            return ''
        return os.path.normpath(_path)

    @staticmethod
    def __check_timeout_num(timeout):
        if isinstance(timeout, (int, float)):
            if timeout < 1:
                raise ParamValueError('超时参数timeout的值不能小于1。')
            return True
        if timeout is None:
            return True
        raise ParamTypeError('参数timeout值应为None、整数或浮点数。')

    def py_info(self):
        """获取当前环境Python版本信息。"""
        info = 'Python {} :: {} bit'
        if not self.env_path:
            return info.format('0.0.0', '?')
        source_code = 'import sys;print(sys.version)'
        _path = os.path.join(self.cur_d, f'ReadPyVER.{VERSION}')
        if not os.path.isfile(_path):
            if not os.path.exists(self.cur_d):
                try:
                    os.makedirs(self.cur_d)
                except Exception:
                    return info.format('0.0.0', '?')
            try:
                with open(_path, 'wt', encoding='utf-8') as py_file:
                    py_file.write(source_code)
            except Exception:
                return info.format('0.0.0', '?')
        result, retcode = _execute_cmd(
            (self.interpreter, _path), '', True, True, None
        )
        if retcode or not result:
            return info.format('0.0.0', '?')
        m_obj = re.match(
            r'(\d+\.\d+\.\d+) (?:\(|\|).+(32|64) bit \(.+\)', result
        )
        if not m_obj:
            return info.format('0.0.0', '?')
        return info.format(*m_obj.groups())

    def pip_path(self):
        """
        根据env_path属性所指的Python安装目录获取pip可执行文件路径。
        如果Scripts目录不存在或无法打开则返回空字符串。
        如果在Scripts目录中没有找到pip可执行文件则返回空字符串。
        :return: str, 该PyEnv实例所指Python环境的pip可执行文件的完整路径或空字符。
        """
        env_path = self.env_path
        if not env_path:
            return ''
        dir_pip_exists = os.path.join(env_path, 'Scripts')
        try:
            dirs_and_files = os.listdir(dir_pip_exists)
        except Exception:
            return ''
        for dir_or_file in dirs_and_files:
            if not os.path.isfile(os.path.join(dir_pip_exists, dir_or_file)):
                continue
            match_obj = re.match(r'^pip.*\.exe$', dir_or_file)
            if not match_obj:
                continue
            return os.path.join(dir_pip_exists, match_obj.group())
        return ''

    def pip_info(self):
        """
        获取该目录的pip版本信息。
        如果获取到pip版本信息，则返回一个PipInformation实例，
        可以通过访问实例的pipver、path、pyver属性分别获取到pip版本号、pip目录路径、该pip所在的Python环境版本号；
        如果没有获取到pip信息或获取到信息但未正确匹配到信息格式，则返回None。
        直接打印PipInfo实例则显示概览：pip_info(pip版本、pip路径、相应Python版本)。
        :return: 匹配到pip版本信息：PipInformation实例；未获取到pip版本信息：返回None。
        """
        if not self.pip_ready:
            return
        cmds = [self.interpreter, *_PIPCMDS['INFO']]
        result, retcode = _execute_cmd(
            cmds, tips='', no_output=True, no_tips=True, timeout=None
        )
        if retcode or not result:
            return
        match_obj = re.match(
            'pip (.+) from (.+) \(python (.+)\)', result.strip()
        )
        if not match_obj:
            return
        res = match_obj.groups()
        if not (len(res) == 3):
            return
        return PipInformation(*res)

    @staticmethod
    def __clean_info(string):
        """清理pip包名列表命令的无关输出。"""
        preprocessed = re.search(
            r'Package\s+Version\s*\n[-\s]+\n(.+)', string, re.S
        )
        if not preprocessed:
            return []
        return re.findall(r'^(\S+)\s+(\S+)\s*$', preprocessed.group(1), re.M)

    def pkgs_info(self, *, no_output=True, no_tips=True, timeout=None):
        """
        获取该Python目录下已安装的包列表，列表包含(包名, 版本)元组，没有获取到则返回空列表。
        :param no_output: bool, 是否不在终端上显示命令输出，默认True(使用GUI时请确保此参数值为True)。
        :param no_tips: bool, 是否不在终端上显示等待提示信息，默认True(使用GUI时请确保此参数值为True)。
        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None表示无限制，默认为None。
        :return: lsit[tuple[str, str]] or list[], 包含(第三方包名, 版本)元组的列表或空列表。
        timeout参数值小于1则抛出ParamValueError异常，该异常可从fastpip.errors模块导入。
        timeout参数数据类型不是int或float或None则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        """
        if not self.pip_ready:
            return []
        self.__check_timeout_num(timeout)
        cmds = [self.interpreter, *_PIPCMDS['LIST']]
        result, retcode = _execute_cmd(
            cmds, '正在获取(包名, 版本)列表', no_output, no_tips, timeout
        )
        if retcode or not result:
            return []
        return self.__clean_info(result)

    def pkg_names(self, *, no_output=True, no_tips=True, timeout=None):
        """
        获取该Python目录下已安装的包名列表，没有获取到包名列表则返回空列表。
        :param no_output: bool, 是否不在终端上显示命令输出，默认True(使用GUI时请确保此参数值为True)。
        :param no_tips: bool, 是否不在终端上显示等待提示信息，默认True(使用GUI时请确保此参数值为True)。
        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None表示无限制，默认为None。
        :return: list[str...] or lsit[], 包含包名的列表或空列表。
        timeout参数值小于1则抛出ParamValueError异常，该异常可从fastpip.errors模块导入。
        timeout参数数据类型不是int或float或None则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        """
        if not self.pip_ready:
            return []
        self.__check_timeout_num(timeout)
        cmds = [self.interpreter, *_PIPCMDS['LIST']]
        result, retcode = _execute_cmd(
            cmds, '正在获取包名列表', no_output, no_tips, timeout
        )
        if retcode or not result:
            return []
        return [n for n, _ in self.__clean_info(result)]

    def outdated(self, *, no_output=True, no_tips=True, timeout=30):
        """
        获取可更新的包列表，列表包含(包名, 已安装版本, 最新版本, 安装包类型)元组。
        如果没有获取到或者没有可更新的包，返回空列表。
        检查更新时，环境中已安装的包越多耗费时间越多，请耐心等待。
        :param no_output: bool, 是否不在终端上显示命令输出，默认True(使用GUI时请确保此参数值为True)。
        :param no_tips: bool, 是否不在终端上显示等待提示信息，默认True(使用GUI时请确保此参数值为True)。
        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None表示无限制，默认为None。
        :return: lsit[tuple[str, str, str, str]] or lsit[]，包含(包名, 已安装版本, 最新版本, 安装包类型)的列表或空列表。
        timeout参数值小于1则抛出ParamValueError异常，该异常可从fastpip.errors模块导入。
        timeout参数数据类型不是int或float或None则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        """
        if not self.pip_ready:
            return []
        self.__check_timeout_num(timeout)
        cmds = [self.interpreter, *_PIPCMDS['OUTDATED']]
        outdated_pkgs_info = []
        result, retcode = _execute_cmd(
            cmds, '正在检查更新', no_output, no_tips, timeout
        )
        if retcode or not result:
            return outdated_pkgs_info
        result = result.strip().split('\n')
        pt1 = r'^(\S+)\s+(\S+)\s+(\S+)\s+(sdist|wheel)$'
        pt2 = r'^(\S+) \((\S+)\) - Latest: (\S+) \[(sdist|wheel)\]$'
        for pkg_ver_info in result:
            res = re.match(pt1, pkg_ver_info)
            if res:
                outdated_pkgs_info.append(res.groups())
        if not outdated_pkgs_info:
            for pkg_ver_info in result:
                res = re.match(pt2, pkg_ver_info)
                if res:
                    outdated_pkgs_info.append(res.groups())
        return outdated_pkgs_info

    def upgrade_pip(
        self,
        *,
        index_url='',
        no_output=True,
        no_tips=True,
        timeout=None,
    ):
        """
        升级pip自身。
        :param index_url: str, 镜像源地址，可为空字符串，默认使用系统内设置的全局镜像源。
        :param no_output: bool, 是否不在终端上显示命令输出，默认True(使用GUI时请确保此参数值为True)。
        :param no_tips: bool, 是否不在终端上显示等待提示信息，默认True(使用GUI时请确保此参数值为True)。
        :param timeout: int or float, 命令执行超时时长，单位为秒，可设置为None表示无限制，默认为None。
        :return: tuple[tuple['pip'], bool], 返回(('pip',), 退出状态)元组，退出状态为True表示升级成功，False表示失败。
        timeout参数值小于1则抛出ParamValueError异常，该异常可从fastpip.errors模块导入。
        timeout参数数据类型不是int或float或None则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        """
        if not self.pip_ready:
            return False
        self.__check_timeout_num(timeout)
        cmds = [self.interpreter, *_PIPCMDS['PIPUP']]
        if index_url:
            cmds.extend(('-i', index_url))
        result, retcode = _execute_cmd(
            cmds, '正在升级pip', no_output, no_tips, timeout
        )
        return (('pip',), not retcode)

    def set_global_index(self, index_url=index_urls['opentuna']):
        """
        设置pip全局镜像源地址。
        :param index_url: str, 镜像源地址，参数可省略。
        :return: bool, 退出状态，True表示设置成功，False表示设置失败。
        参数index_url类型不是str则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        """
        if not self.pip_ready or not index_url:
            return False
        if not isinstance(index_url, str):
            raise ParamTypeError('镜像源地址参数的数据类型应为字符串。')
        cmds = [self.interpreter, *_PIPCMDS['SETINDEX'], index_url]
        return not _execute_cmd(
            cmds, tips='', no_output=True, no_tips=True, timeout=None
        )[1]

    def get_global_index(self):
        """
        显示当前pip全局镜像源地址。
        :return: str, 当前系统pip全局镜像源地址。
        """
        if not self.pip_ready:
            return ''
        cmds = [self.interpreter, *_PIPCMDS['GETINDEX']]
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
        """
        安装Python第三方包。
        包名names必须提供，其他参数可以省略，但除了names参数，其他需要指定的参数需以关键字参数方式指定。
        注意：包名names中只要有一个不可安装(无资源等原因)，其他包也不会被安装。
        所以如果不能保证names中所有的包都能被安装，那最好只输入一个包名参数，在外部循环调用install方法安装所有的包。
        :param names: str, 第三方包名(可变数量参数)。
        :param index_url: str, pip镜像源地址。
        :param upgrade: bool, 是否以升级模式安装(如果之前已安装该包，则升级模式会卸载旧版本安装新版本，反之会跳过安装，不安装新版本)
        :param pre: bool, 查找目标是否包括预发行版和开发版，默认为False，即仅查找稳定版。
        :param user: bool, 是否安装到您平台的Python用户安装目录，通常是 ~/.local/或％APPDATA％Python，默认False。
        :param compile: bool or 'auto', 是否将Python源文件编译为字节码，默认'auto'，由pip决定。
        :param no_output: bool, 是否不在终端上显示命令输出，默认True(使用GUI时请确保此参数值为True)。
        :param no_tips: bool, 是否不在终端上显示等待提示信息，默认True(使用GUI时请确保此参数值为True)。
        :param timeout: int or float, 任务超时限制，单位为秒，可设为None表示无限制，默认为None。
        :return: tuple[tuple[str...], bool], 返回((包名...), 退出状态)元组。
        但包名names中只要有一个包不可安装(无资源等原因)，则所有传入的包名都不会被安装，且退出状态为False。
        所有包名中有非str类型数据则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        index_url数据类型非str则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        timeout参数值小于1则抛出ParamValueError异常，该异常可从fastpip.errors模块导入。
        timeout参数数据类型不是int或float或None则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        """
        if not self.pip_ready or not names:
            return tuple()
        install_pre = kwargs.get('pre', False)
        index_url = kwargs.get('index_url', '')
        timeout = kwargs.get('timeout', None)
        upgrade = kwargs.get('upgrade', False)
        no_tips = kwargs.get('no_tips', True)
        no_output = kwargs.get('no_output', True)
        install_user = kwargs.get('user', False)
        compile_sc = kwargs.get('compile', 'auto')
        if not all(isinstance(s, str) for s in names):
            raise ParamTypeError('包名参数的数据类型应为字符串。')
        if not isinstance(index_url, str):
            raise ParamTypeError('镜像源地址参数数据类型应为字符串。')
        self.__check_timeout_num(timeout)
        cmds = [self.interpreter, *_PIPCMDS['INSTALL'], *names]
        if install_pre:
            cmds.append('--pre')
        if upgrade:
            cmds.append('-U')
        if index_url:
            cmds.extend(('-i', index_url))
        if install_user:
            cmds.append('--user')
        if compile_sc == 'auto':
            pass
        elif compile_sc:
            cmds.append('--compile')
        else:
            cmds.append('--no-compile')
        tips = '正在安装{}'.format(', '.join(names))
        return (
            names,
            not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1],
        )

    def uninstall(self, *names, **kwargs):
        """
        卸载Python第三方包。
        注意：如果names中包含未安装的包名则跳过卸载，以下的退出状态仍为True。
        :param names: str, 第三方包名。
        :param no_output: bool, 是否不在终端上显示命令输出，默认True(使用GUI时请确保此参数值为True)。
        :param no_tips: bool, 是否不在终端上显示等待提示信息，默认True(使用GUI时请确保此参数值为True)。
        :param timeout: int or float, 任务超时限制，单位为秒，可设为None表示无限制，默认为None。
        :return: tuple[tuple[str...], bool], 返回((包名...), 退出状态)元组，状态不为True则表示卸载失败。
        所有包名中有非str类型数据则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        timeout参数值小于1则抛出ParamValueError异常，该异常可从fastpip.errors模块导入。
        timeout参数数据类型不是int或float或None则抛出ParamTypeError异常。该异常可从fastpip.errors模块导入。
        """
        if not self.pip_ready or not names:
            return tuple()
        timeout = kwargs.get('timeout', None)
        no_tips = kwargs.get('no_tips', True)
        no_output = kwargs.get('no_output', True)
        if not all(isinstance(s, str) for s in names):
            raise ParamTypeError('包名参数的数据类型应为字符串。')
        self.__check_timeout_num(timeout)
        tips = '正在卸载{}'.format(', '.join(names))
        cmds = [self.interpreter, *_PIPCMDS['UNINSTALL'], *names]
        return (
            names,
            not _execute_cmd(cmds, tips, no_output, no_tips, timeout)[1],
        )

    def imports(self):
        """获取该Python环境下的包、模块的导入名列表。"""
        pkg_import_names = []
        if not self.env_path:
            return pkg_import_names
        sys_paths, builtins = self.__read_sys_path_builtins()
        for sys_path in sys_paths:
            for names in self.__from_sys_path(sys_path).values():
                pkg_import_names.extend(names)
        pkg_import_names.extend(builtins)
        return pkg_import_names

    def query(self, name, *, case=True):
        """
        查询该环境下指定的包、模块对应的用于导入的名称。
        :param name: str, 要查询的包名或模块名。
        :param case: bool, 查询时是否对name大小写敏感。
        :return: list[str...], 该包、模块的导入名列表。
        要查询的包名非str则抛出ParamTypeError异常，该异常可从fastpip.errors模块导入。
        """
        if not isinstance(name, str):
            raise ParamTypeError('参数name数据类型错误，数据类型应为str。')
        sys_paths, builtins = self.__read_sys_path_builtins()
        if not case:
            name = name.lower()
            lbuiltins = [n.lower() for n in builtins]
        if name in lbuiltins:
            return [builtins[lbuiltins.index(name)]]
        for sys_path in sys_paths:
            if case:
                name_dict = self.__from_sys_path(sys_path)
            else:
                name_dict = dict(
                    (k.lower(), v)
                    for k, v in self.__from_sys_path(sys_path).items()
                )
            if name in name_dict:
                return name_dict[name]
        return []

    def __read_sys_path_builtins(self):
        """读取目标Python环境的sys.path和sys.builtin_module_names属性。"""
        if not self.env_path:
            return []
        source_code = '''import sys
print(sys.path[1:], "\\n", sys.builtin_module_names)'''
        _path = os.path.join(self.cur_d, f'ReadSYSPB.{VERSION}')
        if not os.path.isfile(_path):
            if not os.path.exists(self.cur_d):
                try:
                    os.makedirs(self.cur_d)
                except Exception:
                    return [], ()
            try:
                with open(_path, 'wt', encoding='utf-8') as py_file:
                    py_file.write(source_code)
            except Exception:
                return [], ()
        result, retcode = _execute_cmd(
            (self.interpreter, _path), '', True, True, None
        )
        if retcode or not result:
            return [], ()
        try:
            paths, builtins = result.strip().split('\n')
            return eval(paths.strip()), eval(builtins.strip())
        except Exception:
            return [], ()

    @staticmethod
    def __from_sys_path(pkg_dir):
        """从sys.path列表中的一个路径获取可用于导入的模块、包名。"""
        modules_and_pkgs, names_used_for_import = list(), dict()
        try:
            modules_and_pkgs.extend(os.listdir(pkg_dir))
        except Exception:
            return names_used_for_import
        py_modules, py_packages = list(), list()
        pattern_d = re.compile(
            r'^([0-9a-zA-Z_.]+)-.+(?:\.dist-info|\.egg-info)$'
        )
        pattern_t = re.compile(r'^[a-zA-Z_]?[0-9a-zA-Z_]+')
        pattern_f = re.compile(r'^([0-9a-zA-Z_]+).*(?<!_d)\.py[cdw]?$')
        for mod_pkg in modules_and_pkgs:
            _path = os.path.join(pkg_dir, mod_pkg)
            if os.path.isfile(_path):
                py_modules.append(mod_pkg)
            elif os.path.isdir(_path):
                py_packages.append(mod_pkg)
        for package in py_packages:
            try:
                file_list = os.listdir(os.path.join(pkg_dir, package))
            except Exception:
                continue
            if '__init__.py' in file_list:
                if package not in names_used_for_import:
                    # 有__init__.py文件的目录，其导入名即为目录名
                    names_used_for_import[package] = [package]
                continue
            match_object_d = pattern_d.match(package)
            if not match_object_d:
                continue
            top_level = os.path.join(pkg_dir, package, 'top_level.txt')
            if not os.path.isfile(top_level):
                continue
            try:
                with open(top_level, 'rt') as top_level:
                    lines = top_level.readlines()
            except Exception:
                continue
            names_for_import_top_level = list()
            for l in lines:
                m_obj_t = pattern_t.match(os.path.basename(l.strip()))
                if not m_obj_t:
                    continue
                names_for_import_top_level.append(m_obj_t.group())
            pkg_name = match_object_d.group(1)
            if pkg_name not in names_used_for_import:
                names_used_for_import[pkg_name] = names_for_import_top_level
            else:
                names_used_for_import[pkg_name].extend(
                    names_for_import_top_level
                )
        for module in py_modules:
            match_object_f = pattern_f.match(module)
            if not match_object_f:
                continue
            imp_name = match_object_f.group(1)
            # 单文件模块形式下，导入名和剔除后缀后的模块名相同(后缀不仅指扩展名)
            if imp_name in names_used_for_import:
                continue
            names_used_for_import[imp_name] = [imp_name]
        return names_used_for_import

    def download(self, *names, **kwargs):
        ...
