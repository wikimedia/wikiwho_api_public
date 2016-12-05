#!/usr/bin/env bash
source `which virtualenvwrapper.sh`
workon wwa
python ../manage.py clearsessions
echo 'clearsessions is finished'