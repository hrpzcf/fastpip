# coding: utf-8

from fastpip import PyEnv, all_py_paths, cur_py_path, index_urls

# 打印预置的几个国内 PyPi 镜像地址：
print(index_urls)
# {'aliyun': 'https://mirrors.aliyun.com/pypi/simple/',
# 'tencent': 'https://mirrors.cloud.tencent.com/pypi/simple',
# 'douban': 'https://pypi.doubanio.com/simple/',
# 'huawei': 'https://mirrors.huaweicloud.com/repository/pypi/simple',
# 'opentuna': 'https://opentuna.cn/pypi/web/simple',
# 'tsinghua': 'https://pypi.tuna.tsinghua.edu.cn/simple',
# 'netease': 'https://mirrors.163.com/pypi/simple/'}

# 当前系统环境变量 PATH 中第一个 Python 环境路径：
print(cur_py_path())
# C:\Python37\ (具体与个人系统环境变量 PATH 设置有关)

# 在常用安装位置查找 Python 目录：
print(all_py_paths())
# ['C:\\Python37\\',
# 'C:\\Anaconda3\\',
# 'C:\\Anaconda3\\envs\\py35\\',
# 'C:\\Anaconda3\\envs\\py36\\',
# 'C:\\Anaconda3\\envs\\py37\\',
# 'C:\\Anaconda3\\envs\\py38\\',
# 'C:\\Anaconda3\\envs\\py39\\']

# PyEnv 类：
##########
# 实例化一个 PyEnv 类：
target = PyEnv("C:\\Python37\\")
# target = PyEnv() 与上面一行代码效果是一样的，省略参数时 PyEnv 内部会调用 cur_py_path 函数获取系统环境变量 PATH 中第一个 Python 目录路径，如果 Python 路径还未设置到 PATH 中，则创建一个不指向任何 Python 目录路径的 PyEnv 空实例，实例的所有方法被调用时都将返回空值(不同的方法返回的数据类型也不同，但都是可以判为 False 的空值，例如空列表、空字符串)

# 在该环境中安装模块(例如安装 fastpip)：
print(target.install("fastpip", upgrade=True))
# 安装成功返回 True，否则返回 False。
# upgrade=1 代表以升级模式安装最新版本，否则如果环境中已安装 fastpip，install 方法将不会再安装一次 fastpip。
# 如果有需要，也可以增加以下关键字参数：
# index_url：str，例如 index_url='https://mirrors.cloud.tencent.com/pypi/simple'。本次安装从镜像地址 index_url 处下载安装，否则从本地设置的全局镜像源地址安装，如果本地未设置全局镜像源地址，则从官方源 PyPi 安装，国内用户下载速度非常慢甚至可能因连接超时导致安装失败。
# timeout：int 或 float 或 None，例如 timeout=30，表示设置安装超时限制30秒，如果安装用时超过30秒，则安装失败。None 代表不设超时限制(默认)。
# output：bool，例如 output=True，表示在安装过程中，在终端上打印安装时的输出信息。

# 待续...
