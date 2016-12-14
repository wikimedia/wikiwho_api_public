# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py set_is_article_field -p '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/server/nonarticle_csvs'
"""
from django.core.management.base import BaseCommand
from os import listdir, mkdir
from os.path import exists
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import logging
import math
from time import strftime

from django.conf import settings

from wikiwho.models import Article


def set_is_article_field(ids, is_save):
    print('Start: {} - {} at {}'.format(ids[0], ids[-1], strftime("%H:%M:%S %d-%m-%Y")))
    if is_save:
        print('Done: {} - {} at {}'.format(ids[0], ids[-1], strftime("%H:%M:%S %d-%m-%Y")))
        Article.objects.filter(id__in=ids).update(is_article=False)
    else:
        print('Done without saving: {} - {} at {}'.format(ids[:5], ids[-5:], strftime("%H:%M:%S %d-%m-%Y")))
    return True


class Command(BaseCommand):
    help = 'Sets is_article field to False of articles with page id in given csv files.'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path', help='Path where csv files of page ids are saved.', required=True)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of threads/processors to run parallel.',
                            required=False)
        parser.add_argument('-tpe', '--thread_pool_executor', action='store_true',
                            help='Use ThreadPoolExecutor, default is ProcessPoolExecutor', default=False,
                            required=False)
        parser.add_argument('-s', '--save', help='Save into database.',
                            action='store_true', default=False, required=False)
        parser.add_argument('-b', '--batch', type=int, help='Number of Article objects that '
                                                            'will be processed per thread. Default is 500000',
                            required=False)

    def handle(self, *args, **options):
        csv_folder = options['path']
        csv_folder = csv_folder[:-1] if csv_folder.endswith('/') else csv_folder

        is_ppe = not options['thread_pool_executor']
        if is_ppe:
            Executor = ProcessPoolExecutor
            format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'
        else:
            Executor = ThreadPoolExecutor
            format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'

        # set logging
        log_folder = '{}/{}'.format(csv_folder, 'logs')
        if not exists(log_folder):
            mkdir(log_folder)
        logger = logging.getLogger('future_log')
        file_handler = logging.FileHandler('{}/future_log_at_{}.log'.format(log_folder, strftime("%Y-%m-%d-%H:%M:%S")))
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(format_)
        file_handler.setFormatter(formatter)
        logger.handlers = [file_handler]

        # get non article ids from csv files
        csv_files = listdir(csv_folder)
        ids = []
        for csv_file in csv_files:
            if csv_file.endswith('.csv'):
                with open('{}/{}'.format(csv_folder, csv_file), 'r') as f:
                    ids.extend([int(l) for l in f.read().splitlines()])
        is_save = options['save']
        batch = options['batch'] or 500000
        articles_count = len(ids)
        max_workers = options['max_workers'] or math.ceil(articles_count / batch)

        # start concurrent update
        print('Start: set is_article field at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
        print(is_save, batch, articles_count, max_workers, is_ppe)
        with Executor(max_workers=max_workers) as executor:
            future_to_slice = dict()
            for i in range(0, max_workers):
                future = executor.submit(set_is_article_field, ids[:batch], is_save)
                future_to_slice[future] = i
                del ids[:batch]

            for future in as_completed(future_to_slice):
                i = future_to_slice[future]
                try:
                    data = future.result()
                except Exception as exc:
                    logger.exception('-{}--------{}'.format(i, settings.LOG_PARSING_PATTERN))
        print('Done: set is_article field at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
