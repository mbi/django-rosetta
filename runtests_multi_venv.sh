#!/bin/bash

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

