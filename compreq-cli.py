#!/usr/bin/env python3
# encoding: utf-8
"""
pysdd-cli
~~~~~~~~~

PySDD command line interface.

:author: Wannes Meert, Arthur Choi
:copyright: Copyright 2018 KU Leuven and Regents of the University of California.
:license: Apache License, Version 2.0, see LICENSE for details.
"""
import sys
import time

from pympler import muppy

from pysdd import cli

if __name__ == "__main__":
    c1 = time.time()
    cli.main()
    c2 = time.time()
    print("Memory: " + str(sum([muppy.getsizeof(obj) for obj in muppy.get_objects()])/1024) + "kB")
    print("Time: " + str(c2-c1))