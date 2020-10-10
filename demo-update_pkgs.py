# -*- coding: utf-8 -*-

# 导入全部函数（不推荐）
# from .fastpip import *    # 包含国内镜像源字典mirrors

from fastpip import install, outdated

print('可更新的包：')
# 获取可更新列表
# "无信息输出"参数no_output设置为False
# "无正在运行提示"参数no_tips设为False
# outdated返回值结构：
# [
# (包名, 已安装版本, 最新版本, 安装包类型).
# ...
# ]
outdated_pkgs = outdated(no_output=0, no_tips=0)

# 如果可更新列表为空就退出
if not outdated_pkgs:
    print('没有发现可以更新的包。')
    exit(0)

# 询问是否安装所有可更新的包，回答不是y就退出
if input('\n确认更新？y/n：').lower() != 'y':
    exit(0)

# 可更新列表不为空则按可更新的包名循环安装
for name, *_ in outdated_pkgs:
    # 调用install函数安装，安装模式update（升级）参数设为True
    install(name, update=1, no_tips=0)

print('全部更新完成！')
