# -*- coding: utf-8 -*-

from fastpip import PyEnv, all_py_paths, cur_py_path, index_urls

# 打印预置的几个国内PyPi镜像地址：
print(index_urls)
# {'aliyun': 'https://mirrors.aliyun.com/pypi/simple/',
# 'tencent': 'https://mirrors.cloud.tencent.com/pypi/simple',
# 'douban': 'https://pypi.doubanio.com/simple/',
# 'huawei': 'https://mirrors.huaweicloud.com/repository/pypi/simple',
# 'opentuna': 'https://opentuna.cn/pypi/web/simple',
# 'tsinghua': 'https://pypi.tuna.tsinghua.edu.cn/simple',
# 'netease': 'https://mirrors.163.com/pypi/simple/'}

# 当前系统环境变量PATH中第一个Python环境路径：
print(cur_py_path())
# C:\Python37\ (具体与个人系统环境变量PATH设置有关)

# 在常用安装位置查找Python目录：
print(all_py_paths())
# ['C:\\Python37\\',
# 'C:\\Anaconda3\\',
# 'C:\\Anaconda3\\envs\\py35\\',
# 'C:\\Anaconda3\\envs\\py36\\',
# 'C:\\Anaconda3\\envs\\py37\\',
# 'C:\\Anaconda3\\envs\\py38\\',
# 'C:\\Anaconda3\\envs\\py39\\']

# PyEnv类：
##########
# 实例化一个PyEnv类：
target = PyEnv("C:\\Python37\\")
# target = PyEnv() 与上面一行代码效果是一样的，省略参数时PyEnv内部会调用cur_py_path函数获取系统环境变量PATH中第一个Python目录路径，如果Python路径还未设置到PATH中，则创建一个不指向任何Python目录路径的PyEnv空实例，实例的所有方法被调用时都将返回空值(不同的方法返回的数据类型也不同，但都是可以判为False的空值，例如空列表、空字符串)

# 在该环境中安装模块(例如安装fastpip)：
print(target.install("fastpip", upgrade=1))
# 安装成功返回True，否则返回False。
# upgrade=1代表以升级模式安装最新版本，否则如果环境中已安装fastpip，install方法将不会再安装一次fastpip。
# 如果有需要，也可以增加以下关键字参数：
# index_url：str，例如index_url='https://mirrors.cloud.tencent.com/pypi/simple'。本次安装从镜像地址index_url处下载安装，否则从本地设置的全局镜像源地址安装，如果本地未设置全局镜像源地址，则从官方源PyPi安装，国内用户下载速度非常慢甚至可能因连接超时导致安装失败。
# timeout：int或float或None，例如timeout=30，表示设置安装超时限制30秒，如果安装用时超过30秒，则安装失败。None代表不设超时限制(默认)。
# no_tips：bool，例如no_tips=0，表示在安装过程中显示'正在安装xxx...'动态字样。
# no_output：bool，例如no_output=0，表示在安装结束后，在终端上输出安装时的安装信息。

# 待续...
