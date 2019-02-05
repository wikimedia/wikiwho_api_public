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
import logging
from itertools import islice

from os.path import join, basename, exists, getmtime
from os import mkdir
from time import strftime, sleep, ctime
from datetime import datetime, timedelta, date
from simplejson import JSONDecodeError

from concurrent.futures import ProcessPoolExecutor, as_completed

from django.core.management.base import BaseCommand
from django.conf import settings

from api.utils_pickles import get_pickle_folder
from api.handler import WPHandlerException
from api.utils import get_latest_revision_timestamps
from api.wp_connection import MediaWiki

from base.utils_log import get_logger, get_stream_base_logger
from api_editor.utils_db import fill_notindexed_editor_tables


def fill_notindexed_editor_tables_base(pickle_path, from_ym, to_ym, language, update):
    retries = 6

    while retries:
        retries -= 1
        try:
            if update or not exists (pickle_path) \
                    or (pytz.UTC.localize(datetime.fromtimestamp(getmtime(pickle_path))) >= from_ym):
                fill_notindexed_editor_tables(
                    pickle_path, from_ym, to_ym, language, update)
            return
        except WPHandlerException as e:
            if e.code in ['00', '02']:
                # article does not exist on wp anymore
                # and invalid namespace (probably page was an article and then is moved at some point)
                # dont try to update it, process what we have
                if update:
                    retries += 1

                    # if we are not updating there is no need to do the sleep
                    update = False
                else:
                    if not retries:
                        raise e
                    sleep(30)
            else:
                raise e
        except (UnboundLocalError, JSONDecodeError) as exc:
            sleep(30)
            if not retries:
                raise exc


def non_updated_pickles(language, pickle_folder, _all, logger, log_folder):
    # utcfromtimestamp gives the universal time of the file, it takes into consideration
    # if the file was created during +01:00 (winter time) or +02:00 (summer
    # time) for Germany

    json_folder = join(log_folder, language)
    _date = strftime("%Y-%m-%d")
    if not exists(json_folder):
        mkdir(json_folder)

    _files = {
        basename(p_path)[:-2]: pytz.UTC.localize(datetime.utcfromtimestamp(getmtime(p_path)))
        for p_path in glob.iglob(join(pickle_folder, '*.p'))
    }

    with open(join(json_folder, f'{_date}-files_index.json'), 'w') as fp:
        json.dump(_files, fp, default=str)

    total_files = len(_files)
    print(f'Total files in the directory: {total_files}')

    _index = {}
    _found = {}
    _new = {}
    _to_update = {}
    _updated = {}

    if total_files == 0:
        logger.error(f"No pickles found in the directory: {pickle_folder}")
    else:
        try:
            for req, result in get_latest_revision_timestamps(language, _all, logger):
                for page in result['pages']:
                    pageid = str(page['pageid'])
                    if pageid in _index:
                        logger.warning(f"ERROR! The page id {pagid} exists already "
                                       "(found twice in Wikipedia!)")

                    _index[pageid] = {
                        'title': page['title'],
                        'ts': pytz.UTC.localize(MediaWiki.parse_date(
                            page['revisions'][0]['timestamp']))
                    }
                    if pageid in _files:
                        _index[pageid]['ts_file'] = _files.pop(pageid)
                        _found[pageid] = _index[pageid]
                        if _index[pageid]['ts_file'] < _index[pageid]['ts']:
                            _to_update[pageid] = _index[pageid]
                            yield pageid, True
                        else:
                            _updated[pageid] = _index[pageid]
                            yield pageid, False
                    else:
                        _new[pageid] = _index[pageid]
                        if not (settings.DEBUG or settings.TESTING):
                            yield pageid, True

                    sys.stdout.write(
                        ('\rLeft: {} ({:.3f}%) Processed: {} New: {} Found: {} ({:.3f}%) '
                            'Outdated: {} Updated: {} Current Page ID: {} ').
                        format(
                            total_files - len(_found),
                            (total_files - len(_found)) * 100 / total_files,
                            len(_index),
                            len(_new),
                            len(_found),
                            len(_found) * 100 / total_files,
                            len(_to_update),
                            len(_updated), pageid))
        except Exception as exc:
            logger.exception("Failure iterating over the latest revision timestamps\n"
                             f"The las page processed page ({pageid}) was {_index[pageid]}")

    logger.info(f"""
        ---------------------------------------------------------------------------------------------
        REPORT for {language} LANGUAGE:
        Total pages found in Wikipedia: {len(_index)}
        Total files found in the pickles directory: {total_files}
        Files in the pickles directory NOT FOUND in Wikipedia: {len(_files)}
            Examples: {str(list(islice(_files, 10)))}

        Files in the pickles directory FOUND in Wikipedia: {len(_found)}
            Examples: {str(list(islice(_found, 10)))}
        
        New Files in Wikipedia (not found in pickles directory): {len(_new)}
            Examples: {str(list(islice(_new, 10)))}
        
        Number of files that required an update (based on file modification date): {len(_to_update)}
            Examples: {str(list(islice(_to_update, 10)))}

        Number of files that were already updated (based on file modification date): {len(_updated)}
            Examples: {str(list(islice(_updated, 10)))}

        You can find the full list in the {json_folder}
        ---------------------------------------------------------------------------------------------
        """)

    with open(join(json_folder, f'{_date}-new.json'), 'w') as fp:
        json.dump(_new, fp, default=str)

    with open(join(json_folder, f'{_date}-not_in_wikipedia.json'), 'w') as fp:
        json.dump(_files, fp, default=str)

    with open(join(json_folder, f'{_date}-needed_update.json'), 'w') as fp:
        json.dump(_to_update, fp, default=str)


