#!/usr/bin/env bash
source `which virtualenvwrapper.sh`
workon iwwa
python /home/nuser/wikiwho_api/cron/manage.py clear_expired_accounts
echo 'clear_expired_accounts is finished'