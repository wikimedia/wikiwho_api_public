"""
python wikiwho/tools_dataset/partitioning/delete_from_all_content.py -ic '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/partitions/current_tokens' -ia '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/partitions/tokens' -o '/home/kenan/PycharmProjects/wikiwho_api/wikiwho/tests/test_jsons/stats/partitions/o' -m 2
"""
import csv
import sys
import argparse
from os import listdir, mkdir
from os.path import isfile, exists
from time import strftime
from concurrent.futures import ProcessPoolExecutor, as_completed
import logging


def delete_from(all, current, output_file):
    # TODO we dont need to use csv module here. use simply open as f and for line in f:... check NOTE in
    # replace_content_in_partition
    # article_id, revision_id, token_id, str, origin, inbound, outbound
    # header = 'page_id,last_rev_id,token_id,str,origin_rev_id,in,out'.split(',')
    with open(current, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        current_content = {}
        next(reader, None)  # skip the header
        for row in reader:
            # if 'page_id' == row[0]:
            #     continue
            current_content['{}-{}'.format(row[0], row[2])] = True  # article id, token id
    # print('len(current_content): ', len(current_content))

    # page_id,last_rev_id,token_id,str,origin_rev_id,in,out
    header = 'page_id,last_rev_id,token_id,str,origin_rev_id,in,out'.split(',')
    counter = 0
    with open(all, newline='') as f:
        reader = csv.reader(f, delimiter=',')
        deleted_content = []
        # next(reader, None)  # skip the header
        for row in reader:
            # if 'page_id' == row[0]:
            #     continue
            counter += 1
            if not '{}-{}'.format(row[0], row[2]) in current_content:  # article id, token id
                # page_id,last_rev_id,token_id,str,origin_rev_id, in,out
                deleted_content.append(row)
    del current_content
    # print('len(all_content)', counter)
    # print(output_file)
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(deleted_content)
    # print('len(deleted_content)', len(deleted_content))
    return True


def get_args():
    parser = argparse.ArgumentParser(description='Subtract current token csv from all token csv and '
                                                 'output deleted token csvs.')
    parser.add_argument('-ic', '--input_current', required=True, help='Current token csvs folder')
    parser.add_argument('-ia', '--input_all', required=True, help='All token csvs folder')
    parser.add_argument('-o', '--output', required=True, help='Output folder')
    parser.add_argument('-m', '--max_workers', type=int, help='Default is 10')

    args = parser.parse_args()
    return args


def main():
    args = get_args()
    output_folder = args.output
    if not exists(output_folder):
        mkdir(output_folder)
    max_workers = args.max_workers or 10

    # get input files, order and merge them
    input_current_folder = args.input_current
    input_current_dict = {}
    for input_file_name in listdir(input_current_folder):
        input_file = '{}/{}'.format(input_current_folder, input_file_name)
        # ex input_file_name: currentcontent-20161226-part1-12-5617.csv
        part_id = input_file_name.split('-')[2][4:]
        first_article_id = input_file_name.split('-')[3]
        last_article_id = input_file_name.split('-')[4][:-4]
        input_current_dict[part_id] = [input_file, first_article_id, last_article_id]
    input_all_folder = args.input_all
    input_all_dict = {}
    for input_file_name in listdir(input_all_folder):
        input_file = '{}/{}'.format(input_all_folder, input_file_name)
        # ex input_file_name: mac-tokens-all-part1-12-1728.csv
        part_id = input_file_name.split('-')[3][4:]
        first_article_id = input_file_name.split('-')[4]
        last_article_id = input_file_name.split('-')[5][:-4]
        input_all_dict[part_id] = [input_file, first_article_id, last_article_id]
    assert len(input_current_dict) == len(input_all_dict)
    input_files = []
    for k in sorted(input_current_dict, key=int):
        # print(input_current_dict[k])
        # print(input_all_dict[k])
        assert input_current_dict[k][1] == input_all_dict[k][1]
        assert input_current_dict[k][2] == input_all_dict[k][2]
        input_files.append([input_current_dict[k][0], input_all_dict[k][0],
                            input_current_dict[k][1], input_current_dict[k][2], k])

    # set logging
    log_folder = '{}/{}'.format(output_folder, 'logs')
    if not exists(log_folder):
        mkdir(log_folder)
    logger = logging.getLogger('future_log')
    file_handler = logging.FileHandler('{}/deleted_content_future_at_{}.log'.format(log_folder,
                                                                                    strftime("%Y-%m-%d-%H:%M:%S")))
    file_handler.setLevel(logging.ERROR)
    format_ = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s'
    formatter = logging.Formatter(format_)
    file_handler.setFormatter(formatter)
    logger.handlers = [file_handler]

    # start concurrent processes
    print(max_workers)
    print("Start: ", strftime("%Y-%m-%d-%H:%M:%S"))
    csv.field_size_limit(sys.maxsize)
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        jobs = {}
        files_left = len(input_files)
        files_all = len(input_files)
        files_iter = iter(input_files)
        while files_left:
            for input_current, input_all, first_article_id, last_article_id, part_id in files_iter:
                output_file = '{}/20161226-deleted_content-part{}-{}-{}.csv'.format(output_folder, part_id,
                                                                                    first_article_id, last_article_id)
                if exists(output_file):
                    files_left -= 1
                    continue
                job = executor.submit(delete_from, input_all, input_current, output_file)
                jobs[job] = '{}-{}'.format(first_article_id, last_article_id)
                if len(jobs) == max_workers:  # limit # jobs with max_workers
                    break

            for job in as_completed(jobs):
                files_left -= 1
                range_ = jobs[job]
                try:
                    data = job.result()
                except Exception as exc:
                    logger.exception(range_)

                del jobs[job]
                sys.stdout.write('\r{}-{:.3f}%'.format(files_left, ((files_all - files_left) * 100) / files_all))
                break  # to add a new job, if there is any
    print("Done: ", strftime("%Y-%m-%d-%H:%M:%S"))

if __name__ == '__main__':
    main()
