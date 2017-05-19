import sys
import csv
import argparse
import logging
from collections import defaultdict
from os.path import realpath, exists, join
from os import listdir, mkdir, walk
from time import strftime
from concurrent.futures import ProcessPoolExecutor, as_completed
from random import shuffle
from dateutil import parser


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
            art[page_id].update({rev_id: timestamp})
    return art


def compute_editors(editors, editors_file, tokens_folder, revisions_folder, output_folder, logger):
    # {editor: {rev_id: [len_edits, rev_ts, oadds, oadds_48h, reins, reins_48h, deletes, deletes_48h,
    # [tokens_added], [tokens_added_48h], [tokens_rein], [tokens_rein_48h], [tokens_deleted], [tokens_deleted_48h], edit_no]}}
    editors_dict = {}
    for editor in editors:
        editors_dict[editor] = defaultdict(dict)
    with open(editors_file) as f:
        csv_ = csv.reader(f, delimiter=',')
        for row in csv_:
            # editor,len_edits,edit_no,rev_id,rev_ts
            if row[0] in editors:
                editors_dict[row[0]][int(row[3])] = [row[1], row[4],
                                                     0, 0, 0, 0, 0, 0,
                                                     [], [], [], [], [], [],
                                                     int(row[2])]
    # for editor in editors:
    #     print(editor, len(editors_dict[editor]))

    revisions_dict = {}
    for revision_file in listdir(revisions_folder):
        if revision_file.endswith('.csv'):
            # 20161101-revisions-part7-8785-10139.csv
            revisions_dict[revision_file.split('-')[2][4:]] = '{}/{}'.format(revisions_folder, revision_file)
    # print('len rev files:', len(revisions_dict))

    content_files = []
    for root, dirs, files in walk(join(tokens_folder, 'current_content_newer')):
        for file in files:
            if file.endswith(".csv"):
                content_files.append(join(root, file))
    for root, dirs, files in walk(join(tokens_folder, 'deleted_content_newer')):
        for file in files:
            if file.endswith(".csv"):
                content_files.append(join(root, file))
    shuffle(content_files)
    # print('len content_files:', len(content_files))

    in_outs_still_wrong = set()  # page ids
    seconds_limit = 48 * 3600  # 2 days
    for content_file in content_files:
        # 20161101-current_content-part49-108968-112997.csv
        part_id = content_file.split('-part')[-1].split('-')[0]
        revision_file = revisions_dict[part_id]
        article_revs = load_articles_revisions(revision_file)
        # print(revision_file, content_file)
        with open(content_file) as csvfile:
            next(csvfile, None)  # skip the headers
            # for line in csvfile.read().splitlines(): --> doesnt splitlines correctly
            for line in csvfile:
                # page_id,last_rev_id,token_id,str,origin_rev_id,in,out
                line = line.split(',')
                page_id = int(line[0])
                token_id = int(line[2])
                if line[3].startswith('"') and line[4].endswith('"'):
                    string_ = line[3][1:] + ',' + line[4][:-1]
                    origin_rev_id = int(line[5])
                    ins_outs = line[6:]
                else:
                    string_ = line[3]
                    origin_rev_id = int(line[4])
                    ins_outs = line[5:]
                if string_.startswith('"') and string_.endswith('"'):
                    # string with " was written into csv correctly
                    string_ = string_[1:-1].replace('""', '"')
                revisions = article_revs[page_id]
                is_ins = True
                ins = []
                outs = []
                for in_or_out in ins_outs:
                    in_or_out_ = in_or_out.replace('}', '').replace('{', '').replace('"', '').replace('\n', '')
                    if in_or_out_ and int(in_or_out_) in revisions:
                        if is_ins:
                            ins.append(int(in_or_out_))
                        else:
                            outs.append(int(in_or_out_))
                    elif in_or_out_ and int(in_or_out_) not in revisions and page_id not in in_outs_still_wrong:
                        logger.error('{}: rev_id {} is not in revision file'.format(page_id, in_or_out_))
                        in_outs_still_wrong.add(page_id)
                    if in_or_out.endswith('}"') or in_or_out.endswith('}'):
                        is_ins = False
                if not (0 <= len(outs) - len(ins) <= 1) and page_id not in in_outs_still_wrong:
                    logger.error('{},{},{}: token problematic (not (0 <= len(outs) - len(ins) <= 1))'.
                                 format(page_id, origin_rev_id, token_id))
                    in_outs_still_wrong.add(page_id)

                is_token_problematic = False
                # oadd
                for editor, revs in editors_dict.items():
                    if origin_rev_id in revs:
                        # print('+')
                        d = revs[origin_rev_id]
                        d[2] += 1
                        d[8].append(string_)
                        origin_rev_ts = revisions[origin_rev_id]
                        # print(page_id, string_, origin_rev_id, origin_rev_ts, ins, outs)
                        # print(list(revisions.keys()))
                        # print(ins_outs)
                        # print(d)
                        if outs:
                            first_out_ts = revisions[outs[0]]
                            seconds = (first_out_ts - origin_rev_ts).total_seconds()
                            # print(first_out_ts, seconds, seconds >= seconds_limit)
                            if seconds < 0:
                                is_token_problematic = True
                                if page_id not in in_outs_still_wrong:
                                    logger.error('{},{},{}: token problematic (seconds < 0)'.
                                                 format(page_id, origin_rev_id, token_id))
                                    in_outs_still_wrong.add(page_id)
                                break
                            if seconds >= seconds_limit:
                                d[3] += 1
                                d[9].append(string_)
                        else:
                            d[3] += 1
                            d[9].append(string_)
                if is_token_problematic:
                    continue
                # rein and del
                prev_in_rev_id = None
                for i, out_rev_id in enumerate(outs):
                    # rein
                    if prev_in_rev_id is not None:
                        for editor, revs in editors_dict.items():
                            if prev_in_rev_id in revs:
                                d = revs[prev_in_rev_id]
                                d[4] += 1
                                d[10].append(string_)
                                prev_in_rev_ts = revisions[prev_in_rev_id]
                                out_rev_ts = revisions[out_rev_id]
                                seconds = (out_rev_ts - prev_in_rev_ts).total_seconds()
                                if seconds < 0:
                                    is_token_problematic = True
                                    if page_id not in in_outs_still_wrong:
                                        logger.error('{},{},{}: token problematic (seconds < 0)'.
                                                     format(page_id, origin_rev_id, token_id))
                                        in_outs_still_wrong.add(page_id)
                                    break
                                if seconds >= seconds_limit:
                                    d[5] += 1
                                    d[11].append(string_)
                                break
                        if is_token_problematic:
                            break
                    # del
                    try:
                        in_rev_id = ins[i]
                    except IndexError:
                        # no in for this out
                        for editor, revs in editors_dict.items():
                            if out_rev_id in revs:
                                d = revs[out_rev_id]
                                d[6] += 1
                                d[7] += 1
                                d[12].append(string_)
                                d[13].append(string_)
                                break
                        break
                    else:
                        for editor, revs in editors_dict.items():
                            if out_rev_id in revs:
                                d = revs[out_rev_id]
                                d[6] += 1
                                d[12].append(string_)
                                out_rev_ts = revisions[out_rev_id]
                                in_rev_ts = revisions[in_rev_id]
                                seconds = (in_rev_ts - out_rev_ts).total_seconds()
                                if seconds < 0:
                                    is_token_problematic = True
                                    if page_id not in in_outs_still_wrong:
                                        logger.error('{},{},{}: token problematic (seconds < 0)'.
                                                     format(page_id, origin_rev_id, token_id))
                                        in_outs_still_wrong.add(page_id)
                                    break
                                if seconds >= seconds_limit:
                                    d[7] += 1
                                    d[13].append(string_)
                                break
                        if is_token_problematic:
                            break
                    prev_in_rev_id = in_rev_id
                    out_rev_id = None
                if is_token_problematic:
                    continue
                if prev_in_rev_id is not None and out_rev_id is None:
                    for editor, revs in editors_dict.items():
                        if prev_in_rev_id in revs:
                            d = revs[prev_in_rev_id]
                            d[4] += 1
                            d[10].append(string_)
                            d[5] += 1
                            d[11].append(string_)
                            break

    # output editors data
    output_file = '{}/editors-all-parts-filtered-1000-{}-{}.csv'.format(output_folder, editors[0], editors[-1])
    with open(output_file, 'w') as f_out:
        header = 'editor,len_edits,edit_no,rev_id,rev_ts,' \
                 'oadds,oadds_48h,reins,reins_48h,deletes,deletes_48h,tokens_added,' \
                 'tokens_added_48h,tokens_rein,tokens_rein_48h,tokens_deleted,tokens_deleted_48h'
        csv_out = csv.writer(f_out, delimiter=',')
        csv_out.writerow(header.split(','))
        # {editor: {rev_id: [len_edits, rev_ts, oadds, oadds_48h, reins, reins_48h, deletes, deletes_48h,
        # [tokens_added], [tokens_added_48h], [tokens_rein], [tokens_rein_48h], [tokens_deleted], [tokens_deleted_48h], edit_no]}}
        for editor, revs in editors_dict.items():
            for rev_id, rev_data in revs.items():
                csv_out.writerow([editor, rev_data[0], rev_data[-1], rev_id] + rev_data[1:-1])


