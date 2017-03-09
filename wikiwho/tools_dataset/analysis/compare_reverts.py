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
    d = {}  # {part_id: part_file_path, }
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
    matches = []
    partial_matches = []
    no_matches = []
    try:
        reverts_files = _get_sorted_file_list(reverts_folder)  # reverts-part7-8785-10139.csv
        # collect reverts data
        reverts_dict = {}
        for reverts_file in _get_sub_revert_files(reverts_files, start, end):
            reverts_part = reverts_file.split('.csv')[0].split('-')[1]
            with open(reverts_file) as f_reverts:
                reader = csv.reader(f_reverts, delimiter=',')
                next(reader)  # skip header
                # article,source,target,reverted_add_actions,reverted_del_actions,total_actions,source_editor,target_editor
                for line in reader:
                    # line = line.split(',')
                    # reverted_add_actions + reverted_del_actions by source
                    reverted_actions = int(line[3]) + int(line[4])
                    # total_actions by target
                    total_actions = int(line[5])
                    # True for full revert, False for partial revert
                    source_target = '{}-{}'.format(line[1].strip().rstrip(),
                                                   line[2].strip().rstrip())
                    reverts_dict[source_target] = reverted_actions == total_actions
        # compute sha reverts data in reverts
        count_source_target = 0
        count_source_target_in_reverts = 0
        count_source_target_in_reverts_full = 0
        count_source_target_in_reverts_partial = 0
        sources = []
        targets = []
        with open(sha_reverts_file) as f_sha:
            reader = csv.reader(f_sha, delimiter=',')
            next(reader)  # skip header
            # article_id,source,target,source_editor,target_editor
            for line in reader:
                source = line[1]
                source = source.strip().rstrip()
                sources.append(source)
                source_targets = line[2][1:-1].split(',')
                for target in source_targets:
                    target = target.strip().rstrip()
                    targets.append(target)
                    count_source_target += 1
                    st = '{}-{}'.format(source, target)
                    if st in reverts_dict:
                        matches.append([line[0], source, target])
                        count_source_target_in_reverts += 1
                        if reverts_dict.get(st):
                            count_source_target_in_reverts_full += 1
                        else:
                            partial_matches.append([line[0], source, target])
                            count_source_target_in_reverts_partial += 1
                    else:
                        no_matches.append([line[0], source, target])
        d = {'count_source_target': count_source_target,
             'count_source_target_in_reverts': count_source_target_in_reverts,
             'count_source_target_in_reverts_full': count_source_target_in_reverts_full,
             'count_source_target_in_reverts_partial': count_source_target_in_reverts_partial,
             'count_sources': len(sources),
             'count_distinct_sources': len(set(sources)),
             'count_targets': len(targets),
             'count_distinct_targets': len(set(targets))}
    except Exception as e:
        logger.exception(reverts_part)
    return d, matches, partial_matches, no_matches


def get_args():
    parser = argparse.ArgumentParser(description='Analyse/compare sha reverts in reverts.')
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
    final_data = {'count_source_target': 0,  # count of source-target pairs in sha reverts outputs
                  'count_source_target_in_reverts': 0,  # how many of those pairs are also in reverts output
                  'count_source_target_in_reverts_full': 0,  # how many of them are full revert
                  'count_source_target_in_reverts_partial': 0,  # how many of them are partial revert
                  'count_sources': 0,
                  'count_distinct_sources': 0,
                  'count_targets': 0,
                  'count_distinct_targets': 0
                  }
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
                    data, matches, partial_matches, no_matches = job.result()
                    for k, v in data.items():
                        final_data[k] += v
                    with open('{}/{}.json'.format(output_folder, part_), 'w') as fout:
                        json.dump(data, fout)
                    header = 'article_id,source,target\n'
                    with open('{}/{}_matches.csv'.format(output_folder, part_), 'w') as fout:
                        fout.write(header)
                        for match in matches:
                            fout.write(','.join(match) + '\n')
                    with open('{}/{}_partial_matches.csv'.format(output_folder, part_), 'w') as fout:
                        fout.write(header)
                        for partial_match in partial_matches:
                            fout.write(','.join(partial_match) + '\n')
                    with open('{}/{}_no_matches.csv'.format(output_folder, part_), 'w') as fout:
                        fout.write(header)
                        for no_match in no_matches:
                            fout.write(','.join(no_match) + '\n')
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
