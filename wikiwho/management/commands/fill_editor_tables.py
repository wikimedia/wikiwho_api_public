# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py fill_editor_tables -from 2001-01 -to 2002-01 -m 6 -log '' -lang 'en,de,eu'
"""
import glob
import pytz
import sys
from os.path import join, basename
from time import strftime
from datetime import datetime, timedelta

from concurrent.futures import ProcessPoolExecutor, as_completed

from django.core.management.base import BaseCommand

from api.utils_pickles import get_pickle_folder
from base.utils_log import get_logger
from wikiwho.utils_db import fill_editor_tables


class Command(BaseCommand):
    help = 'Generates editor data and fills the editor database per ym, editor, article.'

    def add_arguments(self, parser):
        parser.add_argument('-from', '--from_ym', required=True,
                            help='Year-month to created data from [YYYY-MM]. Included.')
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

    def get_parameters(self, options):
        from_ym = options['from_ym']
        from_ym = datetime.strptime(from_ym, '%Y-%m').replace(tzinfo=pytz.UTC)
        to_ym = options['to_ym']
        to_ym = datetime.strptime(to_ym, '%Y-%m').replace(tzinfo=pytz.UTC) - timedelta(seconds=1)
        languages = options['language'].split(',')
        max_workers = options['max_workers']
        return from_ym, to_ym, languages, max_workers

    def handle(self, *args, **options):
        from_ym, to_ym, languages, max_workers = self.get_parameters(options)

        print('Start at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
        print(max_workers, languages, from_ym, to_ym)
        # Concurrent process of pickles of each language to generate editor data
        for language in languages:
            # set logging
            log_folder = options['log_folder']
            logger = get_logger('fill_editor_tables_future_log_{}'.format(language),
                                log_folder, is_process=True, is_set=True, language=language)
            pickle_folder = get_pickle_folder(language)
            print('Start: {} - {} at {}'.format(language, pickle_folder, strftime('%H:%M:%S %d-%m-%Y')))

            pickles_iter = glob.iglob(join(pickle_folder, '*.p'))
            pickles_all = sum(1 for x in pickles_iter)
            pickles_left = pickles_all
            pickles_iter = glob.iglob(join(pickle_folder, '*.p'))
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                jobs = {}
                while pickles_left:
                    for pickle_path in pickles_iter:
                        page_id = basename(pickle_path)[:-2]
                        job = executor.submit(fill_editor_tables, pickle_path, from_ym, to_ym, language, update=True)
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
                        sys.stdout.write('\rPickles left: {} - Pickles processed: {:.3f}%'.
                                         format(pickles_left, ((pickles_all - pickles_left) * 100) / pickles_all))
                        break  # to add a new job, if there is any
            print('\nDone: {} - {} at {}'.format(language, pickle_folder, strftime('%H:%M:%S %d-%m-%Y')))
        print('Done at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
