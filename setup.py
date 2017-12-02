#!/usr/bin/env python

from setuptools import setup

setup(name='ShuttleLocation',
      version='1.0',
      description='Shuttle location beacon reporting to the harokou app',
      url='https://github.com/omerzk/ShuttleWifi',
      install_requires=['pathlib', 'pynmea2', 'RPi.GPIO']
     )