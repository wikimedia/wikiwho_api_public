# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py generate_articles -p '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/local/all_articles_list' -s 4040 -e 4041 -m 90 -t 300
"""
from django.core.management.base import BaseCommand, CommandError
from collections import OrderedDict
from os import listdir
from os.path import isfile, join
import csv
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed  # , TimeoutError, CancelledError
import logging
import re
from time import strftime

from api.handler import WPHandler


def generate_article(article_title, check_exists_in_db=False):
    with WPHandler(article_title, check_exists_in_db=check_exists_in_db) as wp:
        wp.handle(revision_ids=[], format_='json', is_api=False)
    # print(article_title)
    return True


class Command(BaseCommand):
    help = 'Generates articles in csv files in given path from wp api.'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path', help='Path where list of articles are saved', required=True)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of threads/processors to run parallel.',
                            required=True)
        parser.add_argument('-t', '--timeout', type=float, required=False,
                            help='This feature does not work for now. Timeout value for each worker [minutes]')
        parser.add_argument('-tpe', '--thread_pool_executor', action='store_true',
                            help='Use ThreadPoolExecutor, default is ProcessPoolExecutor', default=False,
                            required=False)
        parser.add_argument('-s', '--start', type=int, help='From range', required=False)
        parser.add_argument('-e', '--end', type=int, help='To range', required=False)
        parser.add_argument('-c', '--check_exists', action='store_true',
                            help='Check if an article exists in db before creating it. If yes, go to the next article. '
                                 'If not, process article. '
                                 'Be careful that if yes, this costs 1 extra db query for each article!',
                            default=False, required=False)

    def handle(self, *args, **options):
        path = options['path']
        max_workers = options['max_workers']
        is_ppe = not options['thread_pool_executor']
        start = options['start']
        end = options['end']
        check_exists_in_db = options['check_exists']
        timeout = options['timeout'] * 60 if options['timeout'] else None  # convert into seconds
        # if start > end:
        #     raise CommandError('start ({}) must be >= end ({})'.format(start, end))

        file_list = [join(path, f) for f in listdir(path) if isfile(join(path, f)) and re.search(r'-(\d*).', f)]
        ordered_file_list = sorted(file_list, key=lambda x: (int(re.search(r'-(\d*).', x).group(1)), x))
        article_list_files = OrderedDict()
        counter = 0
        for f in ordered_file_list:
            i = int(re.search(r'-(\d*).', f).group(1))
            if counter == 0 and not start and start != 0:
                start = i
            if counter == len(ordered_file_list) - 1 and not end and end != 0:
                end = i
            article_list_files[join(path, f)] = i
            counter += 1

        parsing_pattern = '#######*******#######'
        if is_ppe:
            Executor = ProcessPoolExecutor
            format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'
        else:
            Executor = ThreadPoolExecutor
            format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'

        # logger_timeout = logging.getLogger('timeout')
        # file_handler = logging.FileHandler('{}/logs/timeouts_{}_at_{}.log'.format(path,
        #                                                                           '_'.join([str(start), str(end)]),
        #                                                                           strftime("%Y-%m-%d-%H:%M:%S")))
        # file_handler.setLevel(logging.ERROR)
        # formatter = logging.Formatter('%(message)s')
        # file_handler.setFormatter(formatter)
        # logger_timeout.addHandler(file_handler)
        logger = logging.getLogger('')
        # logger = logging.getLogger('error')
        timeout = None
        for article_list_file in article_list_files:
            csv_number = article_list_files[article_list_file]
            if start <= csv_number <= end:
                with open(article_list_file, 'r') as csv_file:
                    input_articles = csv.reader(csv_file, delimiter=";")
                    # for article in input_articles:
                    #     try:
                    #         generate_article(generate_article, article[0], check_exists_in_db)
                    #     except Exception as exc:
                    #         logger.exception(article[0])

                    file_handler = logging.FileHandler('{}/logs/{}_at_{}.log'.format(path, csv_number,
                                                                                     strftime("%Y-%m-%d-%H:%M:%S")))
                    file_handler.setLevel(logging.ERROR)
                    formatter = logging.Formatter(format_)
                    file_handler.setFormatter(formatter)
                    logger.handlers = [file_handler]
                    # logger.addHandler(file_handler)

                    print('Start: {} at {}'.format(csv_number, strftime("%H:%M:%S %d-%m-%Y")))
                    # We can use a with statement to ensure threads are cleaned up promptly
                    with Executor(max_workers=max_workers) as executor:
                        # Start the load operations and mark each future with its article
                        # TODO there are also page_ids in csv: article[1]. in future pass them to WPHandnler
                        future_to_article = {executor.submit(generate_article, article[0], check_exists_in_db):
                                             article[0]
                                             for article in input_articles}

                        del input_articles  # release memory

                        for future in as_completed(future_to_article):
                            article_name = future_to_article[future]
                        # for future, article_name in future_to_article.items():
                            try:
                                data = future.result(timeout=timeout)
                            # except (TimeoutError, CancelledError) as e:
                            #     logger_timeout.error(article_name)
                            except Exception as exc:
                                logger.exception('{}--------{}'.format(article_name, parsing_pattern))
                                # else:
                                #     print('Success: {}'.format(article_name))
                    print('Done: {} at {}'.format(csv_number, strftime("%H:%M:%S %d-%m-%Y")))
