from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='housekeeper',
      version=version,
      description="Credential caching daemon.",
      long_description="""\
Credential caching daemon to be used along the python keyring. Perfect for mercurial HTTP temporal credential storage.""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='credential keyring daemon',
      author='Jaime Soriano',
      author_email='jsoriano@tuenti.com',
      url='https://github.com/jsoriano/housekeeper',
      license='GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=['python-daemon>=1.0'],
      entry_points="""
	[console_scripts]
        housekeeper = housekeeper.keyring:main
      """,
      )
