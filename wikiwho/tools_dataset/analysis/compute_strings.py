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
    # art = defaultdict(dict)  # {page_id: {rev_id: ['editor', 'timestamp']}, ..}
    art = defaultdict(dict)  # {page_id: {rev_id: 'timestamp'}, ..}
    # print("Load article-revision meta-data.")
    with open(revision_file) as csvfile:
        # Example of line: page_id,rev_id,timestamp,editor
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for aux in infile:
            page_id = int(aux[0])  # article id
            rev_id = int(aux[1])
            timestamp = parser.parse(aux[2])
            # editor = aux[3]
            # art[page_id].update({rev_id: [editor, timestamp]})
            art[page_id].update({rev_id: timestamp})
    return art


def load_articles_revisions_with_editor(revision_file):
    art = defaultdict(dict)  # {page_id: {rev_id: [editor, timestamp]}, ..}
    with open(revision_file) as csvfile:
        # Example of line: page_id,rev_id,timestamp,editor
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for aux in infile:
            page_id = int(aux[0])
            rev_id = int(aux[1])
            timestamp = parser.parse(aux[2])
            editor = aux[3]
            art[page_id].update({rev_id: [editor, timestamp]})
    return art


def compute_string_data(revision_file, token_file, string_set, string_set_startswith, output_file):
    # {page_id: {rev_id: timestamp}, ..}
    article_dict = load_articles_revisions(revision_file)
    # {'y-m': {'string': ['oadds', 'oadds_48h', 'dels', 'dels_48h', 're_ins', 're_ins_48h'], }, {}}
    string_dict = defaultdict(dict)

    # print("Load token meta-data.")
    seconds_limit = 48 * 3600  # hours
    with open(token_file) as csvfile:
        # Example of line CSV: page_id,last_rev_id,token_id,str,origin_rev_id,in,out
        infile = csv.reader(csvfile, delimiter=',')
        # next(infile, None)  # skip the headers
        for line in infile:
            string_ = line[3]
            is_in = string_ in string_set
            if not is_in:
                for w in string_set_startswith:
                    is_in = string_.startswith(w)
                    if is_in:
                        break
            if not is_in:
                continue

            page_id = int(line[0])
            origin_rev_id = int(line[4])
            inbound = eval(line[5].replace("{", "[").replace("}", "]"))
            outbound = eval(line[6].replace("{", "[").replace("}", "]"))

            article_revs = article_dict[page_id]  # {rev_id: timestamp, .. }

            # Cleaning outbound and inbound.
            outs_ts = []
            for rev in outbound:
                if rev in article_revs:
                    outs_ts.append(article_revs[rev])
                # else:
                #     print(1)
            ins_ts = []
            for rev in inbound:
                if rev in article_revs:
                    ins_ts.append(article_revs[rev])
                # else:
                #     print(2)

            # analyse original addition
            origin_ts = article_revs[origin_rev_id]
            origin_period = (origin_ts.year, origin_ts.month)
            oadd_survived = 1
            if outs_ts:
                first_out_ts = outs_ts[0]  # timestamp of first out rev
                seconds_oadd_survived = (first_out_ts - origin_ts).total_seconds()
                if seconds_oadd_survived < seconds_limit:
                    oadd_survived = 0
            if string_ in string_dict[origin_period]:
                string_dict[origin_period][string_][0] += 1
                string_dict[origin_period][string_][1] += oadd_survived
            else:
                string_dict[origin_period][string_] = [1, oadd_survived, 0, 0, 0, 0]

            # analyse deletions
            ts_in_prev = None
            for i, ts_out in enumerate(outs_ts):
                out_period = (ts_out.year, ts_out.month)

                if ts_in_prev is not None:
                    re_insert_survived = 1
                    seconds_re_insert_survived = (ts_out - ts_in_prev).total_seconds()
                    if seconds_re_insert_survived < 0:
                        # sth is wrong with in and outs
                        ts_in_prev = None
                        break
                    if seconds_re_insert_survived < seconds_limit:
                        # re insert did not survive (re-inserted in) 48 hours
                        re_insert_survived = 0
                    re_insert_period = (ts_in_prev.year, ts_in_prev.month)
                    if string_ in string_dict[re_insert_period]:
                        string_dict[re_insert_period][string_][4] += 1
                        string_dict[re_insert_period][string_][5] += re_insert_survived
                    else:
                        string_dict[re_insert_period][string_] = [0, 0, 0, 0, 1, re_insert_survived]

                deletion_survived = 1
                try:
                   ts_in = ins_ts[i]
                except IndexError:
                    # no in for this out => deletion survived
                    if string_ in string_dict[out_period]:
                        string_dict[out_period][string_][2] += 1
                        string_dict[out_period][string_][3] += deletion_survived
                    else:
                        string_dict[out_period][string_] = [0, 0, 1, deletion_survived, 0, 0]
                    ts_in_prev = None
                    break
                seconds_deletion_survived = (ts_in - ts_out).total_seconds()
                if seconds_deletion_survived < 0:
                    # sth is wrong with in and outs
                    ts_in_prev = None
                    break
                if seconds_deletion_survived < seconds_limit:
                    # deletion did not survive (re-inserted in) 48 hours
                    deletion_survived = 0
                if string_ in string_dict[out_period]:
                    string_dict[out_period][string_][2] += 1
                    string_dict[out_period][string_][3] += deletion_survived
                else:
                    string_dict[out_period][string_] = [0, 0, 1, deletion_survived, 0, 0]

                ts_in_prev = ts_in
                ts_out = None
            if ts_in_prev is not None and ts_out is None:
                # if len(ins) == len(outs)
                re_insert_survived = 1
                re_insert_period = (ts_in_prev.year, ts_in_prev.month)
                if string_ in string_dict[re_insert_period]:
                    string_dict[re_insert_period][string_][4] += 1
                    string_dict[re_insert_period][string_][5] += re_insert_survived
                else:
                    string_dict[re_insert_period][string_] = [0, 0, 0, 0, 1, re_insert_survived]

    # output deletion analysis
    with open(output_file, 'w') as f_out:
        f_out.write("year,month,string,oadds,oadds_48h,dels,dels_48h,reins,reins_48h\n")
        for year_month in month_year_iter(1, 2001, 12, 2016):
            (year, month) = year_month
            if year_month in string_dict:
                for string_, data in string_dict[year_month].items():
                    f_out.write(str(year) + ',' + str(month) + ',' + string_ + ',' +
                                str(data[0]) + ',' + str(data[1]) + ',' +
                                str(data[2]) + ',' + str(data[3]) + ',' +
                                str(data[4]) + ',' + str(data[5]) + '\n')
            else:
                f_out.write(str(year) + ',' + str(month) + ',,0,0,0,0,0,0' + '\n')


