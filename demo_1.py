# -*- coding: utf-8 -*-

import sys

# 导入 PyEnv 类
from fastpip import PyEnv


# 创建PyEnv实例：PyEnv(_path)
# 参数_path是一个路径，指向Python解释器(python.exe)所在目录
# 例如 env = PyEnv(r'C:\Anaconda3\envs\py35')

env = PyEnv()  # 不带参数或者PyEnv(None)则使用系统环境变量PATH中第一个Py路径


# 调用PyEnv类实例的outdated方法获取可更新的包列表
# 参数no_output控制是否在终端显示pip命令输出，这里为False表示输出
# 参数no_tips控制是否在终端显示类似"正在xxx..."的提示，这里为False表示显示提示
# 如果在GUI程序中使用fastpip请将这两个参数都设置为True（默认值）
# outdated返回值结构：
# [
# (包名, 已安装版本, 最新版本, 安装包类型),
# ...
# ]
outdated_pkgs = env.outdated(no_output=0, no_tips=0)

# 询问是否安装所有可更新的包，回答非y则退出
if input("\n确认更新？y/[n]：").lower() != "y":
    sys.exit(0)

for name, *_ in outdated_pkgs:
    # 调用目标环境的PyEnv实例的install方法进行安装。
    # upgrade参数为True：
    # 以升级模式安装，如果目标环境已安装该包且该包有新版本，则安装新版本，否则跳过。
    # upgrade参数为False：
    # 如果目标环境已安装，不管该包有没有新版本都不会重新安装，直接跳过。
    env.install(name, upgrade=1, no_tips=0)

print("全部更新完成！")
