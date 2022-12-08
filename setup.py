# !/usr/bin/env python
# encoding=utf-8
# author: zhanzq
# email : zhanzhiqiang09@126.com 
# date  : 2022/8/15
#


import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="common_utils",
    version="1.1.0",
    author="zhanzq",
    author_email="zhanzhiqiang09@126.com",
    description="common utils",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zhanzq/common_utils",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
