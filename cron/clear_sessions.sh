#!/usr/bin/env bash
source `which virtualenvwrapper.sh`
workon ww_dj3
python ../manage.py clearsessions
echo 'clearsessions is finished'