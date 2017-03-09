"""
python wikiwho/tools_dataset/analysis/compare_reverts.py -f '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/dataset' -m 4
"""
from os import listdir, mkdir
from os.path import exists
from time import strftime
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys
import argparse
import logging
import glob
import csv
import json


def _get_sorted_file_list(folder_path, first_sep='-part'):
    files = glob.glob(folder_path + '/*.csv')
    d = {}
    for file_ in files:
        d[file_.split('/')[-1].split(first_sep)[1].split('-')[0]] = file_
    assert len(files) == len(d)
    input_files = []
    for k in sorted(d, key=int):
        input_files.append(d[k])
    return input_files


def _get_sub_revert_files(reverts_files, start, end):
    sub_revert_files = []
    start_passed = False
    for reverts_file in reverts_files:
        r_start, r_end = reverts_file.split('.csv')[0].split('-')[2:]
        r_start = int(r_start)
        r_end = int(r_end)
        # print(start, end, r_start, r_end)
        if r_start <= start <= r_end:
            start_passed = True
        if not start_passed:
            continue
        # print('-----', reverts_file)
        sub_revert_files.append(reverts_file)
        if end < r_end:
            break
    return sub_revert_files


def compare_reverts(reverts_folder, sha_reverts_file, part, start, end, output_folder, log_folder):
    # print(sha_reverts_file)
    logger = logging.getLogger(part)
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                part,
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    reverts_part = 'None'
    d = {}
    try:
        # reverts-part7-8785-10139.csv
        reverts_files = _get_sorted_file_list(reverts_folder)
        reverts_dict = {}
        for reverts_file in _get_sub_revert_files(reverts_files, start, end):
            reverts_part = reverts_file.split('.csv')[0].split('-')[1]
            with open(reverts_file) as f_reverts:
                next(f_reverts)  # skip header
                for line in f_reverts:
                    line = line.split(',')
                    # reverted_add_actions + reverted_del_actions by source
                    reverted_actions = int(line[3]) + int(line[4])
                    # total_actions by target
                    total_actions = int(line[5])
                    # True for full revert, False for partial revert
                    reverts_dict['{}-{}'.format(line[1], line[2])] = reverted_actions == total_actions
        count_source_target = 0
        count_source_target_in_reverts = 0
        count_source_target_in_reverts_full = 0
        count_source_target_in_reverts_partial = 0
        with open(sha_reverts_file) as f_sha:
            reader = csv.reader(f_sha, delimiter=',')
            next(reader)  # skip header
            for line in reader:
                source = line[1]
                targets = line[2][1:-1].split(',')
                for target in targets:
                    count_source_target += 1
                    st = '{}-{}'.format(source, target)
                    if st in reverts_dict:
                        count_source_target_in_reverts += 1
                        if reverts_dict.get(st):
                            count_source_target_in_reverts_full += 1
                        else:
                            count_source_target_in_reverts_partial += 1
        d = {'count_source_target': count_source_target,
             'count_source_target_in_reverts': count_source_target_in_reverts,
             'count_source_target_in_reverts_full': count_source_target_in_reverts_full,
             'count_source_target_in_reverts_partial': count_source_target_in_reverts_partial}
    except Exception as e:
        logger.exception(reverts_part)
    return d


def get_args():
    parser = argparse.ArgumentParser(description='Compute sha reverts.')
    parser.add_argument('-f', '--base_path', required=True,
                        help='Base folder where sha reverts and reverts files take place')
    parser.add_argument('-m', '--max_workers', type=int, help='Default is 10')

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    base_path = args.base_path
    base_path = base_path[:-1] if base_path and base_path.endswith('/') else base_path
    reverts_folder = '{}/{}'.format(base_path, 'output_reverts')
    sha_reverts_folder = '{}/{}'.format(base_path, 'output_sha_reverts')
    output_folder = '{}/{}'.format(base_path, 'output_compare_reverts')
    if not exists(output_folder):
        mkdir(output_folder)

    log_folder = '{}/{}'.format(output_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)
    logger = logging.getLogger('future_log')
    file_handler = logging.FileHandler('{}/compare_reverts_future_at_{}.log'.format(log_folder,
                                                                                    strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]

    # ex input_file name: revisions-20161226-part2-5622-10852.csv_reverts-sha-out.csv
    input_files = _get_sorted_file_list(sha_reverts_folder)

    # for sha_reverts_file in input_files:
    #     data = sha_reverts_file.split('.csv')[0].split('-')
    #     part, start, end = data[2:]
    #     start = int(start)
    #     end = int(end)
    #     compare_reverts(reverts_folder, sha_reverts_file, part, start, end, output_folder, log_folder)
    # sys.exit()

    max_workers = args.max_workers or 10
    print(max_workers)
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    final_data = {'count_source_target': 0,
                  'count_source_target_in_reverts': 0,
                  'count_source_target_in_reverts_full': 0,
                  'count_source_target_in_reverts_partial': 0}
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        files_left = len(input_files)
        files_all = len(input_files)
        files_iter = iter(input_files)
        while files_left:
            for sha_reverts_file in files_iter:
                data = sha_reverts_file.split('.csv')[0].split('-')
                part, start, end = data[2:]
                start = int(start)
                end = int(end)
                job = executor.submit(compare_reverts, reverts_folder, sha_reverts_file, part, start, end,
                                      output_folder, log_folder)
                jobs[job] = part
                if len(jobs) == max_workers:  # limit # jobs with max_workers
                    break

            for job in as_completed(jobs):
                files_left -= 1
                part_ = jobs[job]
                try:
                    data = job.result()
                    for k, v in data.items():
                        final_data[k] += v
                    with open('{}/{}.json'.format(output_folder, part_), 'w') as fp:
                        json.dump(data, fp)
                except Exception as exc:
                    logger.exception(part_)

                del jobs[job]
                sys.stdout.write('\r{}-{:.3f}%'.format(files_left, ((files_all - files_left) * 100) / files_all))
                break  # to add a new job, if there is any
    with open('{}/all.json'.format(output_folder), 'w') as fp:
        json.dump(final_data, fp)
    print("Done: ", strftime("%Y-%m-%d-%H:%M:%S"))


if __name__ == '__main__':
    main()
