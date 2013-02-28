#!/bin/bash

. venv_13/bin/activate
cd testproject
coverage run --rcfile=.coveragerc manage.py test --failfast rosetta
coverage xml
coverage html
cd ..
