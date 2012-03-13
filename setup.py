# This setup file is heavily inspired from the one from Scrapy 

from distutils.core import setup
import os
from distutils.command.install import INSTALL_SCHEMES

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

def is_not_module(filename):
    return os.path.splitext(f)[1] not in ['.py', '.pyc', '.pyo']

for scrapy_dir in ['scholar', 'web_client']:
    for dirpath, dirnames, filenames in os.walk(scrapy_dir):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'): del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(fullsplit(dirpath)))
            data = [f for f in filenames if is_not_module(f)]
            if data:
                data_files.append([dirpath, [os.path.join(dirpath, f) for f in data]])
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

setup_args = {
    'name' :'ScholarScape',
    'version' : '0.1.0',
    'packages' : packages,
    'data_files' : data_files,
    'license' : 'GNU GENERAL PUBLIC LICENSE 3',
    'long_description' : open('README.rst').read(),
    'author' : 'Patrick Browne',
    'author_email' : 'pt.browne@gmail.com',
    'url' : 'http://www.google.fr'
}

setup(**setup_args)