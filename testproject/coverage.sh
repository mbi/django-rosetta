#!/bin/sh
coverage run --rcfile .coveragerc  manage.py test --failfast rosetta
coverage xml
coverage html
