# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py manage_editor_tables -from 2001-01 -to 2002-01 -m 3 -log '' -lang 'en,de,eu'
"""
import sys
import pytz
from time import strftime
from datetime import datetime, timedelta
from os.path import exists
from os import mkdir

from concurrent.futures import ProcessPoolExecutor, as_completed

from base.utils_log import get_logger
from wikiwho.utils_db import manage_editor_tables
from .fill_editor_tables import Command as CommandBase


def manage_editor_tables_base(language, from_ym, to_ym, log_folder):
    logger = get_logger('manage_editor_tables_{}_from_{}_{}_to_{}_{}'.
                        format(language, from_ym.year, from_ym.month, to_ym.year, to_ym.month),
                        log_folder, is_process=True, is_set=False, language=language)
    try:
        manage_editor_tables(language, from_ym, to_ym)
    except Exception as e:
        logger.exception('Manage editor tables exception {}-{}-{}'.format(language, from_ym, to_ym))


class Command(CommandBase):
    help = 'Partition editor tables if necessary and fill latest data into relevant editor table.'

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

        # set logging
        log_folder = options['log_folder']
        if not exists(log_folder):
            mkdir(log_folder)
        logger = get_logger('manage_editor_tables_from_{}_{}_to_{}_{}'.
                            format(from_ym.year, from_ym.month, to_ym.year, to_ym.month),
                            log_folder, is_process=True, is_set=True)

        print('Start at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
        print(max_workers, languages, from_ym, to_ym, log_folder)
        languages_iter = iter(languages)
        languages_all = len(languages)
        languages_left = languages_all
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            jobs = {}
            while languages_left:
                for language in languages_iter:
                    job = executor.submit(manage_editor_tables_base, language, from_ym, to_ym, log_folder)
                    jobs[job] = language
                    if len(jobs) == max_workers:  # limit # jobs with max_workers
                        break

                for job in as_completed(jobs):
                    languages_left -= 1
                    language_ = jobs[job]
                    try:
                        data = job.result()
                    except Exception as exc:
                        logger.exception('{}'.format(language_))

                    del jobs[job]
                    sys.stdout.write('\rPickles left: {} - Pickles processed: {:.3f}%'.
                                     format(languages_left, ((languages_all - languages_left) * 100) / languages_all))
                    break  # to add a new job, if there is any
        print('\nDone: {} - at {}'.format(language, strftime('%H:%M:%S %d-%m-%Y')))
