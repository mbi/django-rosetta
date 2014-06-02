#!/bin/bash

if [ ! -d .venv_14 ]
then
    virtualenv --no-site-packages --distribute --python=python2.7 .venv_14
    . .venv_14/bin/activate
    pip install --use-mirrors Django==1.4 coverage python-memcached six requests==2.1.0 polib==1.0.4 microsofttranslator==0.5
    deactivate
fi
if [ ! -d .venv_15 ]
then
    virtualenv --no-site-packages --distribute --python=python2.7 .venv_15
    . .venv_15/bin/activate
    pip install --use-mirrors Django==1.5 coverage python-memcached six requests==2.1.0 polib==1.0.4 microsofttranslator==0.5
    deactivate
fi
if [ ! -d .venv_15_p3 ]
then
    virtualenv --no-site-packages --distribute --python=python3 .venv_15_p3
    . .venv_15_p3/bin/activate
    pip install --use-mirrors Django==1.5 coverage python3-memcached six requests==2.1.0 polib==1.0.4 microsofttranslator==0.5
    deactivate
fi
if [ ! -d .venv_16 ]
then
    virtualenv --no-site-packages --distribute --python=python2.7 .venv_16
    . .venv_16/bin/activate
    pip install --use-mirrors coverage python-memcached six  Django==1.6.1 requests==2.1.0 polib==1.0.4 microsofttranslator==0.5
    deactivate
fi
if [ ! -d .venv_16_p3 ]
then
    virtualenv --no-site-packages --distribute --python=python3 .venv_16_p3
    . .venv_16_p3/bin/activate
    pip install --use-mirrors coverage python3-memcached six  Django==1.6.1 requests==2.1.0 polib==1.0.4 microsofttranslator==0.5
    deactivate
fi
if [ ! -d .venv_17b ]
then
    virtualenv --no-site-packages --distribute --python=python2.7 .venv_17b
    . .venv_17b/bin/activate
    pip install https://www.djangoproject.com/download/1.7.b4/tarball/
    pip install --use-mirrors coverage python-memcached six  requests==2.1.0 polib==1.0.4 microsofttranslator==0.5
    deactivate
fi
if [ ! -d .venv_17b_p3 ]
then
    virtualenv --no-site-packages --distribute --python=python3 .venv_17b_p3
    . .venv_17b_p3/bin/activate
    pip install https://www.djangoproject.com/download/1.7.b4/tarball/
    pip install --use-mirrors coverage python3-memcached six  requests==2.1.0 polib==1.0.4 microsofttranslator==0.5
    deactivate
fi


. .venv_14/bin/activate
cd testproject
python manage.py --version
python --version
python manage.py test rosetta
cd ..
deactivate

. .venv_15/bin/activate
cd testproject
python manage.py --version
python --version
python manage.py test rosetta
cd ..
deactivate

. .venv_15_p3/bin/activate
cd testproject
python manage.py --version
python --version
python manage.py test rosetta
cd ..
deactivate

. .venv_16/bin/activate
cd testproject
python manage.py --version
python --version
python manage.py test rosetta
cd ..
deactivate

. .venv_16_p3/bin/activate
cd testproject
python manage.py --version
python --version
python manage.py test rosetta
cd ..
deactivate

. .venv_17b/bin/activate
cd testproject
python manage.py --version
python --version
python manage.py test rosetta
cd ..
deactivate

. .venv_17b_p3/bin/activate
cd testproject
python manage.py --version
python --version
python manage.py test rosetta
cd ..
deactivate

# Check translations
for d in `find rosetta -name LC_MESSAGES -type d`; do msgfmt -c -o $d/django.mo $d/django.po; done
