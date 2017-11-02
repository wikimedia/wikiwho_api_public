#!/usr/bin/env bash
# create last month's editor data
last_ym="$(date -u +"%Y-%m" --date="$(date +%Y-%m-15) last month")"
logs_folder='/home/nuser/dumps/xmls_7z/editor_data_logs_'
logs_folder=$logs_folder$last_ym
current_ym=$(date -u +%Y-%m)
echo $logs_folder
echo $last_ym, $current_ym
echo $(which python)
/home/nuser/venvs/iwwa/bin/python /home/nuser/wikiwho_api/manage.py fill_editor_tables -from $last_ym -to $current_ym -m 12 -log $logs_folder -lang 'en,de,eu'
echo 'fill_editor_tables is finished, starting manage_editor_tables'
/home/nuser/venvs/iwwa/bin/python /home/nuser/wikiwho_api/manage.py manage_editor_tables -from $last_ym -to $current_ym -m 12 -log $logs_folder -lang 'en,de,eu'
echo 'manage_editor_tables is finished, starting empty_editor_tables'
/home/nuser/venvs/iwwa/bin/python /home/nuser/wikiwho_api/manage.py empty_editor_tables -m 12 -log $logs_folder -lang 'en,de,eu'
echo 'empty_editor_tables is finished'
echo 'Editor data scripts are finished!'