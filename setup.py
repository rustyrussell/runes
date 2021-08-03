from setuptools import setup  # type: ignore
import os.path


with open('README.md', 'r') as f:
    long_description = f.read()


with open('requirements.txt', 'r') as f:
    requirements = [r for r in f.read().split('\n') if len(r)]


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, rel_path), 'r') as f:
        return f.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith('__version__'):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


# Take description from first line of README.md
description = long_description.split('\n')[0].split(' - ')[1]

setup(name='runes',
      version=get_version("runes/__init__.py"),
      description=description,
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='http://github.com/rustyrussell/runes',
      author='Rusty Russell',
      author_email='rusty@rustcorp.com.au',
      license='MIT',
      scripts=[],
      zip_safe=True,
      packages=['runes'],
      install_requires=requirements)
