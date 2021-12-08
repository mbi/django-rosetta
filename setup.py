import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as test_command


class Tox(test_command):
    user_options = [("tox-args=", "a", "Arguments to pass to tox")]

    def initialize_options(self):
        test_command.initialize_options(self)
        self.tox_args = None

    def finalize_options(self):
        test_command.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import shlex

        import tox

        args = self.tox_args
        if args:
            args = shlex.split(self.tox_args)
        errno = tox.cmdline(args=args)
        sys.exit(errno)


with open("README.rst") as readme:
    long_description = readme.read()

setup(
    name="django-rosetta",
    version=__import__("rosetta").get_version(limit=3),
    description="A Django application that eases the translation of Django projects",
    long_description=long_description,
    author="Marco Bonetti",
    author_email="mbonetti@gmail.com",
    url="https://github.com/mbi/django-rosetta",
    license="MIT",
    packages=find_packages(exclude=["testproject", "testproject.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Localization",
        "Topic :: Software Development :: Internationalization",
        "Framework :: Django",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=["Django >= 2.2", "requests >= 2.1.0", "polib >= 1.1.0"],
    tests_require=["tox", "vcrpy"],
    cmdclass={"test": Tox},
)