def fill_notindexed_editor_tables_batch(from_ym, to_ym, languages, max_workers, log_folder):
    # set logging
    if not exists(log_folder):
        mkdir(log_folder)

    parallel = max_workers >= 1
    logger = get_logger('fill_notindexed_editor_tables',
                        log_folder, is_process=parallel, is_set=True, level=logging.INFO,
                        descriptor=f'From:{from_ym.date()} To:{to_ym.date()}')
    print('Start at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))
    print(f"Workers: {max_workers} - Languages: {languages} - From: {from_ym} - To: {to_ym}")

    # Concurrent process of pickles of each language to generate editor data
    for language in languages:
        logger.info(f"Start processing NOT INDEXED tables for {language}")

        pickle_folder = get_pickle_folder(language)
        non_updated_pickles_iter = non_updated_pickles(
            language, pickle_folder, True, logger, log_folder)

        print('Start: {} - {} at {}'.format(language,
                                            pickle_folder, strftime('%H:%M:%S %d-%m-%Y')))

        if not parallel:
            for pageid, update in non_updated_pickles_iter:
                try:
                    fill_notindexed_editor_tables_base(
                        join(pickle_folder, f'{pageid}.p'),
                        from_ym, to_ym, language, update)
                except Exception as exc:
                    logger.exception(
                        '{}-{}'.format(pageid, language))
        else:
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                jobs = {}
                all_jobs_sent = False
                sent_jobs = 0
                processed_jobs = 0

                while (not all_jobs_sent) or (processed_jobs < sent_jobs):

                    # assume is over, but if there is pickles, set to False
                    all_jobs_sent = True

                    for pageid, update in non_updated_pickles_iter:
                        # there is at least the current job, loop again
                        all_jobs_sent = False

                        pickle_path = join(pickle_folder, f'{pageid}.p')
                        job = executor.submit(
                            fill_notindexed_editor_tables_base, pickle_path, from_ym, to_ym,
                            language, update)
                        sent_jobs += 1
                        jobs[job] = pageid
                        if len(jobs) == max_workers:  # limit # jobs with max_workers
                            break

                    for job in as_completed(jobs):
                        pageid = jobs[job]
                        try:
                            processed_jobs += 1
                            data = job.result()
                        except Exception as exc:
                            logger.exception(
                                '{}-{}'.format(pageid, language))

                        del jobs[job]
                        break  # to add a new job, if there is any
        print('\nDone: {} - {} at {}'.format(language,
                                             pickle_folder, strftime('%H:%M:%S %d-%m-%Y')))
    print('Done at {}'.format(strftime('%H:%M:%S %d-%m-%Y')))


class Command(BaseCommand):
    help = 'Generates editor data and fills the editor database per ym, editor, article.'

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
        fill_notindexed_editor_tables_batch(*self.get_parameters(options))
