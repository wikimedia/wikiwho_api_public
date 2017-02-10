# -*- coding: utf-8 -*-
"""
Example usage:
python wikiwho/tools_dataset/partitioning/replace_content_in_partition.py -o '../partitions' -i '' -m 2 -d 'cd'
"""
from os import mkdir, listdir
from os.path import exists, isfile
import logging
from time import strftime
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys
import argparse


def replace_content_in_partition(input_folder, part_data, output_folder, log_folder, mode='ACD'):
    # NOTE: We dont need to use csv module in this method. Because all input files are already guaranteed to be
    # in csv format.
    part_str = 'part_{}'.format(part_data[0])
    logger = logging.getLogger(part_str)
    file_handler = logging.FileHandler('{}/partition_{}_at_{}.log'.format(log_folder,
                                                                          part_str,
                                                                          strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    try:
        if 'a' in mode.lower():
            # replace all content
            all_output_folder = '{}/tokens'.format(output_folder)
            partition_content_file = '{}/20161226-tokens-part{}-{}-{}.csv'.\
                format(all_output_folder, part_data[0], part_data[1][0], part_data[1][1])
            with open(partition_content_file, 'r') as f:
                content = ''
                replaced = False
                for line in f:
                    article_id = int(line.split(',')[0])
                    if article_id in part_data[2]:
                        if not replaced:
                            replaced = True
                            in_content_file = '{}/{}_content.csv'.format(input_folder, article_id)
                            with open(in_content_file, 'r') as f_new:
                                for line_new in f_new:
                                    content += line_new
                                # content += '\n'
                    else:
                        replaced = False
                        content += line

            new_file_all = '{}/new/20161226-tokens-part{}-{}-{}.csv'.\
                format(all_output_folder, part_data[0], part_data[1][0], part_data[1][1])
            with open(new_file_all, 'w') as f:
                f.write(content)
            del content

        if 'c' in mode.lower():
            # replace current content
            current_output_folder = '{}/current_content'.format(output_folder)
            partition_current_file = '{}/20161226-current_content-part{}-{}-{}.csv'.\
                format(current_output_folder, part_data[0], part_data[1][0], part_data[1][1])
            with open(partition_current_file, 'r') as f:
                header = next(f)
                current_content = header
                replaced = False
                for line in f:
                    article_id = int(line.split(',')[0])
                    if article_id in part_data[2]:
                        if not replaced:
                            replaced = True
                            in_current_file = '{}/{}_current_content.csv'.format(input_folder, article_id)
                            with open(in_current_file, 'r') as f_new:
                                for line_new in f_new:
                                    current_content += line_new
                                # current_content += '\n'
                    else:
                        replaced = False
                        current_content += line

            new_file_current = '{}/new/20161226-current_content-part{}-{}-{}.csv'.\
                format(current_output_folder, part_data[0], part_data[1][0], part_data[1][1])
            with open(new_file_current, 'w') as f:
                f.write(current_content)
            del current_content

        if 'd' in mode.lower():
            # replace deleted content
            deleted_output_folder = '{}/deleted_content'.format(output_folder)
            partition_deleted_file = '{}/20161226-deleted_content-part{}-{}-{}.csv'.\
                format(deleted_output_folder, part_data[0], part_data[1][0], part_data[1][1])
            with open(partition_deleted_file, 'r') as f:
                header = next(f)
                deleted_content = header
                replaced = False
                for line in f:
                    article_id = int(line.split(',')[0])
                    if article_id in part_data[2]:
                        if not replaced:
                            replaced = True
                            in_current_file = '{}/{}_deleted_content.csv'.format(input_folder, article_id)
                            with open(in_current_file, 'r') as f_new:
                                for line_new in f_new:
                                    deleted_content += line_new
                                # deleted_content += '\n'
                    else:
                        replaced = False
                        deleted_content += line

            new_file_deleted = '{}/new/20161226-deleted_content-part{}-{}-{}.csv'.\
                format(deleted_output_folder, part_data[0], part_data[1][0], part_data[1][1])
            with open(new_file_deleted, 'w') as f:
                f.write(deleted_content)
            del deleted_content
    except Exception as e:
        logger.exception('{}'.format(part_str))

    return True


def group_articles(input_folder, output_folder):
    # calculate parts dict
    parts = {}  # {partition_file_path: [part_number, (part_from, part_to), article_ids_set], ..}
    output_folder = output_folder + '/' + 'current_content'
    for o in listdir(output_folder):
        if not isfile('{}/{}'.format(output_folder, o)):
            continue
        part_info = o.split('-part')[1].split('.csv')[0]
        part_number, part_from, part_to = map(int, part_info.split('-'))
        parts['{}/{}'.format(output_folder, o)] = [part_number, (part_from, part_to), set()]
    # group input articles into parts dict
    for i in listdir(input_folder):
        article_id = int(i.split('_')[0])
        for part_file, data in parts.items():
            if data[1][0] <= article_id <= data[1][1]:
                data[2].add(article_id)
                break
    # remove parts without article ids - no need to process them
    to_remove = []
    for part_file in parts:
        if not parts[part_file][2]:
            to_remove.append(part_file)
    for part_file in to_remove:
        del parts[part_file]
    return parts


def get_args():
    parser = argparse.ArgumentParser(description='Replace csv of each article in respective partition csv.')
    parser.add_argument('-i', '--input_folder', required=True,
                        help='Where content csv of each article takes place. '
                             'Name of the csv files must be as <article_id>_content.csv , '
                             '<article_id>_current_content.csv and <article_id>_deleted_content.csv.'
                             'Check wikiwho_to_csv.py.', )
    parser.add_argument('-o', '--output_folder', help='Where partition folders take place.', required=True)
    parser.add_argument('-m', '--max_workers', type=int, help='Number of processors/threads to run parallel. '
                                                              'Default is # compressed files in given folder path.',
                        required=True)
    parser.add_argument('-d', '--mode', help='A: Save all content , C: save current content, '
                                             'ACD: Save all, current and deleted contents.',
                        required=True)

    args = parser.parse_args()
    return args


def main():
    args = get_args()
    input_folder = args.input_folder
    input_folder = input_folder[:-1] if input_folder.endswith('/') else input_folder

    output_folder = args.output_folder
    output_folder = output_folder[:-1] if output_folder and output_folder.endswith('/') else output_folder
    if not exists(output_folder):
        mkdir(output_folder)

    # Group input articles per partition
    parts_dict = group_articles(input_folder, output_folder)
    # for p in parts_dict:
    #     print(p, parts_dict[p])
    # sys.exit()

    # Set logging
    log_folder = '{}/{}'.format(output_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)
    logger = logging.getLogger('future_log')
    file_handler = logging.FileHandler('{}/{}_at_{}.log'.format(log_folder,
                                                                'future_in_outs',
                                                                strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]

    # Get max number of concurrent workers
    max_workers = args.max_workers
    print('max_workers:', max_workers, 'parts_dict:', len(parts_dict))

    mode = args.mode.lower()
    for i in mode:
        if i == 'a':
            if not exists('{}/tokens/new'.format(output_folder)):
                mkdir('{}/tokens/new'.format(output_folder))
        elif i == 'c':
            if not exists('{}/current_content/new'.format(output_folder)):
                mkdir('{}/current_content/new'.format(output_folder))
        elif i == 'd':
            if not exists('{}/deleted_content/new'.format(output_folder)):
                mkdir('{}/deleted_content/new'.format(output_folder))

    print('Start: Replace content in partition at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        files_all = len(parts_dict)
        files_left = files_all
        files_iter = iter(parts_dict.keys())

        while files_left:
            for part_file in files_iter:
                job = executor.submit(replace_content_in_partition, input_folder, parts_dict[part_file],
                                      output_folder, log_folder, mode)
                jobs[job] = 'part_{}'.format(parts_dict[part_file][0])
                if len(jobs) == max_workers:  # limit # jobs with max_workers
                    break

            for job in as_completed(jobs):
                files_left -= 1
                part_ = jobs[job]
                try:
                    data = job.result()
                except Exception as exc:
                    logger.exception(part_)

                del jobs[job]
                sys.stdout.write('\r{}-{:.3f}%'.format(files_left, ((files_all - files_left) * 100) / files_all))
                break  # to add a new job, if there is any
    print('Done: Replace content in partition at {}'.format(strftime("%H:%M:%S %d-%m-%Y")))

if __name__ == '__main__':
    main()
