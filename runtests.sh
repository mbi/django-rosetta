#!/bin/bash

if [ ! -d venv_13 ]
then
    virtualenv --no-site-packages --distribute --python=python2 venv_13
    . venv_13/bin/activate
    pip install Django==1.3 coverage python-memcached six
    deactivate
fi


. venv_13/bin/activate
cd testproject
python manage.py test rosetta
cd ..
deactivate
