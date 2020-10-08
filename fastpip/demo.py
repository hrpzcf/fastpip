# -*- coding: utf-8 -*-

# 导入全部函数（包含国内镜像源字典mirrors）
from fastpip import *

# 获取可更新列表，无运行提示no_tips设为False
outdated = outdated(no_tips=0)

# 如果可更新列表为空就退出
if not outdated:
    print('没有可以更新的包。')
    exit(0)

# 可更新列表不为空就按可更新的包名循环安装
for name, *_ in outdated:
    # 调用install函数安装，升级模式update参数设为True
    install(name, update=1, no_tips=0)

print('全部更新完成！')
