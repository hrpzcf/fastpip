# coding: utf-8

import os
import sys

# 适应某些编辑器、IDE 的模块查找路径问题
sys.path = [os.path.dirname(sys.path[0])] + sys.path

# 导入 PyEnv 类
from fastpip import PyEnv

# 创建 PyEnv 实例：PyEnv(_path)
# 参数 _path 是一个路径，指向 Python 解释器（python.exe）所在目录
# 例如 env = PyEnv(r'C:\Anaconda3\envs\py35')

# 不带参数或者 PyEnv(None) 则使用系统环境变量 PATH 中第一个 Py 环境路径
env = PyEnv()

# 调用 PyEnv 类实例的 outdated 方法获取可更新的包列表
# 参数 output 控制是否在终端显示 pip 命令输出
# 如果在 GUI 程序中使用 fastpip 请将这个参数设置为 False（默认）
# outdated 返回值结构：
# [
# (包名, 已安装版本, 最新版本, 安装包类型),
# ...
# ]
outdated_pkgs = env.outdated(output=True)

# 询问是否安装所有可更新的包，回答非 y 则退出
if input("\n确认更新？y/[n]：").lower() != "y":
    sys.exit(0)

for name, *_ in outdated_pkgs:
    # 调用目标环境的 PyEnv 实例的 install 方法进行安装。
    # upgrade 参数为 True：
    # 以升级模式安装，如果目标环境已安装该包且该包有新版本，则安装新版本，否则跳过。
    # upgrade 参数为 False：
    # 如果目标环境已安装，不管该包有没有新版本都不会重新安装，直接跳过。
    env.install(name, upgrade=True, output=True)

print("全部更新完成！")
