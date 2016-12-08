# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py get_nonarticle_pages -p '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/server/batch_1/batch_11' -m 4
"""
from os import mkdir, listdir
from os.path import basename, exists
import logging
from time import strftime
import csv

from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor  # , TimeoutError, CancelledError
from mwxml import Dump
from mwtypes.files import reader

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


def write_nonarticle_pages(xml_file_path, log_folder, csv_folder, format_):
    xml_file_name = basename(xml_file_path)
    logger = logging.getLogger(xml_file_name[:-3].split('-')[-1])
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                xml_file_name,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    parsing_pattern = settings.LOG_PARSING_PATTERN

    non_articles = []
    print('Start: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))
    try:
        dump = Dump.from_file(reader(xml_file_path))
        # import itertools
        # dump = itertools.islice(dump, 20)
    except Exception as e:
        logger.exception('{}--------{}'.format(xml_file_name, parsing_pattern))
    else:
        for page in dump:
            try:
                if page.namespace != 0 and not page.redirect:
                    non_articles.append([page.id])
            except Exception as e:
                logger.exception('{}-({})--------{}'.format(page.title, page.id, parsing_pattern))

    csv_file = '{}/{}_at_{}.csv'.format(csv_folder, xml_file_name, strftime("%Y-%m-%d-%H:%M:%S"))
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(non_articles)
    print('Done: {} at {}'.format(xml_file_name, strftime("%H:%M:%S %d-%m-%Y")))
    return True


class Command(BaseCommand):
    help = 'Write namespace != 0 pages into csv.'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path', help='Path of xml folder where compressed dumps take place.',
                            required=True)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of processors/threads to run parallel. '
                                                                  'Default is # compressed files in given folder path.',
                            required=False)
        parser.add_argument('-tpe', '--thread_pool_executor', action='store_true',
                            help='Use ThreadPoolExecutor, default is ProcessPoolExecutor', default=False,
                            required=False)

    def handle(self, *args, **options):
        xml_folder = options['path']
        xml_folder = xml_folder[:-1] if xml_folder.endswith('/') else xml_folder
        xml_files = sorted(['{}/{}'.format(xml_folder, x)
                            for x in listdir(xml_folder)
                            if x.endswith('.7z')])
                            # if '.xml-' in x and not x.endswith('.7z')])
        if not xml_files:
            raise CommandError('In given folder ({}), there are no 7z files.'.format(xml_folder))
        log_folder = '{}/{}'.format(xml_folder, 'nonarticle_logs')
        if not exists(log_folder):
            mkdir(log_folder)
        csv_folder = '{}/{}'.format(xml_folder, 'nonarticle_csvs')
        if not exists(csv_folder):
            mkdir(csv_folder)

        max_workers = options['max_workers'] or len(xml_files)
        is_ppe = not options['thread_pool_executor']

        if is_ppe:
            Executor = ProcessPoolExecutor
            format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'
        else:
            Executor = ThreadPoolExecutor
            format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'

        logger = logging.getLogger('future_log')
        file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                    xml_folder.split('/')[-1],
                                                                    strftime("%Y-%m-%d-%H:%M:%S")))
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(format_)
        file_handler.setFormatter(formatter)
        logger.handlers = [file_handler]

        print(max_workers)
        # print(xml_files)
        with Executor(max_workers=max_workers) as executor:
            jobs = {}
            files_left = len(xml_files)
            files_iter = iter(xml_files)

            while files_left:
                for xml_file_path in files_iter:
                    job = executor.submit(write_nonarticle_pages, xml_file_path, log_folder, csv_folder, format_)
                    jobs[job] = basename(xml_file_path)
                    if len(jobs) == max_workers:  # limit # jobs with max_workers
                        break

                for job in as_completed(jobs):
                    files_left -= 1
                    xml_file_name = jobs[job]
                    try:
                        data = job.result()
                    except Exception as exc:
                        logger.exception(xml_file_name)

                    del jobs[job]
                    break  # to add a new job, if there is any
        print('Done: {} at {}'.format(xml_folder, strftime("%H:%M:%S %d-%m-%Y")))
