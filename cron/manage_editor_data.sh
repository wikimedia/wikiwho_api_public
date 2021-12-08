#!/usr/bin/env bash
# create last month's editor data
venv='iwwa366'
wikiwho_api='/home/wikiwho/wikiwho_api'
logs_folder='/home/wikiwho/dumps/actions_logs'
python_cmd='/home/wikiwho/venvs/iwwa366/bin/python'
$threads=12

venv='wikiwho_api'
wikiwho_api='/home/ulloaro/git/wikiwho_api'
logs_folder='/home/ulloaro/git/wikiwho_api/tmp_pickles/editor'
python_cmd='/home/ulloaro/.virtualenvs/wikiwho_api/bin/python'
$threads=-1


last_ym="$(date -u +"%Y-%m" --date="$(date +%Y-%m-15) last month")"
logs_folder=$logs_folder$last_ym
current_ym=$(date -u +%Y-%m)
echo $logs_folder
echo $last_ym, $current_ym

echo $(which python)


$python_cmd $wikiwho_api/manage.py fill_notindexed_editor_tables -from $last_ym -to $current_ym -m 2 -log $logs_folder -lang 'en,de,eu'
echo 'fill_notindexed_editor_tables is finished, starting fill_indexed_editor_tables'
$python_cmd $wikiwho_api/manage.py fill_indexed_editor_tables -from $last_ym -to $current_ym -m -1 -log $logs_folder -lang 'en,de,eu'
echo 'fill_indexed_editor_tables is finished, starting empty_notindexed_editor_tables'
$python_cmd $wikiwho_api/manage.py empty_notindexed_editor_tables -m -1 -log $logs_folder -lang 'en,de,eu'
echo 'empty_notindexed_editor_tables is finished'
echo 'Editor data scripts are finished!'
