# coding: utf-8

import os

from setuptools import find_packages, setup

from fastpip import AUTHOR, NAME, VERSION, WEBSITE

desc = "一个 pip 命令包，帮助你实现使用 Python 编程的方式进行包管理操作。"
try:
    with open("README.md", "rt", encoding="utf-8") as mdfile:
        long_description = mdfile.read()
except Exception:
    long_description = desc
req_file = "requirements.txt"
assert os.path.isfile(req_file), "'requirements.txt' does not exist!"
with open(req_file, "rt", encoding="utf-8") as rf:
    install_requires = [s.strip() for s in rf if s]

setup(
    name=NAME,
    version=VERSION,
    description=desc,
    author=AUTHOR,
    url=WEBSITE,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    platforms=["win32", "win_amd64"],
    install_requires=install_requires,
    python_requires=">=3.7",
    license="MIT License",
    keywords=["pip", "package"],
    package_data={"": ["LICENSE"]},
    classifiers=[
        "Intended Audience :: Developers",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
