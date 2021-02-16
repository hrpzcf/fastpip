# coding: utf-8

from setuptools import find_packages, setup
from fastpip import AUTHOR, EMAIL, NAME, VERSION, WEBSITE

description = '一个pip命令包，可在Python3源代码中实现方便的包管理操作。'

try:
    with open('README.md', 'r', encoding='utf-8') as mdfile:
        long_description = mdfile.read()
except Exception:
    long_description = description

setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    author_email=EMAIL,
    maintainer=AUTHOR,
    maintainer_email=EMAIL,
    url=WEBSITE,
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT License',
    packages=find_packages(),
    platforms=['win32', 'win_amd64'],
    install_requires=['psutil>=5.7.2'],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.7',
    ],
    keywords=['pip', 'package'],
)
