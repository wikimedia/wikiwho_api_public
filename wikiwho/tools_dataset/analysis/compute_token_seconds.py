import sys
import csv
import argparse
import logging
from collections import defaultdict
from dateutil import parser
from os.path import realpath, exists
from os import listdir, mkdir
from time import strftime
from concurrent.futures import ProcessPoolExecutor, as_completed
from math import log


def get_logger(name, log_folder, is_process=True, is_set=True):
    logger = logging.getLogger(name)
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                name,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    if is_process:
        format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
    else:
        format_ = '%(asctime)s %(threadName)-10s %(name)s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    if is_set:
        logger.handlers = [file_handler]
    else:
        logger.addHandler(file_handler)
    return logger


def month_year_iter(start_month, start_year, end_month, end_year):
    ym_start = 12 * start_year + start_month - 1
    ym_end = 12 * end_year + end_month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        yield y, m + 1


def load_articles_revisions(revision_file):
    art = defaultdict(dict)  # {page_id: {rev_id: 'timestamp'}, ..}
    with open(revision_file) as csvfile:
        # Example of line: page_id,rev_id,timestamp,editor
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for aux in infile:
            page_id = int(aux[0])  # article id
            rev_id = int(aux[1])
            timestamp = parser.parse(aux[2])
            # editor = aux[3]
            # art[page_id].update({rev_id: timestamp})
            art[page_id].update({rev_id: timestamp})
    return art


def compute_token_seconds(revision_file, token_file, output_file):
    # {page_id: {rev_id: timestamp}, ..}
    article_dict = load_articles_revisions(revision_file)
    # {page_id: {token_id: [string, oadd_seconds, [out_seconds, ..]]}, }, {}}
    token_seconds_dict = defaultdict(dict)

    with open(token_file) as csvfile:
        # Example of line CSV: page_id,last_rev_id,token_id,str,origin_rev_id,in,out
        infile = csv.reader(csvfile, delimiter=',')
        # next(infile, None)  # skip the headers
        for line in infile:
            string_ = line[3]
            page_id = int(line[0])
            token_id = int(line[2])
            origin_rev_id = int(line[4])
            inbound = eval(line[5].replace("{", "[").replace("}", "]"))
            outbound = eval(line[6].replace("{", "[").replace("}", "]"))
            article_revs = article_dict[page_id]  # {rev_id: timestamp, .. }

            # Cleaning outbound.
            outs_ts = []
            for rev in outbound:
                if rev in article_revs:
                    outs_ts.append(article_revs[rev])

            # get oadd survival seconds
            if outs_ts:
                oadd_seconds = (outs_ts[0] - article_revs[origin_rev_id]).total_seconds()
            else:
                # this token survived (not deleted) until 2016 Nov
                continue

            # Cleaning inbound.
            ins_ts = []
            for rev in inbound:
                if rev in article_revs:
                    ins_ts.append(article_revs[rev])

            # get outs' survival seconds
            outs_seconds = []
            for i, ts_out in enumerate(outs_ts):
                try:
                    ts_in = ins_ts[i]
                except IndexError:
                    # no in for this out => deletion survived
                    break
                seconds_survived = (ts_in - ts_out).total_seconds()
                if seconds_survived < 0:
                    # sth is wrong with in and outs
                    break
                outs_seconds.append(seconds_survived)

            token_seconds_dict[page_id][token_id] = [string_, oadd_seconds, outs_seconds]

    # output deletion analysis
    with open(output_file, 'w') as f_out:
        f_out.write('page_id,token_id,string,oadd_surv_seconds,outs_surv_seconds\n')
        for page_id, page_tokens in token_seconds_dict.items():
            for token_id, data in page_tokens.items():
                outs = ','.join(map(str, data[2])) if data[2] else ''
                outs = '"{{{}}}"'.format(outs) if ',' in outs else '{{{}}}'.format(outs)
                f_out.write(str(page_id) + ',' + str(token_id) + ',' + str(data[0]) + ',' +
                            str(data[1]) + ',' + outs + '\n')


def compute_token_seconds_base(revision_file, token_file, output_file, part_id, log_folder):
    logger = get_logger(part_id, log_folder, is_process=True, is_set=False)
    try:
        compute_token_seconds(revision_file, token_file, output_file)
    except Exception as e:
        logger.exception('part_{}'.format(part_id))
    return True


def get_args():
    """
python compute_token_seconds.py -r '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/revisions' -t '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/tokens' -o '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_token_seconds' -m=4
    """
    parser = argparse.ArgumentParser(description='Compute how many seconds an oadd and outs survived per token.')
    parser.add_argument('-r', '--revisions_folder', required=True, help='Where revision partition csvs are.')
    parser.add_argument('-t', '--tokens_folder', required=True, help='Where token partition csvs are.')
    parser.add_argument('-o', '--output_folder', required=True, help='')
    parser.add_argument('-m', '--max_workers', type=int, help='Default is 16')

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    revisions_folder = args.revisions_folder
    tokens_folder = args.tokens_folder
    output_folder = args.output_folder
    if not exists(output_folder):
        mkdir(output_folder)
    max_workers = args.max_workers or 16

    csv.field_size_limit(sys.maxsize)
    # group and order input files.
    revisions_dict = {}
    for revision_file in listdir(revisions_folder):
        if revision_file.endswith('.csv'):
            # 20161101-revisions-part7-8785-10139.csv
            revisions_dict[revision_file.split('-')[2][4:]] = '{}/{}'.format(revisions_folder, revision_file)
    inputs_dict = {}
    for token_file in listdir(tokens_folder):
        if token_file.endswith('.csv'):
            # ex input_file_name: 20161226-tokens-part3-3378-4631.csv
            part_id = token_file.split('-')[2][4:]
            inputs_dict[part_id] = [part_id,
                                    '{}/{}'.format(tokens_folder, token_file),
                                    revisions_dict[part_id],
                                    '{}/token-seconds-part{}.csv'.format(output_folder, part_id)]
    input_files = []
    for k in sorted(inputs_dict, key=int):
        input_files.append(inputs_dict[k])

    # logging
    log_folder = '{}/{}'.format(output_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)
    logger = get_logger('future_log', log_folder, is_process=True, is_set=True)

    print('max_workers:', max_workers, 'len inputs:', len(input_files))
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        files_left = len(input_files)
        files_all = len(input_files)
        files_iter = iter(input_files)
        while files_left:
            for part_id, token_file, revision_file, output_file in files_iter:
                # print(part_id, revision_file, token_file, output_file, part_id, log_folder)
                # files_left -= 1
                # continue
                job = executor.submit(compute_token_seconds_base, revision_file,
                                      token_file, output_file, part_id, log_folder)
                jobs[job] = part_id
                if len(jobs) == max_workers:  # limit # jobs with max_workers
                    break

            for job in as_completed(jobs):
                files_left -= 1
                part_id_ = jobs[job]
                try:
                    data = job.result()
                except Exception as exc:
                    logger.exception('part_{}'.format(part_id_))

                del jobs[job]
                sys.stdout.write('\rFiles left: {} - Done: {:.3f}%'.
                                 format(files_left, ((files_all - files_left) * 100) / files_all))
                break  # to add a new job, if there is any
    print("\nDone: ", strftime("%Y-%m-%d-%H:%M:%S"))


if __name__ == '__main__':
    main()
