# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py generate_stats -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats' -m 4 -l 10
"""
from os import mkdir
from os.path import exists
import logging
from time import strftime
import sys
import csv

from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

from django.core.management.base import BaseCommand
from django.db import connection

from wikiwho.models import LastRevision
from wikiwho.utils_db import tokens_custom


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        # yield m+1, y
        yield '{}-{}'.format(m+1, y)


def generate_stats(last_rev_id, month_survived, year_survived, article_id):
    values_list = ['editor', 'timestamp']
    tokens = tokens_custom(last_rev_id, values_list, ordered=False, return_dict=False)
    """
    SELECT "wikiwho_token"."editor",
           "wikiwho_token"."timestamp"
    FROM "wikiwho_token"
    INNER JOIN "wikiwho_sentencetoken" ON ("wikiwho_token"."id" = "wikiwho_sentencetoken"."token_id")
    INNER JOIN "wikiwho_paragraphsentence" ON ("wikiwho_sentencetoken"."sentence_id" = "wikiwho_paragraphsentence"."sentence_id")
    INNER JOIN "wikiwho_revisionparagraph" ON ("wikiwho_paragraphsentence"."paragraph_id" = "wikiwho_revisionparagraph"."paragraph_id")
    WHERE "wikiwho_revisionparagraph"."revision_id" = %s
    """

    survived_org_adds = {}  # {'editor' : [survived_org_adds_all, survived_org_adds_this_month]
    persistence_data = {}
    for token_editor, token_timestamp in tokens:
        if token_editor in survived_org_adds:
            survived_org_adds[token_editor][0] += 1
        else:
            survived_org_adds[token_editor] = [1, 0]
        token_month_added = token_timestamp.date().month
        token_year_added = token_timestamp.date().year
        if token_month_added == month_survived and token_year_added == year_survived:
            # if token originally added in current/survived month-year
            survived_org_adds[token_editor][1] += 1
        month_year_added = '{}-{}'.format(token_month_added, token_year_added)
        if month_year_added in persistence_data:
            persistence_data[month_year_added] += 1
        else:
            persistence_data[month_year_added] = 1

    # INSERT INTO table VALUES (1,1),(1,2),(1,3),(2,1);
    q = """
        INSERT INTO "wikiwho_survivedoriginaladds" ("year",
                                                    "month",
                                                    "article_id",
                                                    "editor",
                                                    "survived_org_adds",
                                                    "survived_org_adds_all")
        VALUES {};
        """
    survived_org_adds_list = [(year_survived, month_survived, article_id, editor, soa[1], soa[0])
                              for editor, soa in survived_org_adds.items()]
    q = q.format(str(survived_org_adds_list)[1:-1])
    # print(q)
    with connection.cursor() as cursor:
        cursor.execute(q)
        # rows = cursor.fetchall()
    return persistence_data


class Command(BaseCommand):
    help = 'Generates stats for survived original adds per month-year per editor per article'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--folder', required=True,
                            help='Folder where to write logs and csv.')
        parser.add_argument('-m', '--max_workers', type=int, required=True,
                            help='Number of processors/threads to run parallel. '
                                 'Default is # compressed files in given folder path.')
        parser.add_argument('-ppe', '--process_pool_executor', action='store_true', default=False, required=False,
                            help='Use ProcessPoolExecutor, default is ThreadPoolExecutor')
        parser.add_argument('-l', '--limit', type=int, required=False,
                            help='Queryset limit. Default is all.')
        parser.add_argument('-o', '--offset', type=int, required=False, help='Queryset offset. Default is 0.')

    def handle(self, *args, **options):
        folder = options['folder']
        folder = folder[:-1] if folder and folder.endswith('/') else folder
        log_folder = '{}/{}'.format(folder, 'logs')
        if not exists(log_folder):
            mkdir(log_folder)

        is_ppe = options['process_pool_executor']
        if is_ppe:
            Executor = ProcessPoolExecutor
            format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
        else:
            Executor = ThreadPoolExecutor
            format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'

        logger = logging.getLogger('future_log')
        file_handler = logging.FileHandler('{}/oadds_stats_at_{}.log'.format(log_folder,
                                                                             strftime("%Y-%m-%d-%H:%M:%S")))
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(format_)
        file_handler.setFormatter(formatter)
        logger.handlers = [file_handler]

        max_workers = options['max_workers']
        print(max_workers)
        print('Start: O adds stats at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
        # calculate offset, limit and total number of last rev ids to be processed
        limit = options['limit']
        offset = options['offset'] or 0
        last_revs_data = LastRevision.objects.values_list('id', 'timestamp', 'article_id')
        if limit and offset:
            last_revs_data = last_revs_data[offset:limit]
            last_revs_all = limit - offset
        elif limit:
            last_revs_data = last_revs_data[:limit]
            last_revs_all = limit - 0
        elif offset:
            last_revs_data = last_revs_data[offset:]
            last_revs_all = LastRevision.objects.count() - offset
        else:
            last_revs_all = LastRevision.objects.count()
        last_revs_data = last_revs_data.iterator()
        last_revs_left = last_revs_all

        # create empty persistence_data dict
        persistence_data = {}
        for m_y_added in month_year_iter(1, 2001, 11, 2016):
            persistence_data[m_y_added] = {}
            for m_y_survived in month_year_iter(1, 2001, 11, 2016):
                persistence_data[m_y_added][m_y_survived] = 0

        # calculate survived original adds and persistence table data concurrently
        with Executor(max_workers=max_workers) as executor:
            jobs = {}
            while last_revs_left:
                for last_rev_id, timestamps, article_id in last_revs_data:
                    month_survived = timestamps.date().month
                    year_survived = timestamps.date().year
                    # print(last_rev_data)
                    job = executor.submit(generate_stats, last_rev_id, month_survived, year_survived, article_id)
                    jobs[job] = '{}-{}-{}-{}'.format(article_id, last_rev_id, month_survived, year_survived)
                    if len(jobs) == max_workers:  # limit # jobs with max_workers
                        break

                for job in as_completed(jobs):
                    last_revs_left -= 1
                    article_rev_id = jobs[job]
                    try:
                        data = job.result()
                        # add data into persistence_data dict
                        month_year_survived = '-'.join(article_rev_id.split('-')[2:])
                        for month_year_added, survived_o_adds in data.items():
                            persistence_data[month_year_added][month_year_survived] += survived_o_adds
                    except Exception as exc:
                        logger.exception(article_rev_id)

                    # progress percentage
                    sys.stdout.write('\r{:.3f}%'.format(((last_revs_all - last_revs_left) * 100) / last_revs_all))
                    del jobs[job]
                    break  # to add a new job, if there is any

        # print(persistence_data)
        # write persistence_data into csv
        with open('{}/persistence_data_{}_{}.csv'.format(folder, offset, limit or last_revs_all), 'w') as f:
            w = csv.DictWriter(f, ['month_added'] + list(month_year_iter(1, 2001, 11, 2016)))
            w.writeheader()
            for m_y_added in month_year_iter(1, 2001, 11, 2016):
                persistence_data[m_y_added].update({'month_added': m_y_added})
                w.writerow(persistence_data[m_y_added])
        print('\nDone: O adds stats at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
