#!/usr/bin/env bash
rm ./dist/*.tar.gz
python -m build
pip install ./dist/*.tar.gz
