# fastpip

## 简介

------

一个 pip 命令包，帮助你实现使用 Python 编程的方式进行包管理操作。

<br />

## 如何安装

------

`注：fastpip 仅支持 Windows 系统。`

<br />

> 打开命令窗口或 PowerShell 窗口，使用 pip 命令安装：

```cmd
pip install -U fastpip
```

<br /><br />

## 如何使用

------

示例1：使用 fastpip 升级 Python 环境中的包

```python
import sys

# 导入 PyEnv 类
from fastpip import PyEnv

# 创建 PyEnv 实例：PyEnv(_path)
# 参数 _path 是一个路径，指向 Python 解释器(python.exe)所在目录
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
outdated_pkgs = env.outdated(output=1)

# 询问是否安装所有可更新的包，回答非 y 则退出
if input('\n确认更新？y/[n]：').lower() != 'y':
    sys.exit(0)

for name, *_ in outdated_pkgs:
    # 调用目标环境的 PyEnv 实例的 install 方法进行安装。
    # upgrade 参数为 True：
    # 以升级模式安装，如果目标环境已安装该包且该包有新版本，则安装新版本，否则跳过。
    # upgrade 参数为 False：
    # 如果目标环境已安装，不管该包有没有新版本都不会重新安装，直接跳过。
    env.install(name, upgrade=1, output=1)

print('全部更新完成！')

```

示例2：
```python
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
target = PyEnv('C:\\Python37\\')
# target = PyEnv() 与上面一行代码效果是一样的，省略参数时 PyEnv 内部会调用 cur_py_path 函数获取系统环境变量 PATH 中第一个 Python 目录路径，如果 Python 路径还未设置到 PATH 中，则创建一个不指向任何 Python 目录路径的 PyEnv 空实例，实例的所有方法被调用时都将返回空值(不同的方法返回的数据类型也不同，但都是可以判为 False 的空值，例如空列表、空字符串)

# 在该环境中安装模块(例如安装 fastpip)：
print(target.install('fastpip', upgrade=1))
# 安装成功返回 True，否则返回 False。
# upgrade=1 代表以升级模式安装最新版本，否则如果环境中已安装 fastpip，install 方法将不会再安装一次 fastpip。
# 如果有需要，也可以增加以下关键字参数：
# index_url：str，例如 index_url='https://mirrors.cloud.tencent.com/pypi/simple'。本次安装从镜像地址 index_url 处下载安装，否则从本地设置的全局镜像源地址安装，如果本地未设置全局镜像源地址，则从官方源 PyPi 安装，国内用户下载速度非常慢甚至可能因连接超时导致安装失败。
# timeout：int 或 float 或 None，例如 timeout=30，表示设置安装超时限制30秒，如果安装用时超过30秒，则安装失败。None 代表不设超时限制(默认)。
# output：bool，例如 output=True，表示在安装过程中，在终端上打印安装时的输出信息。
```

更多使用方法请查看源代码或者用 help：

```python
import fastpip

help(fastpip)
```

------

<br />

## 贡献

感谢 liangzai450 的贡献！
