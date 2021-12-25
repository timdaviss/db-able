"""
Setup script
"""

import json
import re

import setuptools


with open('README.md', 'r') as fh:
    long_description = fh.read()

package = json.load(open('package.json', 'r'))
author = package['author']
author_name = re.sub('(<(?:.*)>)', '', author).strip()
author_email = re.search(r'<(.*)>', author).groups()[0]

announcement = 'Building for version %s' % package['version']
print('%s' % ''.join(['*'] * len(announcement)))
print(announcement)
print('%s\n\n' % ''.join(['*'] * len(announcement)))

setuptools.setup(
    name=package['name'],
    version=package['version'],
    author=author_name,
    author_email=author_email,
    description=package['description'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=package['url'],
    packages=setuptools.find_packages(),
    install_requires=[
        'do-py>=0.3',
        'sqlalchemy>=1',
        'pymysql>=1',
        'pyhumps>=3',
        ],
    # https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Operating System :: OS Independent',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python',
        'Programming Language :: Python :: 3.9',
        ],
    keywords=['development', 'OO']
    )
