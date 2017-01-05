# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py generate_stats_csv -i '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/tokens_in_lastrevisions_2.csv' -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats' -m 4 -s '1-2001' -e '1-2002'

split -d --line-bytes=1080M tokens_in_lastrevisions.csv tokens_in_lastrevisions/random/tokens_in_lastrevisions.csv_
"""
from os import mkdir
from os.path import exists
import logging
from time import strftime
import sys
import csv
from datetime import datetime
import pytz

from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils.dateparse import parse_datetime

from wikiwho.models import Revision, Article


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        # yield m+1, y
        yield '{}-{}'.format(m+1, y)


def generate_stats(article_id, article_token_data, m_start, y_start, m_end, y_end):
    # create a dict of revision of this article
    revisions = {}  # { rev_id: [editor, timestamp], ...}
    for rev in Revision.objects.filter(article_id=article_id).values_list('id', 'editor', 'timestamp').iterator():
        if rev[0] not in revisions:
            revisions[rev[0]] = [rev[1], rev[2]]

    # fill the data of months that article has revisions
    # survived_org_adds per article per editor per month-year
    survived_org_adds = {}  # {my_surv: {'editor' : [survived_org_adds_all, survived_org_adds_this_month], ...}, ...}
    # persistence_data only per month-year: tokens added in this m-y and survived of them through history
    persistence_data = {}  # {my_added_1: {my_surv_1: x, my_surv_2: y, ...}, my_added_2: {...}, ...}
    last_rev_ts_curr = None  # timestamp of current last revision from token data
    my_start = datetime(y_start, m_start, 1, tzinfo=pytz.timezone('UTC'))
    my_end = datetime(y_end, m_end, 1, tzinfo=pytz.timezone('UTC'))
    for last_rev_ts, label_rev_id in article_token_data:
        # if next last rev in article
        if last_rev_ts_curr != last_rev_ts:
            last_rev_ts_curr = last_rev_ts
            last_rev_ts_ = parse_datetime(last_rev_ts)
            month_survived = last_rev_ts_.date().month
            year_survived = last_rev_ts_.date().year
            month_year_survived = '{}-{}'.format(month_survived, year_survived)

        if not (my_end > last_rev_ts_ >= my_start):
            # skip token data out of this month-year range
            continue

        # survived_org_adds
        if month_year_survived not in survived_org_adds:
            survived_org_adds[month_year_survived] = {}
        token_editor = revisions[label_rev_id][0]
        token_timestamp = revisions[label_rev_id][1]
        if token_editor in survived_org_adds[month_year_survived]:
            survived_org_adds[month_year_survived][token_editor][0] += 1
        else:
            survived_org_adds[month_year_survived][token_editor] = [1, 0]
        token_month_added = token_timestamp.date().month
        token_year_added = token_timestamp.date().year
        if token_month_added == month_survived and token_year_added == year_survived:
            # if token originally added in current/survived month-year
            survived_org_adds[month_year_survived][token_editor][1] += 1
        # persistence_data
        token_month_year_added = '{}-{}'.format(token_month_added, token_year_added)
        if token_month_year_added in persistence_data:
            if month_year_survived in persistence_data[token_month_year_added]:
                persistence_data[token_month_year_added][month_year_survived] += 1
            else:
                persistence_data[token_month_year_added][month_year_survived] = 1
        else:
            persistence_data[token_month_year_added] = {month_year_survived: 1}

    # fill the data of months that article doesn't have any revisions
    last_my_survived = None
    for month_year_survived in month_year_iter(m_start, y_start, m_end, y_end):
        if month_year_survived in survived_org_adds:
            last_my_survived = month_year_survived
        else:
            if last_my_survived:
                # if article exists in this month-year and has no rev in this month
                # take data from latest month
                survived_org_adds[month_year_survived] = {}
                for t_editor in survived_org_adds[last_my_survived]:
                    # if there is no rev in this month, o_added in this month must be zero
                    # o_added_all will be taken from latest revision
                    survived_org_adds[month_year_survived].\
                        update({t_editor: [survived_org_adds[last_my_survived][t_editor][0],
                                           0]})
                for token_month_year_added in persistence_data:
                    # if no edits in this month, survived tokens from latest month still live in this month
                    if last_my_survived in persistence_data[token_month_year_added]:
                        # if not(persistence_data[token_month_year_added][last_my_survived] > 0):
                        #     print(persistence_data[token_month_year_added][last_my_survived])
                        # if not(persistence_data[token_month_year_added].get(month_year_survived) is None):
                        #     print(persistence_data[token_month_year_added].get(month_year_survived))
                        # assert persistence_data[token_month_year_added][last_my_survived] > 0
                        # assert persistence_data[token_month_year_added].get(month_year_survived) is None
                        persistence_data[token_month_year_added][month_year_survived] = \
                            persistence_data[token_month_year_added][last_my_survived]

    survived_org_adds_list = []
    for month_year_survived in survived_org_adds:
        month_survived, year_survived = month_year_survived.split('-')
        for editor, soa in survived_org_adds[month_year_survived].items():
            # print((year_survived, month_survived, article_id, editor, soa[1], soa[0]))
            survived_org_adds_list.append((year_survived, month_survived, article_id, editor, soa[1], soa[0]))
    if survived_org_adds_list:
        # INSERT INTO table VALUES (1,1),(1,2),(1,3),(2,1);
        # make an insert query for each month-year data of article
        q = """
            INSERT INTO "wikiwho_survivedoriginaladds" ("year",
                                                        "month",
                                                        "article_id",
                                                        "editor",
                                                        "survived_org_adds",
                                                        "survived_org_adds_all")
            VALUES {};
            """
        query = q.format(str(survived_org_adds_list)[1:-1])
        # print(query)
        with connection.cursor() as cursor:
            cursor.execute(query)
    # connection.close()
    return persistence_data


def write_persistence_date_into_csv(persistence_data, folder, limit, m_start_default, y_start_default, m_end, y_end):
    with open('{}/persistence_data_{}.csv'.format(folder, limit), 'w') as f:
        w = csv.DictWriter(f, ['month_added'] + list(
            month_year_iter(m_start_default, y_start_default, m_end, y_end)))
        w.writeheader()
        for m_y_added in month_year_iter(m_start_default, y_start_default, m_end, y_end):
            persistence_data[m_y_added].update({'month_added': m_y_added})
            w.writerow(persistence_data[m_y_added])


class Command(BaseCommand):
    help = 'Generates stats for survived original adds of each editor per month-year per article.'

    def add_arguments(self, parser):
        parser.add_argument('-i', '--input_file', required=True,
                            help='Input csv file which contains all content token data per article per month-year.')
        parser.add_argument('-f', '--folder', required=True, help='Folder where to write logs and csv.')
        parser.add_argument('-m', '--max_workers', type=int, required=True,
                            help='Number of processors/threads to run parallel. '
                                 'Default is # compressed files in given folder path.')
        parser.add_argument('-tpe', '--thread_pool_executor', action='store_true', default=False, required=False,
                            help='Use ThreadPoolExecutor, default is ProcessPoolExecutor')
        parser.add_argument('-s', '--my_start', required=False, help='Month-year start. Default: 1-2001.')
        parser.add_argument('-e', '--my_end', required=False, help='Month-year end. Default: 11-2016.')
        parser.add_argument('-l', '--limit', type=int, required=False,
                            help='Articles limit. Default is all articles in db.')
        parser.add_argument('-sci', '--save_csv_intermediate', action='store_true', default=False, required=False,
                            help='Save updated persistence data into csv after each article is processed. '
                                 'Default is False, so persistence data is saved when all articles is processed.')
        # parser.add_argument('-o', '--offset', type=int, required=False, help='Articles offset. Default is 0.')

    def handle(self, *args, **options):
        # folder for outputs
        folder = options['folder']
        folder = folder[:-1] if folder and folder.endswith('/') else folder

        # decide to use ThreadPoolExecutor or ProcessPoolExecutor
        is_ppe = not options['thread_pool_executor']
        if is_ppe:
            Executor = ProcessPoolExecutor
            format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
        else:
            print('WARNING: Because of python GIL (global interpreter lock) threads '
                  'might not work concurrent for this cpu-bound task!')
            Executor = ThreadPoolExecutor
            format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'

        # set logging into file
        log_folder = '{}/{}'.format(folder, 'logs')
        if not exists(log_folder):
            mkdir(log_folder)
        logger = logging.getLogger('future_log')
        file_handler = logging.FileHandler('{}/oadds_stats_at_{}.log'.format(log_folder,
                                                                             strftime("%Y-%m-%d-%H:%M:%S")))
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(format_)
        file_handler.setFormatter(formatter)
        logger.handlers = [file_handler]

        # decide to month-year range
        m_start_default = 1
        y_start_default = 2001
        m_end_default = 11
        y_end_default = 2016
        my_start = options['my_start'] or '{}-{}'.format(m_start_default, y_start_default)
        m_start, y_start = map(int, my_start.split('-'))
        my_end = options['my_end'] or '{}-{}'.format(m_end_default, y_end_default)
        m_end, y_end = map(int, my_end.split('-'))
        print(m_start, y_start, m_end, y_end)

        # get other user inputs
        max_workers = options['max_workers']  # limit number of concurrent jobs
        print('max_workers:', max_workers)
        limit = options['limit']
        if not limit:
            limit = Article.objects.count()
            connection.close()
            # NOTE: if we dont close the connection before starting the process pool, we get these 2 errors:
            # django.db.utils.OperationalError: SSL error: decryption failed or bad record mac
            # django.db.utils.OperationalError: SSL SYSCALL error: EOF detected
        print('limit:', limit)
        # if limit < max_workers:
        #     max_workers = limit
        save_csv_intermediate = options['save_csv_intermediate']

        print('Start: O adds stats at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))

        # create empty persistence_data dict
        # persistence_data holds number of survived tokens per month-year, when tokens are added through whole history
        persistence_data = {}
        for m_y_added in month_year_iter(m_start_default, y_start_default, m_end, y_end):
            persistence_data[m_y_added] = {}
            for m_y_survived in month_year_iter(m_start_default, y_start_default, m_end, y_end):
                persistence_data[m_y_added][m_y_survived] = 0

        # calculate survived original adds and persistence table data concurrently
        with Executor(max_workers=max_workers) as executor:
            jobs = {}
            with open(options['input_file'], newline='') as f:
                reader = csv.reader(f)
                article_id = None
                article_data = []  # [[last_rev_timestamp, label_revision_id], ...]
                # sent_counter = 0
                finished_counter = 0
                # offset = options['offset'] or 0
                while True:
                    for row in reader:
                        if 'article_id' in row:
                            continue
                        # FIXME
                        # if sent_counter < offset:
                        #     continue
                        # if finished_counter >= limit:
                        #     break
                        # if next article in csv
                        if article_id is not None and article_id != int(row[0]):
                            # sent_counter += 1
                            job = executor.submit(generate_stats, article_id, article_data, m_start, y_start, m_end, y_end)
                            jobs[job] = article_id
                            # print(article_id, int(row[0]), len(article_data), len(jobs))
                            article_data = [[row[1], int(row[4])]]
                            article_id = int(row[0])
                            if len(jobs) == max_workers:  # limit number of jobs with max_workers
                                break
                        else:
                            article_data.append([row[1], int(row[4])])
                            article_id = int(row[0])

                    if len(article_data) > 1:
                        # if last article in csv
                        job = executor.submit(generate_stats, article_id, article_data, m_start, y_start, m_end, y_end)
                        jobs[job] = article_id
                        # print(article_id, len(article_data), len(jobs))
                        article_data = []

                    for job in as_completed(jobs):
                        finished_counter += 1
                        job_article_id = jobs[job]
                        try:
                            data = job.result()
                            # add data into persistence_data dict
                            for month_year_added, survived_dict in data.items():
                                for month_year_survived, survived_o_adds in survived_dict.items():
                                    persistence_data[month_year_added][month_year_survived] += survived_o_adds
                            if save_csv_intermediate:
                                write_persistence_date_into_csv(persistence_data, folder, limit, m_start_default,
                                                                y_start_default, m_end, y_end)
                        except Exception as exc:
                            logger.exception(job_article_id)

                        # progress percentage
                        sys.stdout.write('\r{}-{:.3f}%'.format(finished_counter, (finished_counter * 100) / limit))
                        del jobs[job]
                        if article_data:
                            break  # to add a new job, if there is any

                    if not article_data:
                        break
        write_persistence_date_into_csv(persistence_data, folder, limit, m_start_default, y_start_default, m_end, y_end)
        print('\nDone: O adds stats at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))


"""
COPY (
SELECT "wikiwho_lastrevision"."article_id",
"wikiwho_lastrevision"."timestamp",
"wikiwho_lastrevision"."id",
"wikiwho_token"."token_id",
"wikiwho_token"."label_revision_id",
"wikiwho_token"."value"
FROM "wikiwho_token"
JOIN "wikiwho_sentencetoken" ON ("wikiwho_token"."id" = "wikiwho_sentencetoken"."token_id")
JOIN "wikiwho_paragraphsentence" ON ("wikiwho_sentencetoken"."sentence_id" = "wikiwho_paragraphsentence"."sentence_id")
JOIN "wikiwho_revisionparagraph" ON ("wikiwho_paragraphsentence"."paragraph_id" = "wikiwho_revisionparagraph"."paragraph_id")
JOIN "wikiwho_lastrevision" ON ("wikiwho_revisionparagraph"."revision_id" = "wikiwho_lastrevision"."id")
WHERE "wikiwho_lastrevision"."article_id" IN (2161298, 8170003, 6753648, 9358, 222198)
ORDER BY article_id, timestamp)
TO '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/tokens_in_lastrevisions_2.csv'  DELIMITER ',' CSV HEADER;
"""