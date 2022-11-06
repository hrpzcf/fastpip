# coding: utf-8

from glob import glob

from setuptools import find_packages, setup

from fastpip import AUTHOR, NAME, VERSION, WEBSITE

description = "一个 pip 命令包，帮助你实现使用 Python 编程的方式进行包管理操作。"
try:
    with open("README.md", "rt", encoding="utf-8") as mdfile:
        long_description = mdfile.read()
except Exception:
    long_description = description

setup(
    name=NAME,
    version=VERSION,
    description=description,
    author=AUTHOR,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=WEBSITE,
    packages=find_packages(),
    data_files=[
        ("lib/site-packages/fastpip/demo", glob("demo/*")),
        ("lib/site-packages/fastpip/readme", ["README.md", "LICENSE"]),
    ],
    platforms=["win32", "win_amd64"],
    install_requires=["psutil>=5.7.2"],
    python_requires=">=3.7",
    license="MIT License",
    classifiers=[
        "Intended Audience :: Developers",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords=["pip", "package"],
)