def compute_string_data_base(revision_file, token_file, string_set, string_set_startswith, output_file, part_id, log_folder):
    logger = get_logger(part_id, log_folder, is_process=True, is_set=False)
    try:
        compute_string_data(revision_file, token_file, string_set, string_set_startswith, output_file)
    except Exception as e:
        logger.exception('part_{}'.format(part_id))
    return True


def compute_string_conflict(revision_file, token_file, string_set, string_set_startswith, output_file):
    # {page_id: {rev_id: [editor, timestamp]}, ..}
    article_dict = load_articles_revisions_with_editor(revision_file)
    # {'y-m': {'string': conflict_score, }, {}}
    string_conflict_dict = defaultdict(dict)

    # print("Load token meta-data.")
    log_base = 3600
    with open(token_file) as csvfile:
        # Example of line CSV: page_id,last_rev_id,token_id,str,origin_rev_id,in,out
        infile = csv.reader(csvfile, delimiter=',')
        # next(infile, None)  # skip the headers
        for line in infile:
            string_ = line[3]
            is_in = string_ in string_set
            if not is_in:
                for w in string_set_startswith:
                    is_in = string_.startswith(w)
                    if is_in:
                        break
            if not is_in:
                continue
            page_id = int(line[0])
            inbound = eval(line[5].replace("{", "[").replace("}", "]"))
            outbound = eval(line[6].replace("{", "[").replace("}", "]"))
            article_revs = article_dict[page_id]  # {rev_id: [editor, timestamp], .. }

            # Cleaning outbound and inbound.
            outs_editor_ts = []
            for rev in outbound:
                if rev in article_revs:
                    outs_editor_ts.append(article_revs[rev])
            ins_editor_ts = []
            for rev in inbound:
                if rev in article_revs:
                    ins_editor_ts.append(article_revs[rev])

            # analyse conflict
            editor_in_prev = None
            ts_in_prev = None
            for i, (editor_out, ts_out) in enumerate(outs_editor_ts):
                # re-insert
                if ts_in_prev is not None and editor_in_prev != editor_out:
                    seconds_re_insert_survived = (ts_out - ts_in_prev).total_seconds()
                    if seconds_re_insert_survived < 0:
                        # sth is wrong with in and outs
                        break
                    re_insert_conflict_score = 1.0 / (log(seconds_re_insert_survived + 2.0, log_base))
                    re_insert_period = (ts_in_prev.year, ts_in_prev.month)
                    if string_ in string_conflict_dict[re_insert_period]:
                        string_conflict_dict[re_insert_period][string_] += re_insert_conflict_score
                    else:
                        string_conflict_dict[re_insert_period][string_] = re_insert_conflict_score
                # deletion
                try:
                    editor_in, ts_in = ins_editor_ts[i]
                except IndexError:
                    # no in for this out => deletion survived, no conflict
                    break
                if editor_out != editor_in:
                    seconds_deletion_survived = (ts_in - ts_out).total_seconds()
                    if seconds_deletion_survived < 0:
                        # sth is wrong with in and outs
                        break
                    deletion_conflict_score = 1.0 / (log(seconds_deletion_survived + 2.0, log_base))
                    out_period = (ts_out.year, ts_out.month)
                    if string_ in string_conflict_dict[out_period]:
                        string_conflict_dict[out_period][string_] += deletion_conflict_score
                    else:
                        string_conflict_dict[out_period][string_] = deletion_conflict_score
                editor_in_prev = editor_in
                ts_in_prev = ts_in

    # output deletion analysis
    with open(output_file, 'w') as f_out:
        f_out.write("year,month,string,conflict_time\n")
        for year_month in month_year_iter(1, 2001, 12, 2016):
            (year, month) = year_month
            if year_month in string_conflict_dict:
                for string_, conflict_score in string_conflict_dict[year_month].items():
                    f_out.write(str(year) + ',' + str(month) + ',' + string_ + ',' + str(conflict_score) + '\n')
            else:
                f_out.write(str(year) + ',' + str(month) + ',,0' + '\n')


