from setuptools import setup, find_packages
setup(
    name='django-rosetta',
    version=__import__('rosetta').get_version(limit=3),
    description='A Django application that eases the translation of Django projects',
    long_description=open('README.rst').read(),
    author='Marat Valiev',
    author_email='valiev.m@gmail.com',
    url='https://github.com/user2589/django-rosetta',
    license='MIT',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Localization',
        'Topic :: Software Development :: Internationalization',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "Django >= 1.3",
        "polib >= 0.6.2",
    ],
)
