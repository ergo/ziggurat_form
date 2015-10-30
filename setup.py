import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

from ziggurat_form import __version__

version = '{}.{}.{}'.format(__version__['major'],
                            __version__['minor'],
                            __version__['patch'])


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = [
            '--cov=ziggurat_form',
            '-s'
        ]

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.verbose = True
        self.test_suite = 'tests'

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='ziggurat_form',
    version=version,
    description=""" Set of classes that are reusable across various types of
    web apps, base user object, auth relationships + structured resource tree
    """,
    author='Marcin Lulek',
    author_email='info@webreactor.eu',
    license='BSD',
    packages=find_packages(),
    zip_safe=True,
    # include_package_data=True,
    package_data={
        '': ['*.txt', '*.rst', '*.ini', '*.mako', 'README'],
    },
    cmdclass={"test": PyTest},
    test_suite='pytest',
    install_requires=[
        "colander",
        "peppercorn",
        "webhelpers2",
        "six"
    ],
    tests_require=[
        "coverage",
        "pytest",
        "pytest-cov"
    ]
)
