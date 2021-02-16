# fastpip
`fastpip目前处于Beta阶段，版本升级可能会有不经通知的接口增删、参数变动等，也可能有未知的问题。`

<br />

## 如何安装

------

`注：fastpip仅支持Windows平台。`

<br />

> 打开命令窗口或PowerShell窗口，使用 pip 命令安装：

```cmd
py -m pip install -U fastpip
```

<br /><br />

## 如何使用

------

示例1：使用fastpip升级Python环境中的包

```python
# -*- coding: utf-8 -*-

import sys

# 导入 PyEnv 类
from fastpip import PyEnv


# 创建PyEnv实例：PyEnv(_path)
# 参数_path是一个路径，指向Python解释器(python.exe)所在目录
# 例如 env = PyEnv(r'C:\Anaconda3\envs\py35')

env = PyEnv() # 不带参数或者PyEnv(None)则使用系统环境变量PATH中第一个Py路径


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
if input('\n确认更新？y/[n]：').lower() != 'y':
    sys.exit(0)

for name, *_ in outdated_pkgs:
    # 调用目标环境的PyEnv实例的install方法进行安装。
    # upgrade参数为True：
    # 以升级模式安装，如果目标环境已安装该包且该包有新版本，则安装新版本，否则跳过。
    # upgrade参数为False：
    # 如果目标环境已安装，不管该包有没有新版本都不会重新安装，直接跳过。
    env.install(name, upgrade=1, no_tips=0)

print('全部更新完成！')

```

示例2：
```python
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
target = PyEnv('C:\\Python37\\')
# target = PyEnv() 与上面一行代码效果是一样的，省略参数时PyEnv内部会调用cur_py_path函数获取系统环境变量PATH中第一个Python目录路径，如果Python路径还未设置到PATH中，则创建一个不指向任何Python目录路径的PyEnv空实例，实例的所有方法被调用时都将返回空值(不同的方法返回的数据类型也不同，但都是可以判为False的空值，例如空列表、空字符串)

# 在该环境中安装模块(例如安装fastpip)：
print(target.install('fastpip', upgrade=1))
# 安装成功返回True，否则返回False。
# upgrade=1代表以升级模式安装最新版本，否则如果环境中已安装fastpip，install方法将不会再安装一次fastpip。
# 如果有需要，也可以增加以下关键字参数：
# index_url：str，例如index_url='https://mirrors.cloud.tencent.com/pypi/simple'。本次安装从镜像地址index_url处下载安装，否则从本地设置的全局镜像源地址安装，如果本地未设置全局镜像源地址，则从官方源PyPi安装，国内用户下载速度非常慢甚至可能因连接超时导致安装失败。
# timeout：int或float或None，例如timeout=30，表示设置安装超时限制30秒，如果安装用时超过30秒，则安装失败。None代表不设超时限制(默认)。
# no_tips：bool，例如no_tips=0，表示在安装过程中显示'正在安装xxx...'动态字样。
# no_output：bool，例如no_output=0，表示在安装结束后，在终端上输出安装时的安装信息。
```

更多使用方法请查看源代码或者用 help：

```python
import fastpip

help(fastpip)
```
