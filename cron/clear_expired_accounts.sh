#!/usr/bin/env bash
/home/nuser/venvs/iwwa/bin/python /home/nuser/wikiwho_api/cron/manage.py clear_expired_accounts
echo 'clear_expired_accounts is finished'