def compute_editors_base(batch_limits, editors, editors_file, tokens_folder, revisions_folder, log_folder, output_folder):
    logger = get_logger(batch_limits, log_folder, is_process=True, is_set=False)
    try:
        compute_editors(editors, editors_file, tokens_folder, revisions_folder, output_folder, logger)
    except Exception as e:
        logger.exception('editor_{}'.format(str(editors)))
    return True


def get_args():
    """
python compute_editor_data.py -r '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/revisions' -e '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors/editors-all-parts-filtered-2.csv' -t '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions' -o '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors' -m=4
    """
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-r', '--revisions_folder', required=True, help='Where revision partition csvs are.')
    parser.add_argument('-e', '--editors_file', required=True, help='Where editors file is.')
    parser.add_argument('-t', '--tokens_folder', required=True, help='Where current and deleted content files are.')
    parser.add_argument('-o', '--output_folder', required=True, help='')
    parser.add_argument('-m', '--max_workers', type=int, help='Default is 16')
    parser.add_argument('-b', '--batch_size', type=int, help='Default is 10')
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    batch_size = args.batch_size or 10
    revisions_folder = args.revisions_folder
    tokens_folder = args.tokens_folder
    editors_file = args.editors_file
    output_folder = args.output_folder
    if not exists(output_folder):
        mkdir(output_folder)
    max_workers = args.max_workers or 16

    csv.field_size_limit(sys.maxsize)
    # logging
    log_folder = '{}/{}'.format(output_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)
    logger = get_logger('future_log', log_folder, is_process=True, is_set=True)

    # get list of editors, for whom edit data will be collected
    editors = set()
    with open(editors_file) as f:
        csv_ = csv.reader(f, delimiter=',')
        next(csv_)  # skip the header
        for row in csv_:
            # editor,len_edits,edit_no,rev_id,rev_ts
            editors.add(row[0])

    print('max_workers:', max_workers, 'len editors:', len(editors), 'batch_size:', batch_size)
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        editors_left = len(editors)
        editors_all = len(editors)
        editors_list = list(editors)
        editors_iter = iter(range(0, len(editors_list), batch_size))
        while editors_left > 0:
            # for editor in editors_iter:
            for i in editors_iter:
                batch = editors_list[i:i + batch_size]
                batch_limits = '{}-{}'.format(batch[0], batch[-1])
                # print(batch_limits, batch, editors_file, tokens_folder,
                #       revisions_folder, log_folder, output_folder)
                # editors_left -= batch_size
                # continue
                job = executor.submit(compute_editors_base, batch_limits, batch, editors_file, tokens_folder,
                                      revisions_folder, log_folder, output_folder)
                jobs[job] = batch_limits
                if len(jobs) == max_workers:  # limit # jobs with max_workers
                    break

            for job in as_completed(jobs):
                editors_left -= batch_size
                batch_limits_ = jobs[job]
                try:
                    data = job.result()
                except Exception as exc:
                    logger.exception('editor_{}'.format(batch_limits_))

                del jobs[job]
                sys.stdout.write('\rEditors left: {} - Done: {:.3f}%'.
                                 format(editors_left, ((editors_all - editors_left) * 100) / editors_all))
                break  # to add a new job, if there is any
    print("Done: ", strftime("%Y-%m-%d-%H:%M:%S"))


if __name__ == '__main__':
    main()