def compute_string_conflict_base(revision_file, token_file, string_set, string_set_startswith, output_file, part_id, log_folder):
    logger = get_logger(part_id, log_folder, is_process=True, is_set=False)
    try:
        compute_string_conflict(revision_file, token_file, string_set, string_set_startswith, output_file)
    except Exception as e:
        logger.exception('part_{}'.format(part_id))
    return True


def get_args():
    """
python compute_strings.py -r '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/revisions' -t '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/tokens' -o '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_strings' -m=4
python compute_strings.py -r '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/revisions' -t '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/tokens' -o '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_strings_conflict' -m=4 -c
    """
    parser = argparse.ArgumentParser(description='Compute survival data of oadds and deletions or conflict score '
                                                 'per year-month-string.')
    parser.add_argument('-r', '--revisions_folder', required=True, help='Where revision partition csvs are.')
    parser.add_argument('-t', '--tokens_folder', required=True, help='Where token partition csvs are.')
    parser.add_argument('-s', '--strings', help='Strings comma separated. There is a default list.')
    parser.add_argument('-o', '--output_folder', required=True, help='')
    parser.add_argument('-m', '--max_workers', type=int, help='Default is 16')
    parser.add_argument('-c', '--conflict', action='store_true', default=False,
                        help='Compute conflict score for each script, default is False.')

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    revisions_folder = args.revisions_folder
    tokens_folder = args.tokens_folder
    string_set = args.strings
    if string_set:
        string_set = set(string_set.split(','))
    else:
        string_set = {'conservative*', 'liberal*', 'democratic*', 'anxious*', 'notably*', 'interestingly*',
                      'tragical*', 'comprises', 'comprised', 'remarkabl*', 'however', 'apparent*', 'famous*',
                      'literally', 'figuratively'}
    string_set_startswith = {s[:-1] for s in string_set if s.endswith('*')}  # will be check for startswith
    string_set = {s for s in string_set if not s.endswith('*')}  # will be checked for is equal
    output_folder = args.output_folder
    if not exists(output_folder):
        mkdir(output_folder)
    max_workers = args.max_workers or 16
    is_conflict_computation = args.conflict

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
                                    '{}/strings{}-part{}.csv'.format(output_folder,
                                                                     '-conflict' if is_conflict_computation else '',
                                                                     part_id)]
    input_files = []
    for k in sorted(inputs_dict, key=int):
        input_files.append(inputs_dict[k])

    # logging
    log_folder = '{}/{}'.format(output_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)
    logger = get_logger('future_log', log_folder, is_process=True, is_set=True)

    print('is_conflict_computation:', is_conflict_computation)
    print('max_workers:', max_workers, 'len inputs:', len(input_files))
    print('string_set_startswith:', string_set_startswith)
    print('string_set:', string_set)
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        files_left = len(input_files)
        files_all = len(input_files)
        files_iter = iter(input_files)
        while files_left:
            for part_id, token_file, revision_file, output_file in files_iter:
                # print(part_id, revision_file, token_file, string_set, output_file, part_id, log_folder)
                # files_left -= 1
                # continue
                if not is_conflict_computation:
                    job = executor.submit(compute_string_data_base, revision_file,
                                          token_file, string_set, string_set_startswith,
                                          output_file, part_id, log_folder)
                else:
                    job = executor.submit(compute_string_conflict_base, revision_file,
                                          token_file, string_set, string_set_startswith,
                                          output_file, part_id, log_folder)
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
