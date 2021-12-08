#!/usr/bin/env bash
/home/wikiwho/venvs/iwwa366/bin/python /home/wikiwho/wikiwho_api/cron/manage.py clear_expired_accounts
echo 'clear_expired_accounts is finished'
