"""
Example usage:
python manage.py parse_logs -i '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/server_logs/logs_4'
"""
from os import mkdir, listdir
from os.path import exists
import csv
import json

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Parse and group logs and write failed articles into csvs. Log files must have .log extension.'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--input', help='Path of log folder.', required=True)
        parser.add_argument('-o', '--output', help='Folder to output csvs. Default is input.', required=False)

    def handle(self, *args, **options):
        log_folder = options['input']
        log_folder = log_folder[:-1] if log_folder.endswith('/') else log_folder
        output_folder = options['output'] or log_folder
        output_folder = output_folder[:-1] if output_folder.endswith('/') else output_folder
        csv_output_folder = '{}/csvs'.format(output_folder)
        if not exists(csv_output_folder):
            mkdir(csv_output_folder)
        json_output_folder = '{}/jsons'.format(output_folder)
        if not exists(json_output_folder):
            mkdir(json_output_folder)
        json_errors_dict = {}
        timeouts = []
        recursions = []
        operationals = []
        alreadies = []
        others = []
        entry = []  # entry in logs
        for log_file in listdir(log_folder):
            if log_file.endswith('.log'):
                timeouts_curr = []
                recursions_curr = []
                operationals_curr = []
                alreadies_curr = []
                others_curr = []
                # print(log_file)
                with open('{}/{}'.format(log_folder, log_file)) as f:
                    for line in f.readlines():
                        if settings.LOG_PARSING_PATTERN in line:
                            if entry:
                                log_text = ''.join(entry)
                                article_title = entry[0].split('ERROR')[-1].split('-(')[0].strip()
                                page_id = entry[0].split('ERROR')[-1].split('-(')[1].split(')')[0].strip()
                                if 'OperationalError' in log_text:  # TODO and 'DBError' in entry[0]:
                                    operationals_curr.append([article_title, page_id])
                                elif 'TimeoutError' in log_text:
                                    timeouts_curr.append([article_title, page_id])
                                elif 'RecursionError' in log_text:
                                    recursions_curr.append([article_title, page_id])
                                elif "api.handler.WPHandlerException: 'Article" in log_text:
                                    alreadies_curr.append([article_title, page_id])
                                else:
                                    others_curr.append([article_title, page_id])
                                entry = [line]
                            else:
                                entry.append(line)
                        else:
                            entry.append(line)

                    if entry:
                        log_text = ''.join(entry)
                        article_title = entry[0].split('ERROR')[-1].split('-(')[0].strip()
                        page_id = entry[0].split('ERROR')[-1].split('-(')[1].split(')')[0].strip()
                        if 'OperationalError' in log_text:  # TODO and 'DBError' in entry[0]:
                            operationals_curr.append([article_title, page_id])
                        elif 'TimeoutError' in log_text:
                            timeouts_curr.append([article_title, page_id])
                        elif 'RecursionError' in log_text:
                            recursions_curr.append([article_title, page_id])
                        elif "api.handler.WPHandlerException: 'Article" in log_text:
                            alreadies_curr.append([article_title, page_id])
                        else:
                            others_curr.append([article_title, page_id])
                        entry = []
                timeouts.extend(timeouts_curr)
                recursions.extend(recursions_curr)
                operationals.extend(operationals_curr)
                alreadies.extend(alreadies_curr)
                others.extend(others_curr)
                json_errors_dict[log_file.split('_at_')[0]] = {
                    'timeouts': timeouts_curr,
                    'recursions': recursions_curr,
                    'operationals': operationals_curr,
                    # 'alreadies': alreadies_curr,
                    'others': others_curr
                }
        with open('{}/errors.json'.format(json_output_folder), 'w') as fp:
            json.dump(json_errors_dict, fp, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False)

        with open('{}/timeouts.csv'.format(csv_output_folder), 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(timeouts)
        with open('{}/recursions.csv'.format(csv_output_folder), 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(recursions)
        with open('{}/operationals.csv'.format(csv_output_folder), 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(operationals)
        with open('{}/alreadies.csv'.format(csv_output_folder), 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(alreadies)
        with open('{}/others.csv'.format(csv_output_folder), 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(others)
