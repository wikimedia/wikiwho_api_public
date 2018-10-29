# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py fill_notindexed_editor_tables -from 2001-01 -to 2002-01 -m 6 -log '' -lang 'en,de,eu'

Check wikiwho_api/cron/manage_editor_data.sh for more information how we use 3 editor data scripts each month.
"""
import glob
import pytz
import sys
import json
from os.path import join, basename, exists
from os import mkdir
from time import strftime, sleep
from datetime import datetime, timedelta
from simplejson import JSONDecodeError

from concurrent.futures import ProcessPoolExecutor, as_completed

from django.core.management.base import BaseCommand

from api.utils_pickles import get_pickle_folder
from api.handler import WPHandlerException
from base.utils_log import get_logger
from api_editor.utils_db import fill_notindexed_editor_tables


def fill_notindexed_editor_tables_base(pickle_path, from_ym, to_ym, language, update):
    retries = 6
    while retries:
        retries -= 1
        try:
            fill_notindexed_editor_tables(pickle_path, from_ym, to_ym, language, update)
            return
        except WPHandlerException as e:
            if e.code in ['00', '02']:
                # article does not exist on wp anymore
                # and invalid namespace (probably page was an article and then is moved at some point)
                # dont try to update it, process what we have
                update = False
                sleep(30)
                if not retries:
                    raise
            else:
                raise e
        except (UnboundLocalError, JSONDecodeError):
            sleep(30)
            if not retries:
                raise


class Command(BaseCommand):
    help = 'Generates editor data and fills the editor database per ym, editor, article.'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', required=False,
                            help='Pickles json file {"en": [list of page ids], "de" [], }. '
                                 'If not given, list is taken from relevant pickle folder for each language.')
        parser.add_argument('-from', '--from_ym', required=True,
                            help='Year-month to create data from [YYYY-MM]. Included.')
        parser.add_argument('-to', '--to_ym', required=True,
                            help='Year-month to create data until [YYYY-MM]. Not included.')
        parser.add_argument(
            '-lang', '--language', help="Wikipedia language. Ex: 'en' or 'en,eu,de'", required=True)
        parser.add_argument('-log', '--log_folder',
                            help='Folder where to write logs.', required=True)
        parser.add_argument('-m', '--max_workers', type=int, help='Number of processors/threads to run parallel. ',
                            required=True)
        parser.add_argument('-u', '--update', action='store_true',
                            help='Update pickles from WP api before generating editor data. Default is False.',
                            default=False, required=False)
        # parser.add_argument('-t', '--timeout', type=float, required=False,
        #                     help='Timeout value for each processor for analyzing articles [minutes]')
        # parser.add_argument('-c', '--check_exists', action='store_true', help='', default=False, required=False)

    def get_parameters(self, options):
        json_file = options['file'] or None
        from_ym = options['from_ym']
        from_ym = datetime.strptime(from_ym, '%Y-%m').replace(tzinfo=pytz.UTC)
        to_ym = options['to_ym']
        to_ym = datetime.strptime(
            to_ym, '%Y-%m').replace(tzinfo=pytz.UTC) - timedelta(seconds=1)
        languages = options['language'].split(',')
        max_workers = options['max_workers']
        update = options['update']
        return json_file, from_ym, to_ym, languages, max_workers, update

    def handle(self, *args, **options):
        json_file, from_ym, to_ym, languages, max_workers, update = self.get_parameters(
            options)

        print('Start at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
        print(max_workers, languages, from_ym, to_ym)
        # Concurrent process of pickles of each language to generate editor data
        for language in languages:
            # set logging
            log_folder = options['log_folder']
            if not exists(log_folder):
                mkdir(log_folder)
            logger = get_logger('fill_notindexed_editor_tables_{}_from_{}_{}_to_{}_{}'.
                                format(language, from_ym.year,
                                       from_ym.month, to_ym.year, to_ym.month),
                                log_folder, is_process=True, is_set=True, language=language)
            pickle_folder = get_pickle_folder(language)
            print('Start: {} - {} at {}'.format(language,
                                                pickle_folder, strftime('%H:%M:%S %d-%m-%Y')))

            if json_file:
                with open(json_file, 'r') as f:
                    pickles_dict = json.loads(f.read())
                    pickles_list = [join(pickle_folder, '{}.p'.format(
                        page_id)) for page_id in pickles_dict[language]]
                    pickles_all = len(pickles_list)
                    pickles_left = pickles_all
                    pickles_iter = iter(pickles_list)
            else:
                pickles_list = list(glob.iglob(join(pickle_folder, '*.p')))
                pickles_all = len(pickles_list)
                pickles_left = pickles_all
                pickles_iter = iter(pickles_list)
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                jobs = {}
                while pickles_left:
                    for pickle_path in pickles_iter:
                        page_id = basename(pickle_path)[:-2]
                        job = executor.submit(
                            fill_notindexed_editor_tables_base, pickle_path, from_ym, to_ym, language, update)
                        jobs[job] = page_id
                        if len(jobs) == max_workers:  # limit # jobs with max_workers
                            break

                    for job in as_completed(jobs):
                        pickles_left -= 1
                        page_id_ = jobs[job]
                        try:
                            data = job.result()
                        except Exception as exc:
                            logger.exception(
                                '{}-{}'.format(page_id_, language))

                        del jobs[job]
                        sys.stdout.write('\rPickles left: {} - Pickles processed: {:.3f}%'.
                                         format(pickles_left, ((pickles_all - pickles_left) * 100) / pickles_all))
                        break  # to add a new job, if there is any
            print('\nDone: {} - {} at {}'.format(language,
                                                 pickle_folder, strftime('%H:%M:%S %d-%m-%Y')))
        print('Done at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
