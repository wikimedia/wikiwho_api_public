# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py generate_articles -p '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/local/all_articles_list' -s 4040 -e 4040 -m 40
"""
from django.core.management.base import BaseCommand, CommandError
from collections import OrderedDict
from os import listdir
from os.path import isfile, join, exists, basename
import csv
import concurrent.futures
import logging
import re
from time import strftime

from api.handler import WPHandler


def generate_article(article_title, check_exists=False):
    # TODO do this with page_id in the future?
    with WPHandler(article_title, check_exists=check_exists) as wp:
        wp.handle(revision_ids=[], format_='json', is_api=False)
    # print(article_title)
    return True


class Command(BaseCommand):
    help = 'Generates articles in given path.'

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path', help='Path where list of articles are saved', required=True)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of threads/processors to run parallel.',
                            required=True)
        parser.add_argument('-ppe', '--processor_pool_executor', action='store_true',
                            help='Use ProcessPoolExecutor, default is ThreadPoolExecutor', default=False,
                            required=False)
        parser.add_argument('-s', '--start', type=int, help='From range', required=False)
        parser.add_argument('-e', '--end', type=int, help='To range', required=False)
        parser.add_argument('-c', '--check_exists', action='store_true',
                            help='Check if an article exists before creating it. If yes, go to the next article. '
                                 'If not, process article. '
                                 'Be careful that if yes, this costs 1 extra db query for each article!',
                            default=False, required=False)

    def handle(self, *args, **options):
        path = options['path']
        max_workers = options['max_workers']
        is_ppe = options['processor_pool_executor']
        start = options['start']
        end = options['end']
        check_exists = options['check_exists']
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

        logging.basicConfig(level=logging.ERROR,
                            format='%(levelname)s:%(name)s:%(asctime)s:%(message)s')
        logger = logging.getLogger('')
        # already_list_file = '{}/logs/already_at_{}.txt'.format(path, strftime("%H:%M:%S %d-%m-%Y"))
        for article_list_file in article_list_files:
            if start <= article_list_files[article_list_file] <= end:
                print('Start: {} at {}'.format(article_list_file, strftime("%H:%M:%S %d-%m-%Y")))
                handler = logging.FileHandler('{}/logs/{}_at_{}.log'.format(path,
                                                                            basename(article_list_file).split('.')[0],
                                                                            strftime("%Y-%m-%d-%H:%M:%S")))
                # print(logger.handlers)
                # logger.removeHandler(logging.StreamHandler)
                # logger.addHandler(handler)
                logger.handlers = [handler]
                with open(article_list_file, 'r') as csv_file:
                    input_articles = csv.reader(csv_file, delimiter=";")
                    # for article in input_articles:
                    #     try:
                    #         generate_pickle(article[0], already_list_file, pickle_folder, pickle_folder_2)
                    #     except Exception as exc:
                    #         logger.exception(article[0])

                    # We can use a with statement to ensure threads are cleaned up promptly
                    if is_ppe:
                        # use ProcessPoolExecutor
                        print('Not implemented')  # FIXME requests.session throws sslerror
                        # with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
                        #     # Start the load operations and mark each future with its article
                        #     future_to_article = {executor.submit(generate_pickle, article[0], already_list_file,  pickle_folder, pickle_folder_2):
                        #                          article[0]
                        #                          for article in input_articles}
                        #     for future in concurrent.futures.as_completed(future_to_article):
                        #         article_name = future_to_article[future]
                        #         try:
                        #             data = future.result(timeout=None)
                        #         except Exception as exc:
                        #             # TODO use queue or lock for logging with multiPROCESSING
                        #             # https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
                        #             logger.exception(article_name)
                        #         # else:
                        #         #     print('Success: {}'.format(article_name))
                    else:
                        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                            # Start the load operations and mark each future with its article
                            future_to_article = {executor.submit(generate_article, article[0], check_exists): article[0]
                                                 for article in input_articles}
                            for future in concurrent.futures.as_completed(future_to_article):
                                article_name = future_to_article[future]
                                try:
                                    data = future.result(timeout=None)
                                except Exception as exc:
                                    # no need for lock, logger is thread safe
                                    logger.exception(article_name)
                                    # else:
                                    #     print('Success: {}'.format(article_name))
                print('Done: {} at {}'.format(article_list_file, strftime("%H:%M:%S %d-%m-%Y")))
