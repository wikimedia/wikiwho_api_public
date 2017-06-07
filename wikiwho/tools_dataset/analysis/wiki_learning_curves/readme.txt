Example commands to create wiki learning curves dataset
1. python extract_editors.py -r '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/revisions' -b '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/botlist.csv' -o '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors' -m=4
2. python aggregate_editors.py -i /home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors
3. python pick_editors.py
4. python compute_editor_data.py -r '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/revisions' -e '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors/editors-all-parts-filtered-2.csv' -t '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions' -o '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors' -m=4
