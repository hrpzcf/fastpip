# -*- coding: utf-8 -*-

import sys

# 导入全部（不推荐）
# from fastpip import *    # 包括国内镜像源字典mirrors、各类自定义异常等

# 如果有需要，可以导入预设国内镜像源地址字典mirrors、
# 获取默认操作Python目录路径cur_py_path函数、自动查找Python目录函数all_py_paths等。
from fastpip import PyEnv

# 实例化一个pip操作对象（Python环境）
# 初始化参数原型是PyEnv(path)
# 初始化参数path是一个指向Python解释器（python.exe）所在目录的路径
# 例如 a_py_env = PyEnv(r'C:\Anaconda3\envs\py35')
# 初始化path为空字符串（即''）或省略，则自动查找Python目录，找不到则抛出异常
a_py_env = PyEnv()

# 调用操作对象的outdated方法获取可更新列表
# "无信息输出"参数no_output设置为False
# "无正在运行提示"参数no_tips设为False
# outdated返回值结构：
# [
# (包名, 已安装版本, 最新版本, 安装包类型).
# ...
# ]
outdated_pkgs = a_py_env.outdated(no_output=0, no_tips=0)

# 如果可更新列表为空就退出
if not outdated_pkgs:
    print('没有发现可以更新的包。')
    sys.exit(0)

# 询问是否安装所有可更新的包，回答不是y就退出
if input('\n确认更新？y/n：').lower() != 'y':
    sys.exit(0)

# 可更新列表不为空则按可更新的包名循环安装
for name, *_ in outdated_pkgs:
    # 调用操作对象的install方法安装，安装模式update（升级）参数设为True
    a_py_env.install(name, update=1, no_tips=0)

print('全部更新完成！')
