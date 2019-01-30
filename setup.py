#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
setup.py
~~~~~~~~

Usage: python3 setup.py build_ext --inplace

:author: Wannes Meert
:copyright: Copyright 2017-2019 KU Leuven and Regents of the University of California.
:license: Apache License, Version 2.0, see LICENSE for details.
"""
from setuptools import setup
from setuptools.extension import Extension
import platform
import os
import re
from pathlib import Path


try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None

try:
    import cysignals
except ImportError:
    cysignals = None

# build_type = "debug"
build_type = "optimized"

here = Path(".")  # setup script requires relative paths

with (here / "pysdd" / "__init__.py").open('r') as fd:
    wrapper_version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                                fd.read(), re.MULTILINE).group(1)
if not wrapper_version:
    raise RuntimeError('Cannot find version information')

sdd_version = "2.0"

libwrapper_path = here / "pysdd" / "lib"
sdd_path = libwrapper_path / f"sdd-{sdd_version}"
lib_path = sdd_path / "lib"
# print(f"Platform: {platform.platform()}")
if "Darwin" in platform.platform():
    lib_path = lib_path / "Darwin"
    libsdd_path = lib_path / "libsdd.a"
elif "Linux" in platform.platform():
    lib_path = lib_path / "Linux"
    libsdd_path = lib_path / "libsdd.a"
elif "Windows" in platform.platform():
    lib_path = lib_path / "Windows"
    libsdd_path = lib_path / "libsdd.dll"
else:
    libsdd_path = lib_path / "libsdd.a"
inc_path = sdd_path / "include"
src_path = sdd_path / "src"
csrc_path = here / "pysdd" / "src"
# c_files_paths = src_path.glob("**/*.c")
c_files_paths = (src_path / "fnf").glob("*.c")
c_dirs_paths = set(p.parent for p in src_path.glob("**/*.c"))
all_c_file_paths = [str(p) for p in c_files_paths]  # + [str(p) for p in csrc_path.glob("*.c")]
# print("Found c files: ", ", ".join([str(p) for p in all_c_file_paths]))

os.environ["LDFLAGS"] = f"-L{lib_path}"
os.environ["CPPFLAGS"] = f"-I{inc_path} " + f"-I{csrc_path} " + \
                         " ".join(f"-I{p}" for p in c_dirs_paths)

compile_time_env = dict(HAVE_CYSIGNALS=False)
if cysignals is not None:
    compile_time_env['HAVE_CYSIGNALS'] = True

if "Darwin" in platform.platform() or "Linux" in platform.platform():
    if build_type == "debug":
        gdb_debug = True
        extra_compile_args = ["-march=native", "-O0", "-g"]
    else:
        gdb_debug = False
        extra_compile_args = ["-march=native", "-O2"]
elif "Windows" in platform.platform():
    if build_type == "debug":
        gdb_debug = True
        extra_compile_args = []
    else:
        gdb_debug = False
        extra_compile_args = []

if cythonize is not None:
    ext_modules = cythonize([
        Extension(
            "pysdd.sdd", [str(here / "pysdd" / "sdd.pyx")] + all_c_file_paths,
            extra_objects=[str(libsdd_path)],
            extra_compile_args=extra_compile_args
            # include_dirs=[numpy.get_include()]
        )],
        compiler_directives={'embedsignature': True},
        gdb_debug=gdb_debug,
        compile_time_env=compile_time_env)
else:
    ext_modules = []
    print('Cython not yet available, skipping compilation')

# install_requires = ['numpy', 'cython']
install_requires = ['cython']
tests_require = ['pytest']

with (here / 'README.rst').open('r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='PySDD',
    version=wrapper_version,
    description='Sentential Decision Diagrams',
    long_description=long_description,
    author='Wannes Meert, Arthur Choi',
    author_email='wannes.meert@cs.kuleuven.be',
    url='https://github.com/wannesm/PySDD',
    project_urls={
        'PySDD documentation': 'http://pysdd.readthedocs.io/en/latest/',
        'PySDD source': 'https://github.com/wannesm/PySDD'
    },
    packages=["pysdd"],
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={
        'all': ['cysignals', 'numpy']
    },
    include_package_data=True,
    package_data={
        '': ['*.pyx', '*.pxd', '*.h', '*.c', '*.so', '*.a', '*.dll', '*lib'],
    },
    entry_points={
        'console_scripts': [
            'pysdd = pysdd.cli:main'
        ]},
    python_requires='>=3.6',
    license='Apache 2.0',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Artificial Intelligence'
    ],
    keywords='sdd, knowledge compilation',
    ext_modules=ext_modules,
    zip_safe=False
)
