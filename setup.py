try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'SimpleIRC Python library',
    'author': 'Eric Gach',
    'author_email': 'eric@php-oop.net',
    'url': 'https://github.com/BigE/simpleirc',
    'download_url': '',
    'version': '0.0.1-dev',
    'install_requires': [],
    'packages': ['simpleirc'],
    'scripts': [],
    'name': 'simpleirc',
}

setup(**config)