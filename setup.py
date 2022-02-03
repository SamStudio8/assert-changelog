#!/usr/bin/env python3

import setuptools

setuptools.setup(
    name="pre-commit-assert-changelog",
    version="0.0.1",

    author="Sam Nicholls",
    author_email="sam@samnicholls.net",

    packages=setuptools.find_packages(),
    install_requires=[
        #"keepachangelog @ git+https://github.com/Mulugruntz/keepachangelog.git@9ce1e3ce71f68168681a811b8f244269ba2dea32",
        "keepachangelog==2.0.0.dev2",
    ],

    entry_points = {
        'console_scripts': [
            'assert-changelog = assert_changelog.main:main',
        ]
    },

)
