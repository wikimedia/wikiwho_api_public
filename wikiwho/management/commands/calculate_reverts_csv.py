# -*- coding: utf-8 -*-
"""
Example usage:
python manage.py calculate_reverts -i '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/tokens_in_lastrevisions_2.csv' -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats' -m 4 -s '1-2001' -e '1-2002'

"""
from os import mkdir, listdir
from os.path import exists, isfile
import logging
from time import strftime
import sys
import csv

from concurrent.futures import ProcessPoolExecutor, as_completed, ThreadPoolExecutor

from django.core.management.base import BaseCommand
from django.db import connection

from wikiwho.models import Revision, Article


def buildNetworkReverts(article_id, revisions):
    data = []
    # Iterate over each revision i,
    # starting by the first revision of the article.
    # for i in range(1, len(d[article]["rev_order"])):
    for i, rev_i_id in enumerate(revisions["rev_order"]):

        # Obtain meta-data of revision i.
        # rev_i_id = d[article]["rev_order"][i]
        rev_i = revisions["revs"][rev_i_id]
        s_outs = (set(rev_i["token-outs"]))
        s_ins = (set(rev_i["token-ins"]))

        # Iterate over previous revisions j, starting from i and backwards.
        # Loop to detect reverts from i to j.
        # for j in range(i-1, -1, -1):
        for j in range(i - 1, -1, -1):

            # Obtain meta-data of revision j.
            rev_j_id = revisions["rev_order"][j]
            rev_j = revisions["revs"][rev_j_id]

            # Count number of reverted actions from i to j.
            reverted_actions = 0

            # Detect reverts by deletion.
            if (len(s_outs) > 0):

                s1 = (set(rev_j["oadds"]) | set(rev_j["token-ins"]))

                # Revision i deleted content was created or re-introduced in j.
                intersection = s1 & s_outs
                if len(intersection) > 0:
                    reverted_actions += len(intersection)
                    s_outs -= intersection

            # Detect reverts by re-introduction.
            if (len(s_ins) > 0):
                s1 = set(rev_j["token-outs"])

                # Revision i re-introduced content was deleted in j.
                intersection = s1 & s_ins
                if len(intersection) > 0:
                    reverted_actions += len(intersection)
                    s_ins -= intersection

            # Check if i reverted actions from j.
            if (reverted_actions > 0):
                # TODO why not total actions of rev_i ??
                total_actions = len(rev_j["oadds"]) + len(rev_j["token-ins"]) + len(rev_j["token-outs"])

                data.append([article_id, rev_i_id, rev_j_id, reverted_actions, total_actions,
                             revisions["revs"][rev_i_id]["editor"],
                             revisions["revs"][rev_j_id]["editor"]])

            # Exit loop.
            if len(s_outs) == 0 and len(s_ins) == 0:
                break
    return data


def buildActionsPerRevision(article_id, article_content):
    # create a dict of revision of this article
    revisions = {"rev_order": [], "revs": {}}
    # TODO or get this data from other 2 csv files
    for rev in Revision.objects.filter(article_id=article_id).values_list('id', 'editor', 'timestamp').iterator():
        revisions["rev_order"].append(int(rev[0]))
        revisions["revs"].update({int(rev[0]): {"editor": rev[1], "oadds": [], "token-ins": [], "token-outs": []}})

    for token_data in article_content:
        # token_id, origin, inbound, outbound
        revisions["revs"][int(token_data[1])]["oadds"].append(int(token_data[0]))
        # inbounds
        for elem in token_data[2]:
            try:
                revisions["revs"][int(elem)]["token-ins"].append(int(token_data[0]))
            except:
                pass
        # outbounds
        for elem in token_data[3]:
            try:
                revisions["revs"][int(elem)]["token-outs"].append(int(token_data[0]))
            except:
                pass
    return revisions


def calculate_reverts(input_csv):
    print(input_csv)
    output_csv = input_csv + '.output.csv'
    header = "article,source,target,reverted_actions,total_actions,source_editor,target_editor".split(',')
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)

    with open(input_csv, newline='') as f:
        reader = csv.reader(f)
        article_id = None
        article_content = []
        for row in reader:
            # article_id,revision_id,token_id,str,origin,inbound,outbound
            if 'article_id' in row:
                continue
            # if next article in csv
            if article_id is not None and article_id != int(row[0]):
                revisions = buildActionsPerRevision(article_id, article_content)
                data = buildNetworkReverts(article_id, revisions)
                writer.writerows(data)

                article_id = int(row[0])
            else:
                # token_id, origin, inbound, outbound
                article_content.append([row[2], row[4], row[5], row[6]])
                article_id = int(row[0])
    return True


class Command(BaseCommand):
    help = '.'

    def add_arguments(self, parser):
        parser.add_argument('-f', '--folder', required=True, help='I/O folder where to get input csvs and '
                                                                  'to write logs and csv.')
        parser.add_argument('-m', '--max_workers', type=int, required=False,
                            help='Number of processors/threads to run parallel. '
                                 'Default is # csv files in given folder path.')
        parser.add_argument('-tpe', '--thread_pool_executor', action='store_true', default=False, required=False,
                            help='Use ThreadPoolExecutor, default is ProcessPoolExecutor')
        parser.add_argument('-l', '--limit', type=int, required=False,
                            help='Articles limit. Default is all articles in db.')
        # parser.add_argument('-sci', '--save_csv_intermediate', action='store_true', default=False, required=False,
        #                     help='Save updated persistence data into csv after each article is processed. '
        #                          'Default is False, so persistence data is saved when all articles is processed.')
        # parser.add_argument('-o', '--offset', type=int, required=False, help='Articles offset. Default is 0.')

    def handle(self, *args, **options):
        # folder for inputs/outputs
        folder = options['folder']
        folder = folder[:-1] if folder and folder.endswith('/') else folder

        # get input csv files, they will be processed concurrently
        input_csvs = []
        for i in listdir(folder):
            i_path = '{}/{}'.format(folder, i)
            if isfile(i_path) and i.endswith('.csv'):
                input_csvs.append(i_path)

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

        # get other user inputs
        max_workers = options['max_workers'] or len(input_csvs)  # limit number of concurrent jobs
        print('max_workers:', max_workers)
        limit = options['limit']
        if not limit:
            limit = Article.objects.count()
            connection.close()
            # NOTE: if we dont close the connection before starting the process pool, we get these 2 errors:
            # django.db.utils.OperationalError: SSL error: decryption failed or bad record mac
            # django.db.utils.OperationalError: SSL SYSCALL error: EOF detected
        print('limit:', limit)

        print('Start: Reverts at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
        with Executor(max_workers=max_workers) as executor:
            jobs = {}
            input_csvs_iter = iter(input_csvs)
            csvs_left = len(input_csvs)
            csvs_all = csvs_left
            while csvs_left:
                for input_csv in input_csvs_iter:
                    job = executor.submit(calculate_reverts, input_csv)
                    jobs[job] = input_csv
                    if len(jobs) == max_workers:  # limit number of jobs with max_workers
                        break

                for job in as_completed(jobs):
                    csvs_left -= 1
                    input_csv_file = jobs[job]
                    try:
                        data = job.result()
                    except Exception as exc:
                        logger.exception(input_csv_file)

                    # progress percentage
                    sys.stdout.write('\r{}-{:.3f}%'.format(csvs_left, ((csvs_all - csvs_left) * 100) / csvs_all))
                    del jobs[job]
        print('\nDone: Reverts at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
