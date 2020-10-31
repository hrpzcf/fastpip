### 如何安装

------

从pypi安装：

```
pip install -U fastpip
```



从Gitee安装最新开发版本（推荐）：

1.首先安装依赖模块psutil:

```
pip install psutil
```

2.再安装fastpip:

```
pip install -U git+https://gitee.com/hrpzcf/fastpip@dev
```

fastpip 0.2.0版本与0.1.0及以下版本api不兼容，以下示例仅适用于0.2.0及以上版本，所以推荐安装最新开发版本。



### 如何使用

------

使用fastpip升级Python环境中的包示例（fastpip 0.2.0 或更新版本）：

```python
# -*- coding: utf-8 -*-

import sys

# 用星号通配符导入全部（不推荐）
# 使用星号通配符导入的内容包括：
# 国内PyPi镜像源字典index_urls、PyEnv类, all_py_paths函数, cur_py_path函数
# 各类自定义异常：文件查找异常, 参数值异常, 数据类型异常, 目录查找异常, 适用平台异常
# 没错异常名就是中文的，有点浮夸
# from fastpip import *

# 如果有需要，也可以导入：
# 预设国内镜像源地址字典index_urls（包含七个国内PyPi镜像源）、
# 获取当前系统环境变量PATH第一个Python目录函数cur_py_path、
# 自动查找所有Python目录函数all_py_paths等。
from fastpip import PyEnv

# 生成一个PyEnv类实例
# 初始化参数原型是PyEnv(path)
# 初始化参数path是一个指向Python解释器（python.exe）所在目录的路径
# 例如 target_env = PyEnv(r'C:\Anaconda3\envs\py35')
# 初始化path为空字符串（即''）或省略，则自动查找Python目录
# 自动查找调用函数顺序：cur_py_path > all_py_paths[0]，仍然找不到则抛出异常
target_env = PyEnv()

# 调用PyEnv类实例的outdated方法获取可更新列表
# 参数no_output控制是否在终端显示pip命令输出，这里设置为False表示输出
# 参数no_tips控制是否在终端显示类似"正在..."的提示，这里设为False表示显示提示
# 如果在GUI程序中使用fastpip请确保这两个参数都设置为True
# outdated返回值结构：
# [
# (包名, 已安装版本, 最新版本, 安装包类型),
# ...
# ]
outdated_pkgs = target_env.outdated(no_output=0, no_tips=0)

# 如果可更新列表为空则退出
if not outdated_pkgs:
    print('没有发现可以更新的包。')
    sys.exit(0)

# 询问是否安装所有可更新的包，回答非y则退出
if input('\n确认更新？y/n：').lower() != 'y':
    sys.exit(0)

# 可更新列表不为空则按可更新的包名循环安装
for name, *_ in outdated_pkgs:
    # 调用操作对象的install方法进行安装，安装模式upgrade（升级模式）参数设为True
    target_env.install(name, upgrade=1, no_tips=0)

print('全部更新完成！')

```

