#!/usr/bin/env bash
source `which virtualenvwrapper.sh`
workon iwwa
cd /home/nuser/wikiwho_api/cron
python ../manage.py clear_expired_accounts
echo 'clear_expired_accounts is finished'