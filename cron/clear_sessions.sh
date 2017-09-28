#!/usr/bin/env bash
source `which virtualenvwrapper.sh`
workon iwwa
cd /home/nuser/wikiwho_api/cron
python ../manage.py clearsessions
echo 'clearsessions is finished'