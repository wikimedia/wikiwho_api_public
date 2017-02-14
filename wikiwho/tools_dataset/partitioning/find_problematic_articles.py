# -*- coding: utf-8 -*-
"""
Example usage:
1) python wikiwho/tools_dataset/partitioning/find_problematic_articles.py -i '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/dataset' -d '' -m 2
2) python manage.py generate_articles_from_wp_xmls -p '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/' -j '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/dataset/tokens/output' -m 2 -w -c
3) python wikiwho/tools_dataset/partitioning/replace_content_in_partition.py -o '../partitions' -i '../csv' -m 2 -d 'cd'
"""
from collections import defaultdict
from os import mkdir, listdir
from os.path import exists, isfile
import logging
from time import strftime
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys
import csv
import json
import argparse

from django.utils.dateparse import parse_datetime


def find_problematic_articles(tokens_file, part_number, revisions_file, log_folder):
    part_str = 'part_{}'.format(part_number)
    logger = logging.getLogger(part_str)
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                part_str,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    problematic_articles = []
    try:
        # get list of revision ids per article id
        revisions_dict = defaultdict(dict)
        with open(revisions_file, newline='') as f:
            header = next(f)  # page_id,rev_id,timestamp,editor
            for line in f:
                row = line.split(',')
                revisions_dict[str(row[0])].update({str(row[1]): parse_datetime(row[2])})

        with open(tokens_file, newline='') as f:
            reader = csv.reader(f, delimiter=',')
            problematic = False
            article_id = None
            for row in reader:
                if article_id and row[0] != article_id:
                    # if new article, reset problematic flag
                    problematic = False
                article_id = row[0]
                if problematic:
                    continue
                ins = row[5][1:-1]
                ins = ins.split(',') if ins else []
                outs = row[6][1:-1]
                outs = outs.split(',') if outs else []
                # len diff of in and outs must be 0 or 1
                if not (0 <= len(outs) - len(ins) <= 1):
                    problematic = True
                    problematic_articles.append(['', row[0]])
                    continue
                # ins must not include spam revisions
                for in_ in ins:
                    if in_ not in revisions_dict[row[0]]:
                        problematic = True
                        problematic_articles.append(['', row[0]])
                        break
                if problematic:
                    continue
                # outs must not include spam revisions
                for out_ in outs:
                    if out_ not in revisions_dict[row[0]]:
                        problematic = True
                        problematic_articles.append(['', row[0]])
                        break
                if problematic:
                    continue
                # check timestamp cond
                for o, i in zip(outs, ins):
                    ts_diff = (revisions_dict[row[0]][i] - revisions_dict[row[0]][o]).total_seconds()
                    if ts_diff < 0:
                        # logger.error('ts_diff 1:{} - {} - {} - {}'.format(ts_diff, row[0], len(ins), len(outs)))
                        problematic = True
                        problematic_articles.append(['', row[0]])
                        break
                if problematic:
                    continue
                if len(outs) > len(ins) and ins:
                    ts_diff = (revisions_dict[row[0]][outs[-1]] - revisions_dict[row[0]][ins[-1]]).total_seconds()
                    if ts_diff < 0:
                        # logger.error('ts_diff 2:{}'.format(ts_diff))
                        problematic = True
                        problematic_articles.append(['', row[0]])

    except Exception as e:
        logger.exception(part_str)
    return problematic_articles


def get_dumps_dict(dumps_folder):
    dumps_dict = {}
    for f in listdir(dumps_folder):
        if not isfile(dumps_folder+'/'+f) or not f.endswith('.7z'):
            continue
        pos = f.find("xml")
        from_to = f[pos+4:-3]
        (_, from_, to_) = from_to.split("p")
        from_ = int(from_)
        to_ = int(to_)
        assert to_ > from_
        dumps_dict.update({(from_, to_): f})
    return dumps_dict


