#!/usr/bin/env bash
source `which virtualenvwrapper.sh`
workon iwwa
python /home/nuser/wikiwho_api/manage.py clearsessions
echo 'clearsessions is finished'