### 如何安装

------

从pypi安装：

```
pip install -U fastpip
```

安装最新开发版本（推荐）：

```
pip install -U git+https://gitee.com/hrpzcf/fastpip@dev
```

fastpip 0.2.0版本与0.1.0及以下版本api不兼容，以下示例仅适用于0.2.0及以上版本，所以推荐安装最新开发版本。



### 如何使用

------

使用fastpip升级Python环境中的包示例（fastpip 0.2.0）：

```python
# -*- coding: utf-8 -*-

import sys

# 用星号通配符导入全部（不推荐）
# 使用星号通配符导入的内容包括：
# 国内PyPi镜像源字典mirrors、PyEnv类, all_py_paths函数, cur_py_path函数
# 各类自定义异常：Pip未找到异常, 参数值异常, 参数数据类型异常, 目录查找异常, 适用平台异常
# 没错异常名就是中文的，有点浮夸
# from fastpip import *

# 如果有需要，也可以导入预设国内镜像源地址字典mirrors（包含七个国内PyPi镜像源）、
# 获取默认操作Python目录路径cur_py_path函数、自动查找Python目录函数all_py_paths等。
from fastpip import PyEnv

# 实例化一个pip操作对象（Python环境）
# 初始化参数原型是PyEnv(path)
# 初始化参数path是一个指向Python解释器（python.exe）所在目录的路径
# 例如 a_py_env = PyEnv(r'C:\Anaconda3\envs\py35')
# 初始化path为空字符串（即''）或省略，则自动查找Python目录，找不到则抛出异常
a_py_env = PyEnv()

# 调用操作对象的outdated方法获取可更新列表
# 参数no_output控制是否在终端显示pip命令输出，这里设置为False表示输出
# 参数no_tips控制是否在终端显示类似"正在..."的提示，这里设为False表示显示提示
# 如果在GUI程序中使用fastpip请确保这两个参数都设置为True
# outdated返回值结构：
# [
# (包名, 已安装版本, 最新版本, 安装包类型),
# ...
# ]
outdated_pkgs = a_py_env.outdated(no_output=0, no_tips=0)

# 如果可更新列表为空则退出
if not outdated_pkgs:
    print('没有发现可以更新的包。')
    sys.exit(0)

# 询问是否安装所有可更新的包，回答非y则退出
if input('\n确认更新？y/n：').lower() != 'y':
    sys.exit(0)

# 可更新列表不为空则按可更新的包名循环安装
for name, *_ in outdated_pkgs:
    # 调用操作对象的install方法进行安装，安装模式update（升级模式）参数设为True
    a_py_env.install(name, update=1, no_tips=0)

print('全部更新完成！')

```
