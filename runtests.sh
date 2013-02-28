#!/bin/bash

. venv_13/bin/activate
cd testproject
python manage.py test rosetta
cd ..
deactivate
