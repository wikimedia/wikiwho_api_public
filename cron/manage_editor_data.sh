#!/usr/bin/env bash
source `which virtualenvwrapper.sh`
workon iwwa
cd /home/nuser/wikiwho_api/cron
current_ym=$(date -u +%Y-%m)
next_ym="$(date -u +"%Y-%m" --date="$(date +%Y-%m-15) next month")"
python ../manage.py fill_editor_tables -from current_ym -to next_ym -m 12 -log '/home/nuser/dumps/xmls_7z/editor_data_logs' -lang 'en,de,eu'
echo 'fill_editor_tables is finished, starting manage_editor_tables'
python ../manage.py manage_editor_tables -from current_ym -to next_ym -m 12 -log '/home/nuser/dumps/xmls_7z/editor_data_logs' -lang 'en,de,eu'
echo 'manage_editor_tables is finished, starting empty_editor_tables'
python ../manage.py empty_editor_tables -m 12 -log '/home/nuser/dumps/xmls_7z/editor_data_logs' -lang 'en,de,eu'
echo 'empty_editor_tables is finished'
echo 'Editor data scripts are finished!'