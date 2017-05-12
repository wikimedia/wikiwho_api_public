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


# def month_year_iter(start_month, start_year, end_month, end_year):
#     ym_start = 12 * start_year + start_month - 1
#     ym_end = 12 * end_year + end_month - 1
#     for ym in range(ym_start, ym_end):
#         y, m = divmod(ym, 12)
#         yield y, m + 1
#
#
# def load_articles_revisions(revision_file):
#     art = defaultdict(dict)  # {page_id: {rev_id: ['editor', 'timestamp']}, ..}
#     # print("Load article-revision meta-data.")
#     with open(revision_file) as csvfile:
#         # Example of line: page_id,rev_id,timestamp,editor
#         infile = csv.reader(csvfile, delimiter=',')
#         next(infile, None)  # skip the headers
#         for aux in infile:
#             page_id = int(aux[0])  # article id
#             rev_id = int(aux[1])
#             timestamp = parser.parse(aux[2])
#             editor = aux[3]
#             art[page_id].update({rev_id: [editor, timestamp]})
#     return art


def load_bots(bot_file):
    bots = {}
    # print("Load bot list.")
    with open(bot_file) as infile:
        next(infile, None)
        for line in infile:
            aux = line.split(",", 1)
            bots.update({aux[0]: aux[1]})  # {bot_id: bot_name}
    return bots


def extract_editors(revision_file, bot_file, output_file):
    # Main structures.
    # article_dict = load_articles_revisions(revision_file)
    bots_dict = load_bots(bot_file)

    # {'editor': {ts: (rev_id, page_id), ..}, ..}
    editors_dict = defaultdict(dict)
    with open(revision_file) as csvfile:
        infile = csv.reader(csvfile, delimiter=',')
        next(infile, None)  # skip the headers
        for line in infile:
            # page_id,rev_id,timestamp,editor
            editor = line[3]
            # if editor in bots_dict:
                # print(editor in bots_dict, type(editor))
            if editor in bots_dict or editor.startswith('0|'):
                # skip bots and non-registered editors
                continue
            # print(line[2])
            timestamp = parser.parse(line[2])
            # page_id = int(line[0])  # article id
            # rev_id = int(line[1])
            editors_dict[editor][timestamp] = (line[1], line[0])

    # output editors data
    with open(output_file, 'w') as f_out:
        f_out.write('editor,edit_no,rev_id,rev_ts,page_id\n')
        for editor, data in editors_dict.items():
            for i, rev_ts in enumerate(sorted(data)):
                rev_id, page_id = data[rev_ts]
                f_out.write(editor + ',' + str(i) + ',' + rev_id + ',' + str(rev_ts) + ',' + page_id + '\n')


def extract_editors_base(revision_file, bot_file, output_file, part_id, log_folder):
    logger = get_logger(part_id, log_folder, is_process=True, is_set=False)
    try:
        extract_editors(revision_file, bot_file, output_file)
    except Exception as e:
        logger.exception('part_{}'.format(part_id))
    return True


def get_args():
    """
python extract_editors.py -r '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/revisions' -b '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/botlist.csv' -o '/home/kenan/PycharmProjects/wikiwho_api/tests_ignore/partitions/output_editors' -m=4
    """
    parser = argparse.ArgumentParser(description='Extract')
    parser.add_argument('-r', '--revisions_folder', required=True, help='Where revision partition csvs are.')
    # TODO should we use all_tokens (with if rev_id in art[revs]) or current+deleted
    # parser.add_argument('-t', '--tokens_folder', required=True, help='Where token partition csvs are.')
    parser.add_argument('-b', '--bots_file', required=True, help='')
    parser.add_argument('-o', '--output_folder', required=True, help='')
    parser.add_argument('-m', '--max_workers', type=int, help='Default is 16')

    args = parser.parse_args()
    return args


def main():
    args = get_args()
    revisions_folder = args.revisions_folder
    # tokens_folder = args.tokens_folder
    bots_file = args.bots_file
    output_folder = args.output_folder
    if not exists(output_folder):
        mkdir(output_folder)
    max_workers = args.max_workers or 16

    csv.field_size_limit(sys.maxsize)
    # group and order input files.
    revisions_dict = {}
    for revision_file in listdir(revisions_folder):
        # 20161101-revisions-part7-8785-10139.csv
        revisions_dict[revision_file.split('-')[2][4:]] = '{}/{}'.format(revisions_folder, revision_file)
    input_files = []
    for part_id in sorted(revisions_dict, key=int):
        input_files.append([
            part_id,
            revisions_dict[part_id],
            '{}/editors-part{}.csv'.format(output_folder, part_id)])
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
            for part_id, revision_file, output_file in files_iter:
                # print(part_id, revision_file, bots_file, output_file, log_folder)
                # files_left -= 1
                # continue
                job = executor.submit(extract_editors_base, revision_file,
                                      bots_file, output_file, part_id, log_folder)
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
    print("Done: ", strftime("%Y-%m-%d-%H:%M:%S"))


if __name__ == '__main__':
    main()
