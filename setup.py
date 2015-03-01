#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cohort

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'Django >= 1.6.0',
]

test_requirements = [
    'pytest',
]

setup(
    name='django_cohort_analysis',
    version=cohort.__version__,
    description="A small app to perform cohort analysis in Django",
    long_description=readme + '\n\n' + history,
    author="John Turner",
    author_email='john@springmoves.com',
    url='https://github.com/jturner/django_cohort_analysis',
    packages=[
        'django_cohort_analysis',
    ],
    package_dir={'django_cohort_analysis':
                 'django_cohort_analysis'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords=['django', 'cohort', 'cohort analysis'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
