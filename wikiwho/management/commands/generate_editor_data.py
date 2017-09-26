# -*- coding: utf-8 -*-
"""
Example usage:
"""
from os.path import join, basename
import glob
from time import strftime
from datetime import datetime, timedelta
import pytz

from concurrent.futures import ProcessPoolExecutor, as_completed

from django.core.management.base import BaseCommand

from api.utils_pickles import get_pickle_folder
from base.utils_log import get_logger
from wikiwho.utils_db import fill_editor_table


def generate_editors_data(page_id, pickle_path, language, from_ym, to_ym, log_folder):
    logger = get_logger(page_id, log_folder, is_process=True, is_set=False, language=language)
    try:
        fill_editor_table(pickle_path, from_ym, to_ym, language, update=True)
    except Exception as e:
        logger.exception('{}-{}-{}-{}'.format(page_id, language, from_ym, to_ym))


class Command(BaseCommand):
    help = 'Generates editor data and fills the editor database.'

    def add_arguments(self, parser):
        parser.add_argument('-from', '--from_ym', required=True,
                            help='Year-month to created data from [YYYY-MM]. Included')
        parser.add_argument('-to', '--to_ym', required=True,
                            help='Year-month to created data until [YYYY-MM]. Not included.')
        parser.add_argument('-lang', '--language', help="Wikipedia language. Ex: 'en' or 'en,eu,de'", required=True)
        parser.add_argument('-log', '--log_folder', help='Folder where to write logs. Default is folder of xml folder',
                            required=True)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of processors/threads to run parallel. ',
                            required=True)
        # parser.add_argument('-t', '--timeout', type=float, required=False,
        #                     help='Timeout value for each processor for analyzing articles [minutes]')
        # parser.add_argument('-c', '--check_exists', action='store_true', help='', default=False, required=False)

    def handle(self, *args, **options):
        from_ym = options['from_ym']
        from_ym = datetime.strptime(from_ym, '%Y-%m').replace(tzinfo=pytz.UTC)
        to_ym = options['to_ym']
        to_ym = datetime.strptime(to_ym, '%Y-%m').replace(tzinfo=pytz.UTC) - timedelta(seconds=1)
        languages = options['language'].split(',')

        # get max number of concurrent workers
        max_workers = options['max_workers']

        print('Start at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
        print(max_workers, languages, from_ym, to_ym)
        # Concurrent process of pickles of each language to generate editor data
        for language in languages:
            # set logging
            log_folder = options['log_folder']
            logger = get_logger('future_log', log_folder, is_process=True, is_set=True, language=language)
            pickle_folder = get_pickle_folder(language)
            print('Start: {} - {} at {}'.format(language, pickle_folder, strftime("%H:%M:%S %d-%m-%Y")))

            pickles_iter = glob.iglob(join(pickle_folder, '*.p'))
            pickles_left = sum(1 for x in pickles_iter)
            pickles_iter = glob.iglob(join(pickle_folder, '*.p'))
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                jobs = {}
                while pickles_left:
                    for pickle_path in pickles_iter:
                        page_id = basename(pickle_path)[:-2]
                        job = executor.submit(generate_editors_data, page_id, pickle_path, language, from_ym, to_ym, log_folder)
                        jobs[job] = page_id
                        if len(jobs) == max_workers:  # limit # jobs with max_workers
                            break

                    for job in as_completed(jobs):
                        pickles_left -= 1
                        page_id_ = jobs[job]
                        try:
                            data = job.result()
                        except Exception as exc:
                            logger.exception('{}-{}'.format(page_id_, language))

                        del jobs[job]
                        break  # to add a new job, if there is any
            print('Done: {} - {} at {}'.format(language, pickle_folder, strftime("%H:%M:%S %d-%m-%Y")))
        print('Done at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
