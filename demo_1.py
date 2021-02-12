# -*- coding: utf-8 -*-

import sys

# 导入 PyEnv 类
from fastpip import PyEnv


# 创建一个PyEnv类实例
# 初始化参数原型是PyEnv(python_path)
# 参数python_path是一个指向Python解释器（python.exe）所在目录的路径
# 例如 target_env = PyEnv(r'C:\Anaconda3\envs\py35')
target_env = PyEnv()


# 调用PyEnv类实例的outdated方法获取可更新的模块列表
# 参数no_output控制是否在终端显示pip命令输出，这里设置为False表示输出
# 参数no_tips控制是否在终端显示类似"正在xxx..."的提示，这里设为False表示显示提示
# 如果在GUI程序中使用fastpip请将这两个参数都设置为True（默认）
# outdated返回值结构：
# [
# (包名, 已安装版本, 最新版本, 安装包类型),
# ...
# ]
outdated_pkgs = target_env.outdated(no_output=0, no_tips=0)

# 询问是否安装所有可更新的包，回答非y则退出
if input('\n确认更新？y/n：').lower() != 'y':
    sys.exit(0)

# 可更新列表不为空则按可更新的包名循环安装
for name, *_ in outdated_pkgs:
    # 调用代表目标环境的PyEnv实例的install方法进行安装。
    # 安装模式upgrade参数设为True，则将可升级的包以升级模式安装，否则不安装已安装的包
    target_env.install(name, upgrade=1, no_tips=0)

print('全部更新完成！')
