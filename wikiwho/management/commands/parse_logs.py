from os import listdir
import csv

from django.core.management.base import BaseCommand


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
        timeouts = []
        recursions = []
        operationals = []
        others = []
        entry = []
        parsing_pattern = '#######*******#######'
        for log_file in listdir(log_folder):
            if log_file.endswith('.log'):
                # print(log_file)
                with open('{}/{}'.format(log_folder, log_file)) as f:
                    for line in f.readlines():
                        if parsing_pattern in line and entry:
                            text = ''.join(entry)
                            title = entry[0].split('ERROR')[-1].split('-(')[0].strip()
                            page_id = entry[0].split('ERROR')[-1].split('-(')[1].split(')')[0].strip()
                            if 'OperationalError' in text:  # TODO and 'DBError' in entry[0]:
                                operationals.append([title, page_id])
                            elif 'TimeoutError' in text:
                                timeouts.append([title, page_id])
                            elif 'RecursionError' in text:
                                recursions.append([title, page_id])
                            else:
                                others.append([title, page_id])
                            entry = [line]
                        else:
                            entry.append(line)
        with open('{}/timeouts.csv'.format(output_folder), 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(timeouts)
        with open('{}/recursions.csv'.format(output_folder), 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(recursions)
        with open('{}/operationals.csv'.format(output_folder), 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(operationals)
        with open('{}/others.csv'.format(output_folder), 'w', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerows(others)
