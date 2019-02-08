# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py fill_indexed_editor_tables -from 2001-01 -to 2002-01 -m 3 -log '' -lang 'en,de,eu'
"""
import sys
import pytz
from time import strftime
from datetime import datetime, timedelta
from os.path import exists
from os import mkdir
import logging

from concurrent.futures import ProcessPoolExecutor, as_completed

from django.core.management.base import BaseCommand
from django.conf import settings
from django import db

from base.utils_log import get_logger, close_logger
from api_editor.utils_db import fill_indexed_editor_tables


def fill_indexed_editor_tables_batch(from_ym, to_ym, languages, max_workers, log_folder):
    if not exists(log_folder):
        mkdir(log_folder)

    parallel = max_workers >= 1
    logger = get_logger('fill_indexed_editor_tables',
                        log_folder, is_process=parallel, is_set=True, level=logging.INFO,
                        descriptor=f'From:{from_ym.date()} To:{to_ym.date()}')
    logger.info(f"Start filling up INDEXED tables")

    print('Start at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
    print(max_workers, languages, from_ym,
          to_ym, log_folder)

    languages_iter = iter(languages)
    languages_all = len(languages)
    languages_left = languages_all
    if not parallel:
        for language in languages_iter:
            try:
                fill_indexed_editor_tables(
                    language, from_ym, to_ym)
                print(f'{language} indexed table has been filled')
            except Exception as exc:
                logger.exception('{}'.format(language))
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            jobs = {}
            while languages_left:
                for language in languages_iter:
                    job = executor.submit(
                        fill_indexed_editor_tables, language, from_ym, to_ym)
                    jobs[job] = language
                    if len(jobs) == max_workers:  # limit # jobs with max_workers
                        break

                for job in as_completed(jobs):
                    languages_left -= 1
                    job_language = jobs[job]

                    try:
                        data = job.result()
                    except Exception as exc:
                        logger.exception('{}'.format(job_language))

                    del jobs[job]
                    sys.stdout.write('\rLanguages left: {} - Languages processed: {:.3f}%'.
                                     format(languages_left, languages_all - languages_left))
                    break  # to add a new job, if there is any

        # force all connections to close (necessary for the SSL PostgreSQL connections to work)
        db.connections.close_all()
        print('\nDone: {} - at {}'.format(language, strftime('%H:%M:%S %d-%m-%Y')))


class Command(BaseCommand):
    help = 'Partition editor tables if necessary and fill latest data into relevant editor table.'

    def add_arguments(self, parser):
        parser.add_argument('-from', '--from_ym', required=True,
                            help='Year-month to create data from [YYYY-MM]. Included.')
        parser.add_argument('-to', '--to_ym', required=True,
                            help='Year-month to create data until [YYYY-MM]. Not included.')
        parser.add_argument('-lang', '--language',
                            help="Wikipedia language. Ex: 'en' or 'en,eu,de'", required=True)
        parser.add_argument('-log', '--log_folder',
                            help='Folder where to write logs.',
                            default=settings.ACTIONS_LOG)
        parser.add_argument('-m', '--max_workers', type=int,
                            help='Number of processors/threads to run parallel.',
                            default=settings.ACTIONS_MAX_WORKERS)

    def get_parameters(self, options):
        from_ym = options['from_ym']
        from_ym = datetime.strptime(from_ym, '%Y-%m').replace(tzinfo=pytz.UTC)
        to_ym = options['to_ym']
        to_ym = datetime.strptime(
            to_ym, '%Y-%m').replace(tzinfo=pytz.UTC) - timedelta(seconds=1)
        languages = options['language'].split(',')
        max_workers = options['max_workers']
        return from_ym, to_ym, languages, max_workers, options['log_folder']

    def handle(self, *args, **options):
        fill_indexed_editor_tables_batch(*self.get_parameters(options))
