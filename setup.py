from setuptools import setup, find_packages
setup(
    name='django-rosetta',
    version=__import__('rosetta').get_version(limit=3),
    description='A Django application that eases the translation of Django projects',
    author='Marco Bonetti',
    author_email='mbonetti@gmail.com',
    url='https://github.com/mbi/django-rosetta',
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
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'six >=1.2.0',
        'Django >= 1.3',
        'requests >= 2.1.0',
        'polib >= 1.0.6',
        'microsofttranslator == 0.5'
    ]
)
