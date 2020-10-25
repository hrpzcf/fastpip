import os

from setuptools import find_packages, setup

from fastpip import NAME, VERSION, AUTHOR, EMAIL, WEBSITE

description = '一个对pip命令行操作进行简单封装的模块，可在代码中实现方便的pip命令操作。'
long_description = description

if os.path.exists('README.md'):
    try:
        with open('README.md', 'r', encoding='utf-8') as mdfile:
            long_description = mdfile.read()
    except Exception:
        pass

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
        'Programming Language :: Python :: 3.8',
    ],
    keywords=['pip', 'encapsulation'],
)
