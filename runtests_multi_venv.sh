#!/bin/bash

if [ ! -d venv_13 ]
then
    virtualenv --no-site-packages --distribute --python=python2 venv_13
    . venv_13/bin/activate
    pip install Django==1.3 coverage python-memcached six
    deactivate
fi
if [ ! -d venv_14 ]
then
    virtualenv --no-site-packages --distribute --python=python2 venv_14
    . venv_14/bin/activate
    pip install Django==1.4 coverage python-memcached six
    deactivate
fi
if [ ! -d venv_15 ]
then
    virtualenv --no-site-packages --distribute --python=python2 venv_15
    . venv_15/bin/activate
    pip install Django==1.5 coverage python-memcached six
    deactivate
fi
if [ ! -d venv_15_p3 ]
then
    virtualenv --no-site-packages --distribute --python=python3 venv_15_p3
    . venv_15_p3/bin/activate
    pip install Django==1.5 coverage python3-memcached six
    deactivate
fi
if [ ! -d venv_16 ]
then
    virtualenv --no-site-packages --distribute --python=python2 venv_16
    . venv_16/bin/activate
    pip install https://github.com/django/django/archive/1.6b1.zip
    pip install coverage python-memcached six
    deactivate
fi
if [ ! -d venv_16_p3 ]
then
    virtualenv --no-site-packages --distribute --python=python3 venv_16_p3
    . venv_16_p3/bin/activate
    pip install https://github.com/django/django/archive/1.6b1.zip
    pip install coverage python3-memcached six
    deactivate
fi



. venv_13/bin/activate
cd testproject
python manage.py --version
python manage.py test rosetta
cd ..
deactivate

. venv_14/bin/activate
cd testproject
python manage.py --version
python manage.py test rosetta
cd ..
deactivate

. venv_15/bin/activate
cd testproject
python manage.py --version
python manage.py test rosetta
cd ..
deactivate

. venv_15_p3/bin/activate
cd testproject
python manage.py --version
python --version
python manage.py test rosetta
cd ..
deactivate

. venv_16/bin/activate
cd testproject
python manage.py --version
python manage.py test rosetta
cd ..
deactivate

. venv_16_p3/bin/activate
cd testproject
python manage.py --version
python --version
python manage.py test rosetta
cd ..
deactivate