def get_dump_file(article_id, dumps_dict):
    for (low, high) in dumps_dict.keys():
        if high >= article_id >= low:
            return dumps_dict[(low, high)]
    print("Article id", str(article_id), " not found in dump")


def get_args():
    parser = argparse.ArgumentParser(description='Find articles with problematic in and outs.')
    parser.add_argument('-i', '--input_folder', required=True, help='Folder of partitions.', )
    parser.add_argument('-d', '--dumps_folder', required=True, help='Folder of xml dumps.', )
    parser.add_argument('-m', '--max_workers', type=int, help='Number of processors/threads to run parallel. '
                                                              'Default is # compressed files in given folder path.',
                        required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    input_folder = args.input_folder
    input_folder = input_folder[:-1] if input_folder.endswith('/') else input_folder

    partitions = []
    tokens_folder = '{}/tokens'.format(input_folder)
    for i in listdir(tokens_folder):
        if not isfile('{}/{}'.format(tokens_folder, i)) or not i.endswith('.csv'):
            continue
        part_number = i.split('-part')[1].split('-')[0]
        revisions_folder = '{}/revisions'.format(input_folder)
        for revisions_file in listdir(revisions_folder):
            if '-part{}-'.format(part_number) in revisions_file:
                break
        # tokens file path, part number, revisions file path
        partitions.append(['{}/{}'.format(tokens_folder, i), part_number,
                           '{}/{}'.format(revisions_folder, revisions_file)])
    # print(partitions)

    # dumps
    dumps_folder = args.dumps_folder
    dumps_folder = dumps_folder[:-1] if dumps_folder.endswith('/') else dumps_folder
    dumps_dict = get_dumps_dict(dumps_folder)

    # Set output folder
    output_folder = '{}/output'.format(tokens_folder)
    # print(output_folder)
    if not exists(output_folder):
        mkdir(output_folder)
    output_json = '{}/problematic_articles.json'.format(output_folder, )
    problematic_articles_dict = {}
    with open(output_json, 'w') as f:
        json.dump(problematic_articles_dict, f)

    # Set logging
    log_folder = '{}/{}'.format(tokens_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)
    logger = logging.getLogger('future_log')
    file_handler = logging.FileHandler('{}/problematic_articles_at_{}.log'.format(log_folder,
                                                                                  strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]

    # Get max number of concurrent workers
    max_workers = args.max_workers
    print('max_workers:', max_workers, 'partitions:', len(partitions))

    csv.field_size_limit(sys.maxsize)
    print('Start: Find problematic articles at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        files_all = len(partitions)
        files_left = files_all
        files_iter = iter(partitions)

        while files_left:
            for tokens_file, part_number, revisions_file in files_iter:
                # print(tokens_file, part_number, revisions_file)
                job = executor.submit(find_problematic_articles, tokens_file, part_number, revisions_file, log_folder)
                jobs[job] = 'part_{}'.format(part_number)
                if len(jobs) == max_workers:  # limit # jobs with max_workers
                    break

            for job in as_completed(jobs):
                files_left -= 1
                part_ = jobs[job]
                try:
                    problematic_articles = job.result()
                    for article_title, article_id in problematic_articles:
                        dump_file = get_dump_file(int(article_id), dumps_dict)
                        if not dump_file:
                            continue
                        if dump_file in problematic_articles_dict:
                            problematic_articles_dict[dump_file]['missing'].append([article_title, article_id])
                        else:
                            problematic_articles_dict[dump_file] = {'missing': [[article_title, article_id]]}
                    with open(output_json, 'w') as f:
                        json.dump(problematic_articles_dict, f)
                except Exception as exc:
                    logger.exception(part_)

                del jobs[job]
                sys.stdout.write('\r{}-{:.3f}%'.format(files_left, ((files_all - files_left) * 100) / files_all))
                break  # to add a new job, if there is any
    print('\nDone: Find problematic articles at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))

if __name__ == '__main__':
    main()
