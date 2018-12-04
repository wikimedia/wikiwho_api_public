# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py empty_notindexed_editor_tables -m 3 -log '' -lang 'en,de,eu'
"""
import sys
from time import strftime
from os.path import exists
from os import mkdir

from concurrent.futures import ProcessPoolExecutor, as_completed

from django.core.management.base import BaseCommand

from base.utils_log import get_logger
from api_editor.utils_db import empty_notindexed_editor_tables


def empty_notindexed_editor_tables_base(language, log_folder):

    try:
        empty_notindexed_editor_tables(language)
    except Exception as e:
        logger = get_logger('empty_notindexed_editor_tables_{}'.format(
            language), log_folder, is_process=True, is_set=False, language=language)
        logger.exception('{}'.format(language))


class Command(BaseCommand):
    help = 'Delete all rows inside not indexed editor tables.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-lang', '--language', help="Wikipedia language. Ex: 'en' or 'en,eu,de'", required=True)
        parser.add_argument('-log', '--log_folder', help='Folder where to write logs. Default is folder of xml folder',
                            required=True)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of processors/threads to run parallel. ',
                            required=True)

    def handle(self, *args, **options):
        empty_notindexed_editor_tables(
            languages=options['language'].split(','),
            max_workers=options['max_workers'], log_folder=options['log_folder'])


def empty_notindexed_editor_tables_batch(languages, max_workers, log_folder):
    if not exists(log_folder):
        mkdir(log_folder)

    print('Start at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
    print(max_workers, languages, log_folder)
    languages_iter = iter(languages)
    languages_all = len(languages)
    languages_left = languages_all
    if max_workers < 1:
        for language in languages_iter:
            empty_notindexed_editor_tables_base(
                language, log_folder)
            print(f'{language} not indexed table has been emptied')
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            jobs = {}
            while languages_left:
                for language in languages_iter:
                    job = executor.submit(
                        empty_notindexed_editor_tables_base, language, log_folder)
                    jobs[job] = language
                    if len(jobs) == max_workers:  # limit # jobs with max_workers
                        break

                for job in as_completed(jobs):
                    languages_left -= 1
                    language_ = jobs[job]
                    try:
                        data = job.result()
                    except Exception as exc:
                        logger = get_logger('empty_notindexed_editor_tables', log_folder,
                                            is_process=True, is_set=True)
                        logger.exception('{}'.format(language_))

                    del jobs[job]
                    sys.stdout.write('\rPickles left: {} - Pickles processed: {:.3f}%'.
                                     format(languages_left, ((languages_all - languages_left) * 100) / languages_all))
                    break  # to add a new job, if there is any
    print('\nDone: {} - at {}'.format(language, strftime('%H:%M:%S %d-%m-%Y')))
