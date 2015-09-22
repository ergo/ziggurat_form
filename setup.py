from setuptools import setup, find_packages
from ziggurat_form import __version__

version = '{}.{}.{}'.format(__version__['major'],
                            __version__['minor'],
                            __version__['patch'])

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
    test_suite='ziggurat_form.tests',
    tests_require=[
        "coverage"
    ],
    install_requires=[
        "colander",
        "peppercorn",
        "webhelpers2",
        "six"]
)
