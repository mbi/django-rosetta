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
    ],
    include_package_data=True,
    zip_safe=False
)
